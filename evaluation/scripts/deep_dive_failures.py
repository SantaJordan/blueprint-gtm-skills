#!/usr/bin/env python3
"""
Deep dive into specific failure patterns.
"""
import json
from collections import Counter
from typing import Dict, List, Any

def load_results(file_path: str) -> List[Dict[str, Any]]:
    """Load results from JSON file."""
    with open(file_path, 'r') as f:
        data = json.load(f)
        if isinstance(data, dict) and 'results' in data:
            return data['results']
        return data

def analyze_zero_score_contacts(results: List[Dict[str, Any]]):
    """Deep dive into why contacts have zero validation score."""

    zero_score_patterns = {
        'has_name_no_contact': [],
        'has_contact_no_name': [],
        'no_name_no_contact': [],
        'has_both_still_zero': [],
        'source_issues': Counter()
    }

    for result in results:
        company_name = result.get('company_name', 'Unknown')
        domain = result.get('domain', 'Unknown')
        contacts = result.get('contacts', [])

        for contact in contacts:
            score = contact.get('validation_score', 0)
            if score == 0:
                name = contact.get('name', '')
                email = contact.get('email', '')
                phone = contact.get('phone', '')
                sources = contact.get('sources', [])
                title = contact.get('title', '')

                has_name = bool(name)
                has_contact = bool(email or phone)

                sample = {
                    'company': company_name,
                    'domain': domain,
                    'name': name,
                    'title': title,
                    'email': email,
                    'phone': phone,
                    'sources': sources
                }

                # Track source patterns
                for source in sources:
                    zero_score_patterns['source_issues'][source] += 1

                # Categorize
                if has_name and not has_contact:
                    zero_score_patterns['has_name_no_contact'].append(sample)
                elif has_contact and not has_name:
                    zero_score_patterns['has_contact_no_name'].append(sample)
                elif not has_name and not has_contact:
                    zero_score_patterns['no_name_no_contact'].append(sample)
                else:
                    zero_score_patterns['has_both_still_zero'].append(sample)

    return zero_score_patterns

def analyze_no_contacts_reasons(results: List[Dict[str, Any]]):
    """Understand why some companies have no contacts found at all."""

    no_contact_patterns = {
        'completed_all_stages': [],
        'missing_stages': [],
        'stage_completion': Counter(),
        'has_errors': []
    }

    for result in results:
        contacts = result.get('contacts', [])
        if not contacts:
            company_name = result.get('company_name', 'Unknown')
            domain = result.get('domain', 'Unknown')
            stages = result.get('stages_completed', [])
            errors = result.get('errors', [])

            sample = {
                'company': company_name,
                'domain': domain,
                'stages_completed': stages,
                'errors': errors
            }

            # Track stage completion
            for stage in stages:
                no_contact_patterns['stage_completion'][stage] += 1

            if errors:
                no_contact_patterns['has_errors'].append(sample)
            elif len(stages) >= 5:  # Expected: google_maps, openweb_contacts, data_fill, social_links, validation
                no_contact_patterns['completed_all_stages'].append(sample)
            else:
                no_contact_patterns['missing_stages'].append(sample)

    return no_contact_patterns

def analyze_source_effectiveness(results: List[Dict[str, Any]]):
    """Analyze which sources produce valid vs invalid contacts."""

    source_stats = {}

    for result in results:
        contacts = result.get('contacts', [])
        for contact in contacts:
            is_valid = contact.get('is_valid', False)
            sources = contact.get('sources', [])
            score = contact.get('validation_score', 0)

            for source in sources:
                if source not in source_stats:
                    source_stats[source] = {
                        'total': 0,
                        'valid': 0,
                        'invalid': 0,
                        'zero_score': 0,
                        'score_distribution': []
                    }

                source_stats[source]['total'] += 1
                source_stats[source]['score_distribution'].append(score)

                if is_valid:
                    source_stats[source]['valid'] += 1
                else:
                    source_stats[source]['invalid'] += 1
                    if score == 0:
                        source_stats[source]['zero_score'] += 1

    # Calculate rates
    for source, stats in source_stats.items():
        stats['valid_rate'] = (stats['valid'] / stats['total'] * 100) if stats['total'] > 0 else 0
        stats['zero_score_rate'] = (stats['zero_score'] / stats['total'] * 100) if stats['total'] > 0 else 0
        stats['avg_score'] = sum(stats['score_distribution']) / len(stats['score_distribution']) if stats['score_distribution'] else 0

    return source_stats

