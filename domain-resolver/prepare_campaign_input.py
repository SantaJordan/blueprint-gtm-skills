#!/usr/bin/env python3
"""
Transform Campaign 1 CSV into domain-resolver input format.

Maps:
- provider_name → name
- city → city
- serper_phone → phone
- address → address
- Adds context: "nursing home healthcare"
"""

import pandas as pd
import sys
from pathlib import Path

def prepare_campaign_input(input_file, output_file):
    """Transform campaign CSV to domain-resolver input format."""

    print(f"Reading campaign data from: {input_file}")
    df = pd.read_csv(input_file)

    print(f"Total records: {len(df)}")

    # Create new dataframe with domain-resolver columns
    resolver_input = pd.DataFrame({
        'name': df['provider_name'],
        'city': df['city'],
        'phone': df['serper_phone'],
        'address': df['address'],
        'context': 'nursing home healthcare'
    })

    # Keep CCN as reference column for later merging
    resolver_input['ccn'] = df['ccn']

    # Clean up any missing values
    resolver_input['phone'] = resolver_input['phone'].fillna('')
    resolver_input['address'] = resolver_input['address'].fillna('')

    # Remove any rows with missing critical data (name or city)
    before_clean = len(resolver_input)
    resolver_input = resolver_input.dropna(subset=['name', 'city'])
    after_clean = len(resolver_input)

    if before_clean > after_clean:
        print(f"Warning: Removed {before_clean - after_clean} records with missing name or city")

    # Save to output
    resolver_input.to_csv(output_file, index=False)
    print(f"\nSaved {len(resolver_input)} records to: {output_file}")

    # Print sample
    print("\nSample of prepared data:")
    print(resolver_input.head(3).to_string(index=False))

    return len(resolver_input)

if __name__ == "__main__":
    # Default paths
    input_file = Path(__file__).parent.parent / "Campaign 1_ Inspection Cluster Warning - Final Companies.csv"
    output_file = Path(__file__).parent / "input" / "campaign_one_input.csv"

    # Create input directory if it doesn't exist
    output_file.parent.mkdir(exist_ok=True)

    # Allow command line override
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]

    count = prepare_campaign_input(input_file, output_file)
    print(f"\n✓ Ready to process {count} nursing home facilities")
