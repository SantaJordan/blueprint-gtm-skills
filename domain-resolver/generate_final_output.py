#!/usr/bin/env python3
"""
Generate final two-column output: domain + confidence
Merges resolved domains back with original campaign data using company name matching.
"""

import pandas as pd
from pathlib import Path

def generate_final_output():
    """Create clean two-column output with CCN for reference."""

    # Read files
    input_file = Path("input/campaign_one_input.csv")
    resolved_file = Path("output/campaign_one_resolved_v2.csv")
    output_file = Path("output/campaign_one_final.csv")

    print("Reading input and resolved data...")
    input_df = pd.read_csv(input_file)
    resolved_df = pd.read_csv(resolved_file)

    # Merge on company name
    input_df['name_normalized'] = input_df['name'].str.strip().str.upper()
    resolved_df['name_normalized'] = resolved_df['company_name'].str.strip().str.upper()

    merged = input_df.merge(
        resolved_df[['name_normalized', 'domain', 'confidence', 'source', 'verified', 'needs_manual_review']],
        on='name_normalized',
        how='left'
    )

    # Create final output with CCN, company name, domain, and confidence
    final_output = pd.DataFrame({
        'ccn': merged['ccn'],
        'company_name': merged['name'],
        'domain': merged['domain'],
        'confidence': merged['confidence'],
        'source': merged['source'],
        'verified': merged['verified'],
        'needs_review': merged['needs_manual_review']
    })

    # Sort by confidence (descending) then by company name
    final_output = final_output.sort_values(['confidence', 'company_name'],
                                           ascending=[False, True])

    # Save full output
    final_output.to_csv(output_file, index=False)
    print(f"\n✓ Saved full output to: {output_file}")
    print(f"  Total records: {len(final_output)}")

    # Create simple two-column version
    simple_output = final_output[['domain', 'confidence']].copy()
    simple_file = Path("output/campaign_one_domains_simple.csv")
    simple_output.to_csv(simple_file, index=False)
    print(f"✓ Saved simple two-column output to: {simple_file}")

    # Statistics
    print("\n" + "="*60)
    print("RESULTS SUMMARY")
    print("="*60)

    total = len(final_output)
    found = final_output['domain'].notna().sum()
    not_found = total - found
    high_conf = (final_output['confidence'] >= 85).sum()
    medium_conf = ((final_output['confidence'] >= 70) & (final_output['confidence'] < 85)).sum()
    low_conf = ((final_output['confidence'] < 70) & (final_output['confidence'].notna())).sum()
    needs_review = final_output['needs_review'].sum() if 'needs_review' in final_output else 0

    print(f"Total facilities: {total}")
    print(f"Domains found: {found} ({found/total*100:.1f}%)")
    print(f"Domains not found: {not_found} ({not_found/total*100:.1f}%)")
    print()
    print("Confidence breakdown:")
    print(f"  High confidence (≥85): {high_conf} ({high_conf/total*100:.1f}%)")
    print(f"  Medium confidence (70-84): {medium_conf} ({medium_conf/total*100:.1f}%)")
    print(f"  Low confidence (<70): {low_conf} ({low_conf/total*100:.1f}%)")
    print(f"  Needs manual review: {needs_review}")
    print()

    # Show sample
    print("Sample of high-confidence results:")
    print(final_output[final_output['confidence'] >= 85].head(10).to_string(index=False))

    if not_found > 0:
        print("\n" + "="*60)
        print(f"Facilities without domains ({not_found}):")
        print("="*60)
        no_domain = final_output[final_output['domain'].isna()][['ccn', 'company_name']]
        print(no_domain.to_string(index=False))

    return final_output

if __name__ == "__main__":
    generate_final_output()
