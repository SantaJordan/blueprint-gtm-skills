#!/usr/bin/env python3
"""
Compare V1 (original) vs V2 (LLM-verified) domain resolution results
"""

import pandas as pd
from pathlib import Path

def compare_results():
    """Compare V1 and V2 results"""

    # Read both results
    v1_file = Path("output/campaign_one_resolved.csv")
    v2_file = Path("output/campaign_one_resolved_v2.csv")

    print("="*80)
    print("DOMAIN RESOLVER V1 vs V2 COMPARISON")
    print("="*80)
    print()

    v1 = pd.read_csv(v1_file)
    v2 = pd.read_csv(v2_file)

    print(f"V1 Results: {len(v1)} companies")
    print(f"V2 Results: {len(v2)} companies")
    print()

    # Overall metrics
    print("="*80)
    print("OVERALL METRICS")
    print("="*80)

    metrics = pd.DataFrame({
        'Metric': [
            'Total Companies',
            'Domains Found',
            'Success Rate',
            'High Confidence (≥85)',
            'High Confidence Rate',
            'Needs Manual Review',
            'Manual Review Rate'
        ],
        'V1': [
            len(v1),
            v1['domain'].notna().sum(),
            f"{v1['domain'].notna().sum()/len(v1)*100:.1f}%",
            (v1['confidence'] >= 85).sum(),
            f"{(v1['confidence'] >= 85).sum()/len(v1)*100:.1f}%",
            v1['needs_manual_review'].sum(),
            f"{v1['needs_manual_review'].sum()/len(v1)*100:.1f}%"
        ],
        'V2': [
            len(v2),
            v2['domain'].notna().sum(),
            f"{v2['domain'].notna().sum()/len(v2)*100:.1f}%",
            (v2['confidence'] >= 85).sum(),
            f"{(v2['confidence'] >= 85).sum()/len(v2)*100:.1f}%",
            v2['needs_manual_review'].sum(),
            f"{v2['needs_manual_review'].sum()/len(v2)*100:.1f}%"
        ]
    })

    print(metrics.to_string(index=False))
    print()

    # Find changed domains
    print("="*80)
    print("DOMAIN CHANGES (V1 → V2)")
    print("="*80)
    print()

    # Merge on company name
    comparison = v1.merge(
        v2,
        on='company_name',
        how='outer',
        suffixes=('_v1', '_v2')
    )

    # Find differences
    domain_changed = comparison[comparison['domain_v1'] != comparison['domain_v2']]

    if len(domain_changed) > 0:
        print(f"Found {len(domain_changed)} companies with changed domains:\n")

        for idx, row in domain_changed.iterrows():
            print(f"\n{row['company_name']}")
            print(f"  V1: {row['domain_v1']} (confidence: {row['confidence_v1']}, method: {row['method_v1']})")
            print(f"  V2: {row['domain_v2']} (confidence: {row['confidence_v2']}, method: {row['method_v2']})")

            # Check if it was a problematic domain
            v1_domain = str(row['domain_v1'])
            if 'usnews.com' in v1_domain or 'medicare.gov' in v1_domain or 'hanys.org' in v1_domain:
                print(f"  ✓ FIXED: Removed directory site!")
            elif 'trilogyhs.com' in v1_domain or 'communicarehealth.com' in v1_domain or 'futurecare.com' in v1_domain:
                print(f"  ⚠ Changed from parent company domain")
    else:
        print("No domain changes found")

    print()

    # Check for domains removed in V2
    print("="*80)
    print("DOMAINS REMOVED IN V2 (Previously Wrong)")
    print("="*80)
    print()

    removed = comparison[(comparison['domain_v1'].notna()) & (comparison['domain_v2'].isna())]

    if len(removed) > 0:
        print(f"Found {len(removed)} domains removed (likely incorrect in V1):\n")
        for idx, row in removed.iterrows():
            print(f"\n{row['company_name']}")
            print(f"  Removed: {row['domain_v1']} (confidence: {row['confidence_v1']})")
    else:
        print("No domains were removed")

    print()

    # Check for new domains added in V2
    print("="*80)
    print("DOMAINS ADDED IN V2 (Previously Not Found)")
    print("="*80)
    print()

    added = comparison[(comparison['domain_v1'].isna()) & (comparison['domain_v2'].notna())]

    if len(added) > 0:
        print(f"Found {len(added)} new domains in V2:\n")
        for idx, row in added.iterrows():
            print(f"\n{row['company_name']}")
            print(f"  Added: {row['domain_v2']} (confidence: {row['confidence_v2']})")
    else:
        print("No new domains were added")

    print()

    # Confidence distribution
    print("="*80)
    print("CONFIDENCE DISTRIBUTION")
    print("="*80)
    print()

    print("V1 Confidence Distribution:")
    print(f"  99%: {(v1['confidence'] == 99).sum()} companies")
    print(f"  85-98%: {((v1['confidence'] >= 85) & (v1['confidence'] < 99)).sum()} companies")
    print(f"  70-84%: {((v1['confidence'] >= 70) & (v1['confidence'] < 85)).sum()} companies")
    print(f"  50-69%: {((v1['confidence'] >= 50) & (v1['confidence'] < 70)).sum()} companies")
    print(f"  <50%: {(v1['confidence'] < 50).sum()} companies")

    print()

    print("V2 Confidence Distribution:")
    print(f"  95%: {(v2['confidence'] == 95).sum()} companies")
    print(f"  90%: {(v2['confidence'] == 90).sum()} companies")
    print(f"  85-89%: {((v2['confidence'] >= 85) & (v2['confidence'] < 90)).sum()} companies")
    print(f"  70-84%: {((v2['confidence'] >= 70) & (v2['confidence'] < 85)).sum()} companies")
    print(f"  <70%: {(v2['confidence'] < 70).sum()} companies")

    print()

    # Source distribution
    print("="*80)
    print("SOURCE DISTRIBUTION")
    print("="*80)
    print()

    print("V1 Sources:")
    print(v1['source'].value_counts().to_string())

    print("\nV2 Sources:")
    print(v2['source'].value_counts().to_string())

    print()
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print()

    # Calculate improvements
    v1_found = v1['domain'].notna().sum()
    v2_found = v2['domain'].notna().sum()
    v1_review = v1['needs_manual_review'].sum()
    v2_review = v2['needs_manual_review'].sum()

    print(f"✓ Domain changes: {len(domain_changed)}")
    print(f"✓ Domains removed (bad): {len(removed)}")
    print(f"✓ Domains added (new): {len(added)}")
    print(f"✓ Manual review reduced: {v1_review} → {v2_review} ({v1_review - v2_review} fewer)")
    print()

    if len(removed) > 0:
        print(f"🎯 SUCCESS: Eliminated {len(removed)} incorrect directory/parent company domains!")

    print()

if __name__ == "__main__":
    compare_results()
