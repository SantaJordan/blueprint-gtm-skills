#!/usr/bin/env python3
"""
Prepare SMB Sample from Yelp Business Data

Loads Yelp business JSON, filters by target categories,
samples 100 per category, and outputs in SMB pipeline format.

Usage:
    python -m evaluation.scripts.prepare_yelp_sample \
        --input ~/Downloads/bd_20250806_032310_0.json \
        --sample-per-category 100 \
        --output evaluation/data/yelp_diverse_1000.json
"""

import argparse
import json
import random
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from urllib.parse import urlparse


# Target categories for diverse SMB testing
TARGET_CATEGORIES = [
    "Plumbing",
    "Heating & Air Conditioning/HVAC",
    "Electricians",
    "Movers",
    "Junk Removal & Hauling",
    "Tree Services",
    "Auto Repair",
    "General Contractors",
    "Roofing",
    "Landscaping",
]

# Mapping from Yelp category to simplified vertical name
CATEGORY_TO_VERTICAL = {
    "Plumbing": "plumbing",
    "Heating & Air Conditioning/HVAC": "hvac",
    "Electricians": "electricians",
    "Movers": "movers",
    "Junk Removal & Hauling": "junk_removal",
    "Tree Services": "tree_services",
    "Auto Repair": "auto_repair",
    "General Contractors": "general_contractors",
    "Roofing": "roofing",
    "Landscaping": "landscaping",
}


@dataclass
class SMBCompany:
    """A company in SMB pipeline format"""
    company_name: str
    domain: str
    vertical: str
    address: str | None = None
    phone: str | None = None
    place_id: str | None = None
    rating: float | None = None
    reviews: int | None = None
    yelp_url: str | None = None


def extract_domain(website: str | None) -> str | None:
    """Extract clean domain from website URL"""
    if not website:
        return None

    website = website.strip()
    if not website:
        return None

    # Add scheme if missing
    if not website.startswith(('http://', 'https://')):
        website = 'https://' + website

    try:
        parsed = urlparse(website)
        domain = parsed.netloc or parsed.path.split('/')[0]

        # Remove www prefix
        if domain.startswith('www.'):
            domain = domain[4:]

        # Basic validation
        if '.' not in domain or len(domain) < 4:
            return None

        return domain.lower()
    except Exception:
        return None


def categorize_business(categories: list[str] | None) -> str | None:
    """Find which target category a business belongs to"""
    if not categories:
        return None

    for cat in categories:
        if cat in TARGET_CATEGORIES:
            return cat
    return None


def load_and_filter_yelp_data(input_path: str) -> dict[str, list[dict]]:
    """Load Yelp JSON and filter by target categories"""
    print(f"Loading Yelp data from: {input_path}")

    with open(input_path, 'r') as f:
        data = json.load(f)

    print(f"Total records: {len(data)}")

    # Group by target category
    by_category: dict[str, list[dict]] = {cat: [] for cat in TARGET_CATEGORIES}

    for biz in data:
        # Must have website
        website = biz.get('website')
        if not website:
            continue

        domain = extract_domain(website)
        if not domain:
            continue

        # Must have name
        name = biz.get('name', '').strip()
        if not name:
            continue

        # Find matching category
        categories = biz.get('categories', [])
        target_cat = categorize_business(categories)

        if target_cat:
            by_category[target_cat].append(biz)

    # Report counts
    print("\nBusinesses with websites per category:")
    for cat, businesses in by_category.items():
        print(f"  {cat}: {len(businesses)}")

    return by_category


def sample_and_transform(
    by_category: dict[str, list[dict]],
    sample_per_category: int,
    seed: int
) -> list[SMBCompany]:
    """Sample from each category and transform to SMB format"""
    random.seed(seed)

    all_companies = []

    for category, businesses in by_category.items():
        vertical = CATEGORY_TO_VERTICAL.get(category, category.lower().replace(' ', '_'))

        # Sample (or take all if fewer available)
        if len(businesses) > sample_per_category:
            sampled = random.sample(businesses, sample_per_category)
        else:
            sampled = businesses
            print(f"Warning: Only {len(businesses)} available for {category} (wanted {sample_per_category})")

        # Transform to SMB format
        for biz in sampled:
            domain = extract_domain(biz.get('website'))
            if not domain:
                continue

            company = SMBCompany(
                company_name=biz.get('name', '').strip(),
                domain=domain,
                vertical=vertical,
                address=biz.get('full_address'),
                phone=biz.get('phone_number'),
                place_id=biz.get('yelp_biz_id'),  # Use Yelp ID as place_id
                rating=biz.get('overall_rating'),
                reviews=biz.get('reviews_count'),
                yelp_url=biz.get('url'),
            )
            all_companies.append(company)

    # Shuffle
    random.shuffle(all_companies)

    return all_companies


def main():
    parser = argparse.ArgumentParser(description="Prepare SMB sample from Yelp data")
    parser.add_argument(
        "--input",
        required=True,
        help="Path to Yelp JSON file"
    )
    parser.add_argument(
        "--sample-per-category",
        type=int,
        default=100,
        help="Number of companies to sample per category (default: 100)"
    )
    parser.add_argument(
        "--output",
        default="evaluation/data/yelp_diverse_1000.json",
        help="Output JSON file path"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )

    args = parser.parse_args()

    # Verify input exists
    if not Path(args.input).exists():
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)

    print(f"Input: {args.input}")
    print(f"Sample per category: {args.sample_per_category}")
    print(f"Random seed: {args.seed}")
    print(f"Target categories: {len(TARGET_CATEGORIES)}")

    # Load and filter
    by_category = load_and_filter_yelp_data(args.input)

    # Sample and transform
    companies = sample_and_transform(
        by_category,
        sample_per_category=args.sample_per_category,
        seed=args.seed
    )

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    by_vertical = {}
    for c in companies:
        by_vertical[c.vertical] = by_vertical.get(c.vertical, 0) + 1

    for vertical, count in sorted(by_vertical.items()):
        print(f"  {vertical}: {count}")

    print(f"\nTotal companies: {len(companies)}")

    # Create output directory
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save JSON
    output_data = [asdict(c) for c in companies]
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"\nSaved to: {output_path}")


if __name__ == "__main__":
    main()
