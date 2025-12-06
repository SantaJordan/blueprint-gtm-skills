#!/usr/bin/env python3
"""
GPT-4 Batch QA Script for SMB Contact Results

Loads pipeline results and sends batches to GPT-4 for quality scoring.
Each result is evaluated for:
1. Name plausibility
2. Title appropriateness
3. Email validity
4. Overall confidence

Usage:
    OPENAI_API_KEY="..." python -m evaluation.scripts.run_batch_qa \
        --input evaluation/results/yelp_940_results.json \
        --output evaluation/results/yelp_940_qa_scores.json \
        --batch-size 50
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from openai import AsyncOpenAI

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class QAScore:
    """Quality score for a single result"""
    company_name: str
    vertical: str
    contact_name: str | None
    contact_title: str | None
    contact_email: str | None
    domain: str

    # Scores
    name_plausible: str  # yes/no/unclear
    title_appropriate: str  # yes/no/unclear/na
    email_valid: str  # yes/no/na
    overall_score: int  # 0-100

    # Reasoning
    reasoning: str
    red_flags: list[str]


SYSTEM_PROMPT = """You are an expert at evaluating SMB contact discovery results.
You'll receive batches of contact discovery results and need to evaluate each one.

For each result, determine:

1. **Name Plausibility** (yes/no/unclear):
   - "yes" if the name looks like a real person's name (e.g., "John Smith", "Maria Garcia")
   - "no" if it's clearly garbage (e.g., "Menu", "Contact Us", "Report Project", "Click Here")
   - "unclear" if ambiguous (e.g., single name, unusual format)

2. **Title Appropriateness** (yes/no/unclear/na):
   - "yes" if title suggests ownership/leadership (Owner, CEO, Founder, President, Manager, Director)
   - "no" if title is clearly wrong (e.g., "Passes Away", "Menu Item", random words)
   - "unclear" if can't determine
   - "na" if no title provided

3. **Email Validity** (yes/no/na):
   - "yes" if email format is valid AND domain matches company domain
   - "no" if email is malformed or domain doesn't match
   - "na" if no email provided

4. **Overall Score** (0-100):
   - 90-100: High confidence correct contact
   - 70-89: Likely correct but some uncertainty
   - 50-69: Possible but suspicious
   - 30-49: Unlikely to be correct
   - 0-29: Almost certainly wrong/garbage

5. **Red Flags**: List any issues found (garbage text, parsing errors, wrong person type, etc.)

Return a JSON array with one object per input result."""

USER_PROMPT_TEMPLATE = """Evaluate these {count} SMB contact discovery results:

{results_json}

Return a JSON array with exactly {count} objects, one per result, in the same order.
Each object should have these fields:
- company_name: string (from input)
- name_plausible: "yes" | "no" | "unclear"
- title_appropriate: "yes" | "no" | "unclear" | "na"
- email_valid: "yes" | "no" | "na"
- overall_score: number (0-100)
- reasoning: string (brief explanation)
- red_flags: array of strings

