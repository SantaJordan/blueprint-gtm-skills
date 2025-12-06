#!/usr/bin/env python3
"""
Analyze cost-effectiveness of different pipeline strategies.
Calculate ROI for different source combinations and verticals.
"""

import json
from collections import defaultdict
from typing import Dict, List, Any

def load_results(file_path: str) -> List[Dict[str, Any]]:
    """Load JSON results file."""
    with open(file_path, 'r') as f:
        data = json.load(f)
        if isinstance(data, dict) and 'results' in data:
            return data['results']
        return data

def analyze_cost_by_source_combination(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Calculate cost-effectiveness for different source combinations."""

    # Define costs per source
    source_costs = {
        'google_maps': 0.002,
        'google_maps_owner': 0.002,
        'openweb_contacts': 0.002,
        'social_links': 0.002,
        'serper_osint': 0.001,
        'data_fill': 0.001,
        'bbb_discovery': 0.003,
        'page_scrape': 0.002,
        'schema_org': 0.001
    }

    # Track results by source combination
    combo_stats = defaultdict(lambda: {
        'companies': 0,
        'companies_with_valid': 0,
        'total_contacts': 0,
        'valid_contacts': 0,
        'estimated_cost': 0.0
    })

    for result in results:
        # Calculate cost for this company
        stages = result.get('stages_completed', [])
        company_cost = 0.0

        # Map stages to costs
        stage_cost_map = {
            'google_maps': 0.002,
            'openweb_contacts': 0.002,
            'social_links': 0.002,
            'serper_osint': 0.001,
            'data_fill': 0.001,
            'bbb_discovery': 0.003,
            'website_fallback': 0.002,
            'early_exit_gmaps': 0.0,  # No additional cost
            'validation': 0.0  # No cost (internal)
        }

        for stage in stages:
            company_cost += stage_cost_map.get(stage, 0.0)

        # Get primary sources from contacts
        sources_used = set()
        contacts = result.get('contacts', [])
        for contact in contacts:
            for source in contact.get('sources', []):
                sources_used.add(source)

        # Create combo key from sorted sources
        combo_key = ' + '.join(sorted(sources_used)) if sources_used else 'no_sources'

        # Update stats
        has_valid = any(c.get('is_valid', False) for c in contacts)
        valid_count = sum(1 for c in contacts if c.get('is_valid', False))

        combo_stats[combo_key]['companies'] += 1
        combo_stats[combo_key]['total_contacts'] += len(contacts)
        combo_stats[combo_key]['valid_contacts'] += valid_count
        combo_stats[combo_key]['estimated_cost'] += company_cost
        if has_valid:
            combo_stats[combo_key]['companies_with_valid'] += 1

    # Calculate metrics
    results = []
    for combo, stats in combo_stats.items():
        if stats['companies'] < 3:  # Skip small samples
            continue

        avg_cost = stats['estimated_cost'] / stats['companies'] if stats['companies'] > 0 else 0
        success_rate = (stats['companies_with_valid'] / stats['companies'] * 100) if stats['companies'] > 0 else 0
        valid_per_dollar = stats['valid_contacts'] / stats['estimated_cost'] if stats['estimated_cost'] > 0 else 0
        cost_per_valid = stats['estimated_cost'] / stats['valid_contacts'] if stats['valid_contacts'] > 0 else 0

        results.append({
            'combination': combo,
            'companies': stats['companies'],
            'success_rate': success_rate,
            'avg_cost_per_company': avg_cost,
            'valid_contacts': stats['valid_contacts'],
            'cost_per_valid_contact': cost_per_valid,
            'valid_contacts_per_dollar': valid_per_dollar,
            'total_cost': stats['estimated_cost']
        })

    # Sort by valid contacts per dollar (ROI)
    results.sort(key=lambda x: x['valid_contacts_per_dollar'], reverse=True)
    return results

def analyze_vertical_roi(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Calculate ROI by vertical."""

    vertical_stats = defaultdict(lambda: {
        'companies': 0,
        'companies_with_valid': 0,
        'valid_contacts': 0,
        'estimated_cost': 0.0
    })

    for result in results:
        vertical = result.get('vertical', 'unknown')

        # Calculate cost
        stages = result.get('stages_completed', [])
        stage_cost_map = {
            'google_maps': 0.002,
            'openweb_contacts': 0.002,
            'social_links': 0.002,
            'serper_osint': 0.001,
            'data_fill': 0.001,
            'bbb_discovery': 0.003,
            'website_fallback': 0.002,
            'early_exit_gmaps': 0.0,
            'validation': 0.0
        }

        company_cost = sum(stage_cost_map.get(stage, 0.0) for stage in stages)

        # Track stats
        contacts = result.get('contacts', [])
        has_valid = any(c.get('is_valid', False) for c in contacts)
        valid_count = sum(1 for c in contacts if c.get('is_valid', False))

        vertical_stats[vertical]['companies'] += 1
        vertical_stats[vertical]['estimated_cost'] += company_cost
        vertical_stats[vertical]['valid_contacts'] += valid_count
        if has_valid:
            vertical_stats[vertical]['companies_with_valid'] += 1

    # Calculate metrics
    roi_results = []
    for vertical, stats in vertical_stats.items():
        if stats['companies'] < 10:  # Skip small samples
            continue

        success_rate = (stats['companies_with_valid'] / stats['companies'] * 100) if stats['companies'] > 0 else 0
        avg_cost = stats['estimated_cost'] / stats['companies'] if stats['companies'] > 0 else 0
        cost_per_valid = stats['estimated_cost'] / stats['valid_contacts'] if stats['valid_contacts'] > 0 else 0
        valid_per_dollar = stats['valid_contacts'] / stats['estimated_cost'] if stats['estimated_cost'] > 0 else 0

        roi_results.append({
            'vertical': vertical,
            'companies': stats['companies'],
            'success_rate': success_rate,
            'avg_cost_per_company': avg_cost,
            'valid_contacts': stats['valid_contacts'],
            'cost_per_valid_contact': cost_per_valid,
            'valid_contacts_per_dollar': valid_per_dollar
        })

    # Sort by valid contacts per dollar
    roi_results.sort(key=lambda x: x['valid_contacts_per_dollar'], reverse=True)
    return roi_results

def print_report(source_roi: List[Dict[str, Any]], vertical_roi: List[Dict[str, Any]]):
    """Print cost-effectiveness report."""
    print("=" * 100)
    print("COST-EFFECTIVENESS ANALYSIS")
    print("=" * 100)

    print("\n1. SOURCE COMBINATION ROI (Sorted by Valid Contacts per Dollar)")
    print("=" * 100)
    print(f"\n{'Source Combination':<40} {'Companies':<12} {'Success%':<10} {'Avg Cost':<10} {'Cost/Valid':<12} {'Valid/$':<10}")
    print("-" * 100)

    for combo in source_roi[:15]:  # Top 15
        print(f"{combo['combination'][:40]:<40} "
              f"{combo['companies']:<12} "
              f"{combo['success_rate']:<10.1f} "
              f"${combo['avg_cost_per_company']:<9.3f} "
              f"${combo['cost_per_valid_contact']:<11.3f} "
              f"{combo['valid_contacts_per_dollar']:<10.1f}")

    print("\n\n2. VERTICAL ROI ANALYSIS (Sorted by Valid Contacts per Dollar)")
    print("=" * 100)
    print(f"\n{'Vertical':<25} {'Companies':<12} {'Success%':<10} {'Avg Cost':<10} {'Cost/Valid':<12} {'Valid/$':<10}")
    print("-" * 100)

    for vertical in vertical_roi:
        print(f"{vertical['vertical']:<25} "
              f"{vertical['companies']:<12} "
              f"{vertical['success_rate']:<10.1f} "
              f"${vertical['avg_cost_per_company']:<9.3f} "
              f"${vertical['cost_per_valid_contact']:<11.3f} "
              f"{vertical['valid_contacts_per_dollar']:<10.1f}")

    print("\n\n3. STRATEGY RECOMMENDATIONS")
    print("=" * 100)

    # Best overall ROI
    best_combo = source_roi[0]
    print(f"\nBEST ROI STRATEGY:")
    print(f"  Source: {best_combo['combination']}")
    print(f"  Success Rate: {best_combo['success_rate']:.1f}%")
    print(f"  Cost per Company: ${best_combo['avg_cost_per_company']:.3f}")
    print(f"  Cost per Valid Contact: ${best_combo['cost_per_valid_contact']:.3f}")
    print(f"  Valid Contacts per Dollar: {best_combo['valid_contacts_per_dollar']:.1f}")

    # Best vertical
    best_vertical = vertical_roi[0]
    print(f"\nBEST VERTICAL FOR ROI:")
    print(f"  Vertical: {best_vertical['vertical']}")
    print(f"  Success Rate: {best_vertical['success_rate']:.1f}%")
    print(f"  Cost per Valid Contact: ${best_vertical['cost_per_valid_contact']:.3f}")
    print(f"  Valid Contacts per Dollar: {best_vertical['valid_contacts_per_dollar']:.1f}")

    # Budget scenarios
    print(f"\n\nBUDGET SCENARIOS:")
    print("-" * 100)

    print("\nScenario 1: $100 Budget - Maximum Volume")
    best_volume = max(source_roi[:5], key=lambda x: x['valid_contacts_per_dollar'])
    companies = int(100 / best_volume['avg_cost_per_company'])
    valid_contacts = int(companies * best_volume['success_rate'] / 100)
    print(f"  Strategy: {best_volume['combination']}")
    print(f"  Companies to process: ~{companies}")
    print(f"  Expected valid contacts: ~{valid_contacts}")
    print(f"  Cost per valid: ${100/valid_contacts:.2f}")

    print("\nScenario 2: $100 Budget - Best Quality")
    best_quality = max(source_roi[:5], key=lambda x: x['success_rate'])
    companies = int(100 / best_quality['avg_cost_per_company'])
    valid_contacts = int(companies * best_quality['success_rate'] / 100)
    print(f"  Strategy: {best_quality['combination']}")
    print(f"  Companies to process: ~{companies}")
    print(f"  Expected valid contacts: ~{valid_contacts}")
    print(f"  Success rate: {best_quality['success_rate']:.1f}%")

    print("\nScenario 3: $1000 Budget - Focus on Best Vertical")
    companies = int(1000 / best_vertical['avg_cost_per_company'])
    valid_contacts = int(companies * best_vertical['success_rate'] / 100)
    print(f"  Vertical: {best_vertical['vertical']}")
    print(f"  Companies to process: ~{companies}")
    print(f"  Expected valid contacts: ~{valid_contacts}")
    print(f"  Success rate: {best_vertical['success_rate']:.1f}%")

    print("\n" + "=" * 100)

def main():
    """Main execution."""
    results_file = "/Users/jordancrawford/Desktop/Blueprint-GTM-Skills/evaluation/results/yelp_940_results.json"

    print(f"Loading results from: {results_file}")
    results = load_results(results_file)

    print("Calculating cost-effectiveness metrics...")
    source_roi = analyze_cost_by_source_combination(results)
    vertical_roi = analyze_vertical_roi(results)

    print_report(source_roi, vertical_roi)

if __name__ == "__main__":
    main()
