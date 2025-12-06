#!/usr/bin/env python3
"""
Test the Adaptive Controller on the adversarial sample.

This script runs the adaptive pipeline that classifies each business
and selects the appropriate strategy (SMB, Franchise, Healthcare, Corporate).

Usage:
    OPENWEB_NINJA_API_KEY="..." \
    SERPER_API_KEY="..." \
    OPENAI_API_KEY="..." \
    python -u -m evaluation.scripts.run_adaptive_test \
      --input evaluation/data/smb_random_200.json \
      --output evaluation/results/adaptive_test_200.json \
      --limit 50 \
      --concurrency 5
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from collections import Counter
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "contact-finder"))

from modules.pipeline.adaptive_controller import AdaptiveController, classify_business_type, BusinessType
from modules.pipeline.tool_wrappers import create_tool_factory
from modules.llm.openai_provider import OpenAIProvider

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def process_batch(
    controller: AdaptiveController,
    companies: list[dict],
    semaphore: asyncio.Semaphore,
    delay: float = 0.5
) -> list[dict]:
    """Process a batch of companies with concurrency control"""

    async def process_one(company: dict) -> dict:
        async with semaphore:
            try:
                result = await controller.process_company(
                    company_name=company.get("company_name", company.get("name", "")),
                    domain=company.get("domain"),
                    city=company.get("city"),
                    state_code=company.get("state"),
                    category=company.get("category", company.get("vertical"))
                )
                await asyncio.sleep(delay)
                return result
            except Exception as e:
                logger.error(f"Error processing {company.get('company_name')}: {e}")
                return {
                    "company_name": company.get("company_name", ""),
                    "error": str(e),
                    "contact": None
                }

    tasks = [process_one(c) for c in companies]
    return await asyncio.gather(*tasks)


def print_stats(results: list[dict], controller: AdaptiveController):
    """Print summary statistics"""
    total = len(results)
    with_contact = sum(1 for r in results if r.get("contact"))
    total_cost = sum(r.get("total_cost", 0) for r in results)

    # Count by business type
    type_counts = Counter()
    type_success = Counter()
    for r in results:
        biz_type = r.get("business_type", "unknown")
        type_counts[biz_type] += 1
        if r.get("contact"):
            type_success[biz_type] += 1

    # Confidence distribution
    confidences = [r["contact"]["confidence"] for r in results if r.get("contact") and r["contact"].get("confidence")]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0

    high_conf = sum(1 for c in confidences if c >= 80)
    med_conf = sum(1 for c in confidences if 50 <= c < 80)
    low_conf = sum(1 for c in confidences if c < 50)

    print("\n" + "=" * 60)
    print("Adaptive Controller Test Results")
    print("=" * 60)
    print(f"\nOverall:")
    print(f"  Total:          {total}")
    print(f"  With Contact:   {with_contact} ({with_contact/total*100:.1f}%)")
    print(f"  Avg Confidence: {avg_confidence:.1f}%")
    print(f"  Total Cost:     ${total_cost:.4f}")
    print(f"  Cost/Company:   ${total_cost/total:.4f}")

    print(f"\nBy Business Type:")
    for biz_type in ["smb", "franchise", "healthcare", "corporate"]:
        count = type_counts.get(biz_type, 0)
        success = type_success.get(biz_type, 0)
        if count > 0:
            pct = success / count * 100
            print(f"  {biz_type:12}: {success:3}/{count:3} ({pct:5.1f}%)")

    print(f"\nConfidence Breakdown:")
    print(f"  High (80+):   {high_conf}")
    print(f"  Medium (50-79): {med_conf}")
    print(f"  Low (<50):    {low_conf}")

    # Strategy pivots
    pivots = sum(1 for r in results if r.get("strategy_pivoted"))
    print(f"\nStrategy Pivots: {pivots}")

    # Controller stats
    stats = controller.get_stats()
    print(f"\nController Stats:")
    print(f"  Early Exits: {stats['early_exits']}")
    print(f"  Total Pivots: {stats['pivots']}")


async def main():
    parser = argparse.ArgumentParser(description="Test Adaptive Controller")
    parser.add_argument("--input", required=True, help="Input JSON file")
    parser.add_argument("--output", required=True, help="Output JSON file")
    parser.add_argument("--limit", type=int, default=50, help="Max companies to process")
    parser.add_argument("--concurrency", type=int, default=5, help="Concurrent requests")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between requests")
    args = parser.parse_args()

    # Check API keys
    openweb_key = os.environ.get("OPENWEB_NINJA_API_KEY")
    serper_key = os.environ.get("SERPER_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")

    if not openweb_key:
        print("Error: OPENWEB_NINJA_API_KEY not set")
        sys.exit(1)
    if not serper_key:
        print("Error: SERPER_API_KEY not set")
        sys.exit(1)
    if not openai_key:
        print("Error: OPENAI_API_KEY not set")
        sys.exit(1)

    # Load input data
    with open(args.input) as f:
        data = json.load(f)

    companies = data[:args.limit]
    print(f"Processing {len(companies)} companies with adaptive controller...")

    # Show classification breakdown
    print("\nBusiness Type Classification:")
    type_counts = Counter()
    for c in companies:
        name = c.get("company_name", c.get("name", ""))
        category = c.get("category", c.get("vertical", ""))
        biz_type = classify_business_type(name, category)
        type_counts[biz_type] += 1

    for biz_type in BusinessType:
        count = type_counts[biz_type]
        if count > 0:
            print(f"  {biz_type.value:12}: {count} ({count/len(companies)*100:.1f}%)")

    # Initialize components
    tool_factory = create_tool_factory(
        openweb_api_key=openweb_key,
        serper_api_key=serper_key
    )

    llm_provider = OpenAIProvider(api_key=openai_key)

    controller = AdaptiveController(
        llm_provider=llm_provider,
        tools=tool_factory.get_tools(),
        cost_budget=0.02
    )

    semaphore = asyncio.Semaphore(args.concurrency)

    # Process companies
    start_time = time.time()
    results = await process_batch(controller, companies, semaphore, args.delay)
    elapsed = time.time() - start_time

    # Print stats
    print_stats(results, controller)
    print(f"\nTime: {elapsed:.1f}s ({elapsed/len(companies):.1f}s/company)")

    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump({
            "config": {
                "input": args.input,
                "limit": args.limit,
                "concurrency": args.concurrency,
            },
            "summary": {
                "total": len(results),
                "with_contact": sum(1 for r in results if r.get("contact")),
                "total_cost": sum(r.get("total_cost", 0) for r in results),
                "elapsed_seconds": elapsed,
            },
            "results": results
        }, f, indent=2, default=str)

    print(f"\nResults saved to: {output_path}")

    # Cleanup
    await tool_factory.close()


if __name__ == "__main__":
    asyncio.run(main())