IMPORTANT: Return ONLY the JSON array, no other text."""


async def evaluate_batch(
    client: AsyncOpenAI,
    results: list[dict],
    model: str = "gpt-4o-mini"
) -> list[dict]:
    """Evaluate a batch of results with GPT-4"""

    # Prepare simplified results for context
    simplified = []
    for r in results:
        simplified.append({
            "company_name": r.get("company_name", "Unknown"),
            "domain": r.get("domain", ""),
            "vertical": r.get("vertical", ""),
            "contact_name": r.get("contact_name") or r.get("owner_name"),
            "contact_title": r.get("contact_title") or r.get("owner_title"),
            "contact_email": r.get("contact_email"),
            "sources": r.get("contact_sources", []),
            "confidence": r.get("contact_confidence", 0),
        })

    user_prompt = USER_PROMPT_TEMPLATE.format(
        count=len(simplified),
        results_json=json.dumps(simplified, indent=2)
    )

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=4000,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content

        # Parse response
        parsed = json.loads(content)

        # Handle both array and object with "results" key
        if isinstance(parsed, list):
            return parsed
        elif isinstance(parsed, dict) and "results" in parsed:
            return parsed["results"]
        elif isinstance(parsed, dict) and len(parsed) == len(simplified):
            # Sometimes returns object with indices as keys
            return [parsed[str(i)] for i in range(len(simplified))]
        else:
            logger.warning(f"Unexpected response format: {type(parsed)}")
            return []

    except Exception as e:
        logger.error(f"Error evaluating batch: {e}")
        return []


async def run_qa(
    input_file: str,
    output_file: str,
    batch_size: int,
    model: str
):
    """Run GPT-4 QA on pipeline results"""

    # Load results
    logger.info(f"Loading results from: {input_file}")
    with open(input_file, 'r') as f:
        data = json.load(f)

    # Handle both formats: direct array or nested under 'results'
    if isinstance(data, dict):
        results = data.get("results", [])
        metadata = {k: v for k, v in data.items() if k != "results"}
    else:
        results = data
        metadata = {}

    logger.info(f"Loaded {len(results)} results")

    # Handle V2 format: flatten contacts from nested array to top-level
    def get_best_contact(r: dict) -> dict | None:
        """Get best valid contact from a result (V2 format)"""
        contacts = r.get("contacts", [])
        if not contacts:
            # Fall back to V1 format
            if r.get("contact_name") or r.get("owner_name"):
                return r
            return None
        # Find best valid contact
        valid = [c for c in contacts if c.get("is_valid")]
        if valid:
            return max(valid, key=lambda c: c.get("confidence", 0))
        # Return highest confidence even if not valid
        return max(contacts, key=lambda c: c.get("confidence", 0))

    # Flatten V2 results to have best contact at top level
    flattened_results = []
    for r in results:
        contact = get_best_contact(r)
        if contact:
            flat = {
                "company_name": r.get("company_name"),
                "domain": r.get("domain"),
                "vertical": r.get("vertical"),
                "contact_name": contact.get("name"),
                "contact_title": contact.get("title"),
                "contact_email": contact.get("email"),
                "contact_sources": contact.get("sources", []),
                "contact_confidence": contact.get("confidence", 0),
            }
            flattened_results.append(flat)

    # Filter to only results with contacts
    results_with_contacts = [
        r for r in flattened_results
        if r.get("contact_name")
    ]
    results_without_contacts = len(results) - len(results_with_contacts)

    logger.info(f"Results with contacts: {len(results_with_contacts)}")
    logger.info(f"Results without contacts: {results_without_contacts}")

    if not results_with_contacts:
        logger.warning("No results with contacts to evaluate!")
        return

    # Initialize OpenAI client
    client = AsyncOpenAI()

    # Process in batches
    all_scores = []
    total_batches = (len(results_with_contacts) + batch_size - 1) // batch_size

    for i in range(0, len(results_with_contacts), batch_size):
        batch = results_with_contacts[i:i+batch_size]
        batch_num = i // batch_size + 1

        logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} results)")

        scores = await evaluate_batch(client, batch, model)

        if scores:
            all_scores.extend(scores)
            logger.info(f"  Got {len(scores)} scores")
        else:
            logger.warning(f"  No scores returned for batch {batch_num}")

        # Small delay between batches
        if batch_num < total_batches:
            await asyncio.sleep(0.5)

    # Aggregate metrics
    metrics = aggregate_scores(all_scores, results_with_contacts)

    # Save results
    output_data = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "input_file": input_file,
            "total_results": len(results),
            "results_with_contacts": len(results_with_contacts),
            "results_without_contacts": results_without_contacts,
            "model": model,
            "batch_size": batch_size,
        },
        "metrics": metrics,
        "scores": all_scores,
    }

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    logger.info(f"\nSaved QA scores to: {output_path}")

    # Print summary
    print("\n" + "=" * 60)
    print("QA SUMMARY")
    print("=" * 60)
    print(f"Total results evaluated: {len(all_scores)}")
    print(f"\nName Plausibility:")
    print(f"  Yes: {metrics['name_plausible_yes']} ({metrics['name_plausible_yes_pct']:.1f}%)")
    print(f"  No: {metrics['name_plausible_no']} ({metrics['name_plausible_no_pct']:.1f}%)")
    print(f"  Unclear: {metrics['name_plausible_unclear']} ({metrics['name_plausible_unclear_pct']:.1f}%)")
    print(f"\nTitle Appropriateness:")
    print(f"  Yes: {metrics['title_appropriate_yes']} ({metrics['title_appropriate_yes_pct']:.1f}%)")
    print(f"  No: {metrics['title_appropriate_no']} ({metrics['title_appropriate_no_pct']:.1f}%)")
    print(f"\nEmail Validity:")
    print(f"  Yes: {metrics['email_valid_yes']} ({metrics['email_valid_yes_pct']:.1f}%)")
    print(f"  No: {metrics['email_valid_no']} ({metrics['email_valid_no_pct']:.1f}%)")
    print(f"  N/A: {metrics['email_valid_na']} ({metrics['email_valid_na_pct']:.1f}%)")
    print(f"\nOverall Scores:")
    print(f"  Average: {metrics['avg_score']:.1f}")
    print(f"  High (90+): {metrics['score_high']} ({metrics['score_high_pct']:.1f}%)")
    print(f"  Medium (70-89): {metrics['score_medium']} ({metrics['score_medium_pct']:.1f}%)")
    print(f"  Low (50-69): {metrics['score_low']} ({metrics['score_low_pct']:.1f}%)")
    print(f"  Garbage (<50): {metrics['score_garbage']} ({metrics['score_garbage_pct']:.1f}%)")
    print("=" * 60)


def aggregate_scores(scores: list[dict], original_results: list[dict]) -> dict:
    """Aggregate QA scores into metrics"""
    if not scores:
        return {}

    total = len(scores)

    # Count each category
    name_yes = sum(1 for s in scores if s.get("name_plausible") == "yes")
    name_no = sum(1 for s in scores if s.get("name_plausible") == "no")
    name_unclear = total - name_yes - name_no

    title_yes = sum(1 for s in scores if s.get("title_appropriate") == "yes")
    title_no = sum(1 for s in scores if s.get("title_appropriate") == "no")
    title_unclear = sum(1 for s in scores if s.get("title_appropriate") == "unclear")
    title_na = total - title_yes - title_no - title_unclear

    email_yes = sum(1 for s in scores if s.get("email_valid") == "yes")
    email_no = sum(1 for s in scores if s.get("email_valid") == "no")
    email_na = total - email_yes - email_no

    # Overall scores
    overall_scores = [s.get("overall_score", 0) for s in scores]
    avg_score = sum(overall_scores) / len(overall_scores) if overall_scores else 0

    score_high = sum(1 for s in overall_scores if s >= 90)
    score_medium = sum(1 for s in overall_scores if 70 <= s < 90)
    score_low = sum(1 for s in overall_scores if 50 <= s < 70)
    score_garbage = sum(1 for s in overall_scores if s < 50)

    # Collect red flags
    all_flags = []
    for s in scores:
        all_flags.extend(s.get("red_flags", []))

    from collections import Counter
    flag_counts = Counter(all_flags)

    return {
        "total_evaluated": total,
        "name_plausible_yes": name_yes,
        "name_plausible_yes_pct": 100 * name_yes / total,
        "name_plausible_no": name_no,
        "name_plausible_no_pct": 100 * name_no / total,
        "name_plausible_unclear": name_unclear,
        "name_plausible_unclear_pct": 100 * name_unclear / total,

        "title_appropriate_yes": title_yes,
        "title_appropriate_yes_pct": 100 * title_yes / total,
        "title_appropriate_no": title_no,
        "title_appropriate_no_pct": 100 * title_no / total,
        "title_appropriate_unclear": title_unclear,
        "title_appropriate_unclear_pct": 100 * title_unclear / total,
        "title_appropriate_na": title_na,
        "title_appropriate_na_pct": 100 * title_na / total,

        "email_valid_yes": email_yes,
        "email_valid_yes_pct": 100 * email_yes / total,
        "email_valid_no": email_no,
        "email_valid_no_pct": 100 * email_no / total,
        "email_valid_na": email_na,
        "email_valid_na_pct": 100 * email_na / total,

        "avg_score": avg_score,
        "score_high": score_high,
        "score_high_pct": 100 * score_high / total,
        "score_medium": score_medium,
        "score_medium_pct": 100 * score_medium / total,
        "score_low": score_low,
        "score_low_pct": 100 * score_low / total,
        "score_garbage": score_garbage,
        "score_garbage_pct": 100 * score_garbage / total,

        "top_red_flags": flag_counts.most_common(10),
    }


def main():
    parser = argparse.ArgumentParser(description="GPT-4 batch QA for SMB results")
    parser.add_argument(
        "--input",
        required=True,
        help="Path to pipeline results JSON"
    )
    parser.add_argument(
        "--output",
        default="evaluation/results/qa_scores.json",
        help="Output file for QA scores"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Number of results per GPT-4 batch"
    )
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="OpenAI model to use"
    )

    args = parser.parse_args()

    if not os.environ.get("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not set")
        sys.exit(1)

    asyncio.run(run_qa(
        input_file=args.input,
        output_file=args.output,
        batch_size=args.batch_size,
        model=args.model
    ))


if __name__ == "__main__":
    main()
