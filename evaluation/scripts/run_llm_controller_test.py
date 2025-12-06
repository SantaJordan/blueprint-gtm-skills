#!/usr/bin/env python
"""
Test script for LLMController (Phase 2)

Tests the agent loop with early exit optimization.
Compares cost and quality vs the fixed-stage pipeline (Phase 1).
"""

import asyncio
import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

# Add project root and contact-finder to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "contact-finder"))

from modules.pipeline.llm_controller import LLMController
from modules.pipeline.tool_wrappers import create_tool_factory
from modules.llm.openai_provider import OpenAIProvider

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def process_company(controller: LLMController, company: dict) -> dict:
    """Process a single company through the LLM controller"""
    start_time = time.time()

    result = await controller.process_company(
        company_name=company.get("name") or company.get("company_name"),
        domain=company.get("domain") or company.get("website"),
        city=company.get("city"),
        state_code=company.get("state"),
        vertical=company.get("vertical") or company.get("category")
    )

    result["processing_time_ms"] = (time.time() - start_time) * 1000
    result["input"] = company

    return result


async def run_batch(
    companies: list[dict],
    controller: LLMController,
    concurrency: int = 5
) -> list[dict]:
    """Run a batch of companies through the controller"""
    results = []
    semaphore = asyncio.Semaphore(concurrency)

    async def process_with_semaphore(company: dict, idx: int) -> dict:
        async with semaphore:
            logger.info(f"[{idx+1}/{len(companies)}] Processing: {company.get('name') or company.get('company_name')}")
            result = await process_company(controller, company)
            return result

    tasks = [
        process_with_semaphore(company, i)
        for i, company in enumerate(companies)
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Handle exceptions
    processed = []
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            logger.error(f"Error processing company {i}: {r}")
            processed.append({
                "error": str(r),
                "input": companies[i]
            })
        else:
            processed.append(r)

    return processed


def analyze_results(results: list[dict]) -> dict:
    """Analyze results and compute metrics"""
    total = len(results)
    with_contact = [r for r in results if r.get("contact")]
    early_exits = [r for r in results if r.get("llm_stages", 5) < 3]  # Less than 3 stages = early exit

    total_cost = sum(r.get("total_cost", 0) for r in results)
    avg_stages = sum(r.get("llm_stages", 0) for r in results) / max(1, total)
    avg_time = sum(r.get("processing_time_ms", 0) for r in results) / max(1, total)

    # Confidence distribution
    confidences = [r["contact"]["confidence"] for r in with_contact if r.get("contact", {}).get("confidence")]

    return {
        "total_companies": total,
        "with_contact": len(with_contact),
        "contact_rate": len(with_contact) / max(1, total) * 100,
        "early_exits": len(early_exits),
        "early_exit_rate": len(early_exits) / max(1, total) * 100,
        "total_cost": total_cost,
        "avg_cost_per_company": total_cost / max(1, total),
        "avg_stages": avg_stages,
        "avg_time_ms": avg_time,
        "avg_confidence": sum(confidences) / max(1, len(confidences)) if confidences else 0,
        "confidence_distribution": {
            "high_80+": len([c for c in confidences if c >= 80]),
            "medium_50-79": len([c for c in confidences if 50 <= c < 80]),
            "low_below_50": len([c for c in confidences if c < 50]),
        }
    }


async def main():
    parser = argparse.ArgumentParser(description="Test LLMController (Phase 2)")
    parser.add_argument("--input", required=True, help="Input JSON file with companies")
    parser.add_argument("--output", required=True, help="Output JSON file for results")
    parser.add_argument("--limit", type=int, default=20, help="Number of companies to test")
    parser.add_argument("--concurrency", type=int, default=5, help="Concurrent requests")
    parser.add_argument("--max-stages", type=int, default=5, help="Max stages per company")
    parser.add_argument("--cost-budget", type=float, default=0.015, help="Max cost per company")
    args = parser.parse_args()

    # Check API keys
    required_keys = ["OPENWEB_NINJA_API_KEY", "SERPER_API_KEY", "OPENAI_API_KEY"]
    missing = [k for k in required_keys if not os.environ.get(k)]
    if missing:
        logger.error(f"Missing required environment variables: {missing}")
        sys.exit(1)

    # Load companies
    with open(args.input, "r") as f:
        data = json.load(f)

    companies = data if isinstance(data, list) else data.get("companies", data.get("results", []))
    companies = companies[:args.limit]
    logger.info(f"Loaded {len(companies)} companies (limit: {args.limit})")

    # Initialize components
    llm_provider = OpenAIProvider()
    tool_factory = create_tool_factory()
    tools = tool_factory.get_tools()

    controller = LLMController(
        llm_provider=llm_provider,
        tools=tools,
        max_stages=args.max_stages,
        cost_budget=args.cost_budget
    )

    # Run batch
    logger.info(f"Starting batch with concurrency={args.concurrency}")
    start_time = time.time()

    results = await run_batch(companies, controller, args.concurrency)

    total_time = time.time() - start_time
    logger.info(f"Batch completed in {total_time:.1f}s")

    # Analyze results
    metrics = analyze_results(results)
    controller_stats = controller.get_stats()

    # Print summary
    print("\n" + "="*60)
    print("LLMController Test Results (Phase 2)")
    print("="*60)
    print(f"Companies processed: {metrics['total_companies']}")
    print(f"With valid contact: {metrics['with_contact']} ({metrics['contact_rate']:.1f}%)")
    print(f"Early exits: {metrics['early_exits']} ({metrics['early_exit_rate']:.1f}%)")
    print(f"\nCost Analysis:")
    print(f"  Total cost: ${metrics['total_cost']:.4f}")
    print(f"  Avg cost/company: ${metrics['avg_cost_per_company']:.4f}")
    print(f"  Avg stages: {metrics['avg_stages']:.2f}")
    print(f"\nController Stats:")
    print(f"  LLM calls: {controller_stats['total_llm_calls']}")
    print(f"  Tool calls: {controller_stats['total_tool_calls']}")
    print(f"  Early exits: {controller_stats['early_exits']}")
    print(f"\nQuality:")
    print(f"  Avg confidence: {metrics['avg_confidence']:.1f}")
    print(f"  High (80+): {metrics['confidence_distribution']['high_80+']}")
    print(f"  Medium (50-79): {metrics['confidence_distribution']['medium_50-79']}")
    print(f"  Low (<50): {metrics['confidence_distribution']['low_below_50']}")
    print(f"\nPerformance:")
    print(f"  Total time: {total_time:.1f}s")
    print(f"  Avg time/company: {metrics['avg_time_ms']:.0f}ms")
    print("="*60)

    # Save results
    output_data = {
        "metrics": metrics,
        "controller_stats": controller_stats,
        "results": results,
        "config": {
            "input": args.input,
            "limit": args.limit,
            "concurrency": args.concurrency,
            "max_stages": args.max_stages,
            "cost_budget": args.cost_budget
        }
    }

    with open(args.output, "w") as f:
        json.dump(output_data, f, indent=2, default=str)

    logger.info(f"Results saved to {args.output}")

    # Cleanup
    await tool_factory.close()

    # Print example results
    print("\nExample Results:")
    for r in results[:5]:
        name = r.get("company_name", "Unknown")
        contact = r.get("contact")
        if contact:
            print(f"  {name}: {contact.get('name')} ({contact.get('confidence', 0):.0f}%) - stages: {r.get('llm_stages', 0)}")
        else:
            print(f"  {name}: No contact - {r.get('no_contact_reason', 'unknown')}")


if __name__ == "__main__":
    asyncio.run(main())
