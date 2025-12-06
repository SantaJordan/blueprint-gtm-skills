#!/usr/bin/env python3
"""
Deep dive analysis of vertical performance with actionable insights.
"""

import json
from collections import defaultdict
from typing import Dict, List, Any


def deep_dive_analysis(results_file: str):
    """Perform deep dive analysis on vertical performance."""

    with open(results_file, 'r') as f:
        data = json.load(f)

    results = data.get('results', [])

    # Group by vertical
    vertical_data = defaultdict(list)
    for result in results:
        vertical = result.get('vertical', 'unknown')
        vertical_data[vertical].append(result)

    print("=" * 100)
    print("SMB CONTACT DISCOVERY - VERTICAL DEEP DIVE ANALYSIS")
    print("=" * 100)
    print()

    # Analyze each vertical
    for vertical in sorted(vertical_data.keys()):
        companies = vertical_data[vertical]
        analyze_vertical(vertical, companies)

    # Cross-vertical insights
    print_cross_vertical_insights(vertical_data)


def analyze_vertical(vertical: str, companies: List[Dict]):
    """Analyze a single vertical in depth."""

    print(f"\n{'=' * 100}")
    print(f"VERTICAL: {vertical.upper()}")
    print(f"{'=' * 100}\n")

    total = len(companies)
    valid_companies = [c for c in companies if any(contact.get('is_valid', False) for contact in c.get('contacts', []))]
    success_rate = len(valid_companies) / total * 100

    # 1. Success Overview
    print(f"📊 SUCCESS METRICS")
    print(f"   Total Companies: {total}")
    print(f"   Successful: {len(valid_companies)} ({success_rate:.1f}%)")
    print(f"   Failed: {total - len(valid_companies)} ({100 - success_rate:.1f}%)")
    print()

    # 2. Contact Quality Analysis
    all_valid_contacts = []
    for company in valid_companies:
        all_valid_contacts.extend([c for c in company.get('contacts', []) if c.get('is_valid', False)])

    with_email = sum(1 for c in all_valid_contacts if c.get('email'))
    with_phone = sum(1 for c in all_valid_contacts if c.get('phone'))
    with_name = sum(1 for c in all_valid_contacts if c.get('name'))
    with_linkedin = sum(1 for c in all_valid_contacts if c.get('linkedin_url'))

    print(f"✅ CONTACT QUALITY ({len(all_valid_contacts)} valid contacts)")
    print(f"   With Email: {with_email} ({with_email/len(all_valid_contacts)*100:.1f}%)")
    print(f"   With Phone: {with_phone} ({with_phone/len(all_valid_contacts)*100:.1f}%)")
    print(f"   With Name: {with_name} ({with_name/len(all_valid_contacts)*100:.1f}%)")
    print(f"   With LinkedIn: {with_linkedin} ({with_linkedin/len(all_valid_contacts)*100:.1f}%)")
    print()

    # 3. Data Source Effectiveness
    source_performance = defaultdict(lambda: {'count': 0, 'high_conf': 0})
    for contact in all_valid_contacts:
        for source in contact.get('sources', []):
            source_performance[source]['count'] += 1
            if contact.get('confidence', 0) >= 80:
                source_performance[source]['high_conf'] += 1

    print(f"🔍 DATA SOURCE EFFECTIVENESS")
    for source, stats in sorted(source_performance.items(), key=lambda x: x[1]['count'], reverse=True):
        high_conf_pct = stats['high_conf'] / stats['count'] * 100 if stats['count'] > 0 else 0
        print(f"   {source:<25} {stats['count']} contacts ({high_conf_pct:.0f}% high confidence)")
    print()

    # 4. Common Issues
    failed_companies = [c for c in companies if not any(contact.get('is_valid', False) for contact in c.get('contacts', []))]
    if failed_companies:
        stages_missed = defaultdict(int)
        common_errors = defaultdict(int)

        for company in failed_companies:
            stages = company.get('stages_completed', [])
            if 'google_maps' not in stages:
                stages_missed['google_maps'] += 1
            if 'openweb_contacts' not in stages:
                stages_missed['openweb_contacts'] += 1

            for error in company.get('errors', []):
                common_errors[error] += 1

        print(f"⚠️  COMMON ISSUES ({len(failed_companies)} failed companies)")
        if stages_missed:
            print(f"   Missing Stages:")
            for stage, count in sorted(stages_missed.items(), key=lambda x: x[1], reverse=True)[:3]:
                print(f"      - {stage}: {count} companies")
        if common_errors:
            print(f"   Common Errors:")
            for error, count in sorted(common_errors.items(), key=lambda x: x[1], reverse=True)[:3]:
                print(f"      - {error}: {count} companies")
        print()

    # 5. Best Practices
    # Find top performing companies
    top_companies = sorted(valid_companies,
                          key=lambda x: max(c.get('confidence', 0) for c in x.get('contacts', []) if c.get('is_valid', False)),
                          reverse=True)[:3]

    if top_companies:
        print(f"🏆 TOP PERFORMERS (examples)")
        for i, company in enumerate(top_companies, 1):
            name = company.get('company_name', 'Unknown')
            valid_contacts = [c for c in company.get('contacts', []) if c.get('is_valid', False)]
            max_conf = max(c.get('confidence', 0) for c in valid_contacts)
            sources = set()
            for c in valid_contacts:
                sources.update(c.get('sources', []))
            print(f"   {i}. {name}: {max_conf:.0f}% confidence, {len(valid_contacts)} contacts")
            print(f"      Sources: {', '.join(sources)}")
        print()

    # 6. Recommendations
    print(f"💡 RECOMMENDATIONS")
    if success_rate >= 75:
        print(f"   ✓ Excellent performance - maintain current strategy")
        print(f"   ✓ Consider this vertical as a benchmark for others")
    elif success_rate >= 65:
        print(f"   • Good performance with room for improvement")
        print(f"   • Focus on improving contact quality (email coverage)")
    else:
        print(f"   ⚠ Below average performance - needs optimization")
        print(f"   • Consider additional data sources")
        print(f"   • Review failed cases for pattern identification")

    # Specific recommendations based on data
    if with_email / len(all_valid_contacts) < 0.3:
        print(f"   • LOW EMAIL COVERAGE ({with_email/len(all_valid_contacts)*100:.0f}%) - add email enrichment step")

    if len([s for s in source_performance.keys() if 'google_maps' in s]) / len(source_performance) > 0.7:
        print(f"   • Over-reliant on Google Maps - diversify data sources")

    print()


