#!/usr/bin/env python3
"""
Quick test of the business type classifier on sample data
"""

import json
import sys
from pathlib import Path
from collections import Counter

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "contact-finder"))

from modules.pipeline.adaptive_controller import classify_business_type, BusinessType


def main():
    input_file = Path(__file__).parent.parent / "data" / "smb_random_200.json"

    if not input_file.exists():
        print(f"Error: {input_file} not found")
        return

    with open(input_file) as f:
        data = json.load(f)

    # Classify each business
    results = []
    type_counts = Counter()

    for item in data:
        name = item.get("company_name", item.get("name", ""))
        category = item.get("category", item.get("vertical", ""))
        city = item.get("city", "")

        biz_type = classify_business_type(name, category, city)
        type_counts[biz_type] += 1
        results.append({
            "name": name,
            "category": category,
            "type": biz_type.value
        })

    # Print summary
    print("=" * 60)
    print("Business Type Classification Results")
    print("=" * 60)
    print(f"\nTotal: {len(results)}")
    print("\nBreakdown:")
    for biz_type in BusinessType:
        count = type_counts[biz_type]
        pct = count / len(results) * 100
        print(f"  {biz_type.value:12}: {count:4} ({pct:5.1f}%)")

    # Show examples of each type
    print("\n" + "=" * 60)
    print("Examples by Type")
    print("=" * 60)

    for biz_type in BusinessType:
        examples = [r for r in results if r["type"] == biz_type.value][:5]
        if examples:
            print(f"\n{biz_type.value.upper()}:")
            for ex in examples:
                print(f"  - {ex['name'][:50]:50} | {ex['category'][:20]}")

    # Save detailed results
    output_file = Path(__file__).parent.parent / "results" / "classifier_test.json"
    with open(output_file, "w") as f:
        json.dump({
            "summary": {t.value: type_counts[t] for t in BusinessType},
            "results": results
        }, f, indent=2)

    print(f"\nDetailed results saved to: {output_file}")


if __name__ == "__main__":
    main()