def print_deep_dive_report(zero_score_patterns, no_contact_patterns, source_stats):
    """Print detailed failure analysis report."""

    print("=" * 80)
    print("DEEP DIVE: FAILURE ROOT CAUSES")
    print("=" * 80)
    print()

    # Zero score analysis
    print("WHY CONTACTS HAVE ZERO VALIDATION SCORE")
    print("-" * 80)
    print(f"Has Name, No Contact Info: {len(zero_score_patterns['has_name_no_contact'])}")
    print(f"Has Contact Info, No Name: {len(zero_score_patterns['has_contact_no_name'])}")
    print(f"No Name, No Contact Info: {len(zero_score_patterns['no_name_no_contact'])}")
    print(f"Has Both, Still Zero: {len(zero_score_patterns['has_both_still_zero'])}")
    print()

    print("Sample: Has Name, No Contact Info")
    for sample in zero_score_patterns['has_name_no_contact'][:3]:
        print(f"  - {sample['company']}: {sample['name']} ({sample['title']}) - Sources: {sample['sources']}")
    print()

    print("Sample: Has Contact Info, No Name")
    for sample in zero_score_patterns['has_contact_no_name'][:3]:
        print(f"  - {sample['company']}: {sample['email'] or sample['phone']} - Sources: {sample['sources']}")
    print()

    print("Sample: Has Both, Still Zero Score")
    for sample in zero_score_patterns['has_both_still_zero'][:5]:
        print(f"  - {sample['company']}: {sample['name']} ({sample['title']})")
        print(f"    Email: {sample['email']}, Phone: {sample['phone']}")
        print(f"    Sources: {sample['sources']}")
    print()

    # Sources associated with zero scores
    print("SOURCES PRODUCING ZERO-SCORE CONTACTS")
    print("-" * 80)
    for source, count in zero_score_patterns['source_issues'].most_common():
        print(f"{count:4d} - {source}")
    print()

    # No contacts analysis
    print("WHY NO CONTACTS WERE FOUND AT ALL")
    print("-" * 80)
    print(f"Completed All Stages: {len(no_contact_patterns['completed_all_stages'])}")
    print(f"Missing Stages: {len(no_contact_patterns['missing_stages'])}")
    print(f"Has Errors: {len(no_contact_patterns['has_errors'])}")
    print()

    print("Stage Completion for No-Contact Companies:")
    for stage, count in no_contact_patterns['stage_completion'].most_common():
        print(f"  {count:3d} - {stage}")
    print()

    print("Sample: Completed All Stages, No Contacts")
    for sample in no_contact_patterns['completed_all_stages'][:5]:
        print(f"  - {sample['company']} ({sample['domain']})")
        print(f"    Stages: {sample['stages_completed']}")
    print()

    print("Sample: Missing Stages")
    for sample in no_contact_patterns['missing_stages'][:5]:
        print(f"  - {sample['company']} ({sample['domain']})")
        print(f"    Stages: {sample['stages_completed']}")
    print()

    if no_contact_patterns['has_errors']:
        print("Sample: Has Errors")
        for sample in no_contact_patterns['has_errors'][:5]:
            print(f"  - {sample['company']} ({sample['domain']})")
            print(f"    Errors: {sample['errors']}")
        print()

    # Source effectiveness
    print("SOURCE EFFECTIVENESS ANALYSIS")
    print("-" * 80)
    print(f"{'Source':<30} {'Total':<8} {'Valid':<8} {'Invalid':<8} {'Zero%':<8} {'Avg Score':<10}")
    print("-" * 80)

    for source, stats in sorted(source_stats.items(), key=lambda x: x[1]['zero_score_rate'], reverse=True):
        print(f"{source:<30} {stats['total']:<8} {stats['valid']:<8} {stats['invalid']:<8} "
              f"{stats['zero_score_rate']:<8.1f} {stats['avg_score']:<10.1f}")
    print()

    # Key insights
    print("KEY INSIGHTS & PATTERNS")
    print("-" * 80)

    # Insight 1: Zero score breakdown
    total_zero_score = sum([
        len(zero_score_patterns['has_name_no_contact']),
        len(zero_score_patterns['has_contact_no_name']),
        len(zero_score_patterns['no_name_no_contact']),
        len(zero_score_patterns['has_both_still_zero'])
    ])

    if total_zero_score > 0:
        no_contact_pct = len(zero_score_patterns['has_name_no_contact']) / total_zero_score * 100
        no_name_pct = len(zero_score_patterns['has_contact_no_name']) / total_zero_score * 100
        neither_pct = len(zero_score_patterns['no_name_no_contact']) / total_zero_score * 100

        print(f"1. ZERO-SCORE BREAKDOWN:")
        print(f"   - {no_contact_pct:.1f}% have name but no contact info (email/phone)")
        print(f"   - {no_name_pct:.1f}% have contact info but no name")
        print(f"   - {neither_pct:.1f}% have neither name nor contact info")
        print()

    # Insight 2: Sources with high zero-score rates
    worst_sources = sorted(source_stats.items(), key=lambda x: x[1]['zero_score_rate'], reverse=True)[:3]
    if worst_sources:
        print(f"2. WORST PERFORMING SOURCES (by zero-score rate):")
        for source, stats in worst_sources:
            print(f"   - {source}: {stats['zero_score_rate']:.1f}% zero-score, avg score {stats['avg_score']:.1f}")
        print()

    # Insight 3: No contacts despite completing stages
    if no_contact_patterns['completed_all_stages']:
        print(f"3. PIPELINE GAPS:")
        print(f"   - {len(no_contact_patterns['completed_all_stages'])} companies completed all stages but found no contacts")
        print(f"   - This suggests data sources are returning empty results, not pipeline failures")
        print()

def main():
    """Main analysis function."""
    results_file = "/Users/jordancrawford/Desktop/Blueprint-GTM-Skills/evaluation/results/yelp_940_results.json"

    print("Loading results...")
    results = load_results(results_file)

    print(f"Analyzing {len(results)} companies...")
    print()

    zero_score_patterns = analyze_zero_score_contacts(results)
    no_contact_patterns = analyze_no_contacts_reasons(results)
    source_stats = analyze_source_effectiveness(results)

    print_deep_dive_report(zero_score_patterns, no_contact_patterns, source_stats)

if __name__ == "__main__":
    main()