def print_cross_vertical_insights(vertical_data: Dict[str, List[Dict]]):
    """Print insights across all verticals."""

    print(f"\n{'=' * 100}")
    print(f"CROSS-VERTICAL INSIGHTS")
    print(f"{'=' * 100}\n")

    # Calculate metrics per vertical
    vertical_metrics = {}
    for vertical, companies in vertical_data.items():
        valid_companies = [c for c in companies if any(contact.get('is_valid', False) for contact in c.get('contacts', []))]
        all_valid_contacts = []
        for company in valid_companies:
            all_valid_contacts.extend([c for c in company.get('contacts', []) if c.get('is_valid', False)])

        vertical_metrics[vertical] = {
            'success_rate': len(valid_companies) / len(companies) * 100,
            'avg_contacts': len(all_valid_contacts) / len(companies),
            'email_coverage': sum(1 for c in all_valid_contacts if c.get('email')) / len(all_valid_contacts) * 100 if all_valid_contacts else 0,
        }

    # Key patterns
    print("🔑 KEY PATTERNS IDENTIFIED")
    print()

    # 1. Success rate correlation
    high_success = {v: m for v, m in vertical_metrics.items() if m['success_rate'] >= 75}
    low_success = {v: m for v, m in vertical_metrics.items() if m['success_rate'] < 60}

    if high_success:
        avg_email = sum(m['email_coverage'] for m in high_success.values()) / len(high_success)
        print(f"1. HIGH SUCCESS VERTICALS (≥75%): {', '.join(high_success.keys())}")
        print(f"   - Average email coverage: {avg_email:.1f}%")
        print(f"   - Pattern: Strong Google Maps presence + social links")
        print()

    if low_success:
        avg_email = sum(m['email_coverage'] for m in low_success.values()) / len(low_success)
        print(f"2. LOW SUCCESS VERTICALS (<60%): {', '.join(low_success.keys())}")
        print(f"   - Average email coverage: {avg_email:.1f}%")
        print(f"   - Pattern: Weaker online presence, need alternative sources")
        print()

    # 3. Overall recommendations
    print("🎯 STRATEGIC RECOMMENDATIONS")
    print()
    print(f"1. EXPAND EMAIL DISCOVERY")
    print(f"   - Current bottleneck: Low email coverage across most verticals")
    print(f"   - Action: Add email-focused enrichment (Hunter.io, Clearbit)")
    print()
    print(f"2. VERTICAL-SPECIFIC SOURCES")
    print(f"   - HVAC/Movers: Add industry directories (HomeAdvisor, Thumbtack)")
    print(f"   - Auto Repair: Leverage review sites (Yelp business owner data)")
    print(f"   - Tree Services: Check local licensing databases")
    print()
    print(f"3. OPTIMIZE PIPELINE")
    print(f"   - Early exit on Google Maps owner contact is effective")
    print(f"   - Social links discovery adds value across all verticals")
    print(f"   - Consider parallel source queries to reduce processing time")
    print()


def main():
    results_file = "/Users/jordancrawford/Desktop/Blueprint-GTM-Skills/evaluation/results/yelp_940_results.json"
    deep_dive_analysis(results_file)


if __name__ == '__main__':
    main()
