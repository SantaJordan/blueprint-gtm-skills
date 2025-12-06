#!/usr/bin/env python3
"""
Generate Human Spot-Check Sample

Creates a stratified sample of results for manual verification:
- 10 high-confidence successes
- 10 low-confidence/borderline results
- 10 failures/no contact

Outputs a markdown table with all info needed for manual verification.

Usage:
    python -m evaluation.scripts.generate_spotcheck \
        --input evaluation/results/yelp_940_results.json \
        --output evaluation/results/yelp_940_spotcheck.md \
        --sample 30
"""

import argparse
import json
import random
import sys
from datetime import datetime
from pathlib import Path


def load_results(input_file: str) -> list[dict]:
    """Load pipeline results"""
    with open(input_file, 'r') as f:
        data = json.load(f)

    # Handle both formats
    if isinstance(data, dict):
        return data.get("results", [])
    return data


def get_best_contact(r: dict) -> dict | None:
    """Get best valid contact from a result (V2 format)"""
    contacts = r.get("contacts", [])
    if not contacts:
        # Fall back to V1 format
        if r.get("contact_name") or r.get("owner_name"):
            return {
                "name": r.get("contact_name") or r.get("owner_name"),
                "title": r.get("contact_title") or r.get("owner_title"),
                "email": r.get("contact_email"),
                "confidence": r.get("contact_confidence", 0) or r.get("confidence", 0),
                "sources": r.get("contact_sources", []),
            }
        return None
    # Find best valid contact
    valid = [c for c in contacts if c.get("is_valid")]
    if valid:
        return max(valid, key=lambda c: c.get("confidence", 0))
    # Return highest confidence even if not valid
    return max(contacts, key=lambda c: c.get("confidence", 0))


def flatten_result(r: dict) -> dict:
    """Flatten V2 result to have best contact at top level"""
    contact = get_best_contact(r)
    flat = {
        "company_name": r.get("company_name"),
        "domain": r.get("domain"),
        "vertical": r.get("vertical"),
        "phone": r.get("phone", ""),
    }
    if contact:
        flat["owner_name"] = contact.get("name")
        flat["owner_title"] = contact.get("title")
        flat["contact_email"] = contact.get("email")
        flat["contact_confidence"] = contact.get("confidence", 0)
        flat["contact_sources"] = contact.get("sources", [])
    return flat


def stratify_results(results: list[dict]) -> dict[str, list[dict]]:
    """Stratify results into categories"""
    high_confidence = []
    low_confidence = []
    failures = []

    for r in results:
        # Flatten V2 format
        flat = flatten_result(r)

        # Check if has contact
        has_contact = flat.get("owner_name")
        confidence = flat.get("contact_confidence", 0)

        if not has_contact:
            failures.append(flat)
        elif confidence >= 70:
            high_confidence.append(flat)
        else:
            low_confidence.append(flat)

    return {
        "high_confidence": high_confidence,
        "low_confidence": low_confidence,
        "failures": failures,
    }


def sample_category(items: list[dict], n: int, seed: int) -> list[dict]:
    """Sample n items from a category"""
    random.seed(seed)
    if len(items) <= n:
        return items
    return random.sample(items, n)


def generate_markdown(
    samples: dict[str, list[dict]],
    input_file: str
) -> str:
    """Generate markdown report for manual verification"""

    lines = [
        "# Human Verification Spot-Check",
        "",
        f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Source**: `{input_file}`",
        "",
        "## Instructions",
        "",
        "For each company:",
        "1. Visit the company website (domain column)",
        "2. Look for About/Team/Contact page",
        "3. Cross-reference with LinkedIn or Google search",
        "4. Mark the verification status",
        "",
        "---",
        "",
    ]

    # High confidence section
    lines.extend([
        "## High Confidence Results (Expected: Correct)",
        "",
        "These should mostly be correct. If many fail, pipeline has issues.",
        "",
    ])
    lines.append(format_table(samples["high_confidence"], "high"))

    # Low confidence section
    lines.extend([
        "",
        "## Low Confidence Results (Borderline)",
        "",
        "These are uncertain. Check if pipeline correctly flagged them.",
        "",
    ])
    lines.append(format_table(samples["low_confidence"], "low"))

    # Failures section
    lines.extend([
        "",
        "## Failures (No Contact Found)",
        "",
        "Verify if there IS a findable owner that pipeline missed.",
        "",
    ])
    lines.append(format_table(samples["failures"], "failure"))

    # Summary template
    lines.extend([
        "",
        "---",
        "",
        "## Verification Summary",
        "",
        "| Category | Verified Correct | Verified Incorrect | Unable to Verify |",
        "|----------|------------------|-------------------|------------------|",
        "| High Confidence | /10 | /10 | /10 |",
        "| Low Confidence | /10 | /10 | /10 |",
        "| Failures (missed) | /10 | /10 | /10 |",
        "",
        "### Notes",
        "",
        "_Add observations here_",
        "",
    ])

    return "\n".join(lines)


def format_table(results: list[dict], category: str) -> str:
    """Format results as markdown table"""
    if not results:
        return "_No results in this category_\n"

    lines = []

    # Header
    if category == "failure":
        lines.append("| # | Company | Domain | Phone | Vertical | Verify |")
        lines.append("|---|---------|--------|-------|----------|--------|")
    else:
        lines.append("| # | Company | Domain | Contact | Title | Email | Conf | Sources | Verify |")
        lines.append("|---|---------|--------|---------|-------|-------|------|---------|--------|")

    for i, r in enumerate(results, 1):
        company = r.get("company_name", "Unknown")[:30]
        domain = r.get("domain", "")
        phone = r.get("phone", "") or ""
        vertical = r.get("vertical", "")[:15]

        if category == "failure":
            lines.append(f"| {i} | {company} | [{domain}](https://{domain}) | {phone} | {vertical} | [ ] |")
        else:
            contact = r.get("owner_name") or r.get("contact_name") or ""
            title = r.get("owner_title") or r.get("contact_title") or ""
            email = r.get("contact_email") or ""
            conf = r.get("contact_confidence", 0) or r.get("confidence", 0)
            sources = ", ".join(r.get("contact_sources", [])[:2]) or "unknown"

            # Truncate long fields
            contact = contact[:25] if contact else ""
            title = title[:20] if title else ""
            email = email[:30] if email else ""
            sources = sources[:20]

            lines.append(f"| {i} | {company} | [{domain}](https://{domain}) | {contact} | {title} | {email} | {conf:.0f} | {sources} | [ ] |")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate spot-check sample")
    parser.add_argument(
        "--input",
        required=True,
        help="Path to pipeline results JSON"
    )
    parser.add_argument(
        "--output",
        default="evaluation/results/spotcheck.md",
        help="Output markdown file"
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=30,
        help="Total samples (divided across 3 categories)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed"
    )

    args = parser.parse_args()

    # Load results
    print(f"Loading results from: {args.input}")
    results = load_results(args.input)
    print(f"Total results: {len(results)}")

    # Stratify
    stratified = stratify_results(results)
    print(f"High confidence: {len(stratified['high_confidence'])}")
    print(f"Low confidence: {len(stratified['low_confidence'])}")
    print(f"Failures: {len(stratified['failures'])}")

    # Sample
    samples_per_cat = args.sample // 3
    samples = {
        "high_confidence": sample_category(stratified["high_confidence"], samples_per_cat, args.seed),
        "low_confidence": sample_category(stratified["low_confidence"], samples_per_cat, args.seed + 1),
        "failures": sample_category(stratified["failures"], samples_per_cat, args.seed + 2),
    }

    total_samples = sum(len(v) for v in samples.values())
    print(f"\nSampled: {total_samples} results")

    # Generate markdown
    markdown = generate_markdown(samples, args.input)

    # Save
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        f.write(markdown)

    print(f"Saved spot-check to: {output_path}")


if __name__ == "__main__":
    main()
