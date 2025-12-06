#!/usr/bin/env python3
"""
Analyze failure patterns in SMB contact discovery results.
"""
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Any

def load_results(file_path: str) -> List[Dict[str, Any]]:
    """Load results from JSON file."""
    with open(file_path, 'r') as f:
        data = json.load(f)
        # Handle both formats: direct list or dict with 'results' key
        if isinstance(data, dict) and 'results' in data:
            return data['results']
        return data

def analyze_failures(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze failure patterns in results."""

    # Initialize counters
    total_companies = len(results)
    no_contacts_found = 0
    all_invalid_contacts = 0
    has_valid_contacts = 0
    has_errors = 0

    # Pattern tracking
    error_messages = Counter()
    failure_verticals = Counter()
    no_contact_verticals = Counter()
    invalid_contact_verticals = Counter()

    # Detailed failure categories
    failure_categories = {
        'no_contacts': [],
        'all_invalid': [],
        'with_errors': [],
        'partial_success': []
    }

    for result in results:
        company_name = result.get('company_name', 'Unknown')
        vertical = result.get('vertical', 'Unknown')
        contacts = result.get('contacts', [])
        errors = result.get('errors', [])

        # Count errors
        if errors:
            has_errors += 1
            for error in errors:
                error_messages[error] += 1
            failure_categories['with_errors'].append({
                'company': company_name,
                'vertical': vertical,
                'errors': errors,
                'contacts_found': len(contacts)
            })

        # Analyze contacts
        if not contacts:
            no_contacts_found += 1
            no_contact_verticals[vertical] += 1
            failure_categories['no_contacts'].append({
                'company': company_name,
                'vertical': vertical,
                'errors': errors
            })
        else:
            # Check if any contacts are valid
            valid_contacts = [c for c in contacts if c.get('is_valid', False)]

            if not valid_contacts:
                all_invalid_contacts += 1
                invalid_contact_verticals[vertical] += 1
                failure_categories['all_invalid'].append({
                    'company': company_name,
                    'vertical': vertical,
                    'contacts_count': len(contacts),
                    'contacts': contacts[:3]  # Sample first 3
                })
            else:
                has_valid_contacts += 1
                if len(valid_contacts) < len(contacts):
                    failure_categories['partial_success'].append({
                        'company': company_name,
                        'vertical': vertical,
                        'valid': len(valid_contacts),
                        'total': len(contacts)
                    })

        # Track verticals with any kind of failure
        if not contacts or not any(c.get('is_valid', False) for c in contacts) or errors:
            failure_verticals[vertical] += 1

    # Calculate rates
    no_contacts_rate = (no_contacts_found / total_companies) * 100
    all_invalid_rate = (all_invalid_contacts / total_companies) * 100
    has_valid_rate = (has_valid_contacts / total_companies) * 100
    has_errors_rate = (has_errors / total_companies) * 100

    # Total failures (no contacts OR all invalid)
    total_failures = no_contacts_found + all_invalid_contacts
    total_failure_rate = (total_failures / total_companies) * 100

    return {
        'summary': {
            'total_companies': total_companies,
            'no_contacts_found': no_contacts_found,
            'no_contacts_rate': f"{no_contacts_rate:.1f}%",
            'all_invalid_contacts': all_invalid_contacts,
            'all_invalid_rate': f"{all_invalid_rate:.1f}%",
            'total_failures': total_failures,
            'total_failure_rate': f"{total_failure_rate:.1f}%",
            'has_valid_contacts': has_valid_contacts,
            'has_valid_rate': f"{has_valid_rate:.1f}%",
            'has_errors': has_errors,
            'has_errors_rate': f"{has_errors_rate:.1f}%"
        },
        'error_patterns': {
            'top_10_errors': error_messages.most_common(10),
            'total_unique_errors': len(error_messages)
        },
        'vertical_analysis': {
            'no_contacts_by_vertical': dict(no_contact_verticals.most_common()),
            'all_invalid_by_vertical': dict(invalid_contact_verticals.most_common()),
            'total_failures_by_vertical': dict(failure_verticals.most_common())
        },
        'failure_samples': {
            'no_contacts_sample': failure_categories['no_contacts'][:5],
            'all_invalid_sample': failure_categories['all_invalid'][:5],
            'with_errors_sample': failure_categories['with_errors'][:5],
            'partial_success_sample': failure_categories['partial_success'][:5]
        }
    }

def analyze_invalid_reasons(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze why contacts were marked invalid."""

    invalid_reasons = Counter()
    validation_score_distribution = defaultdict(int)

    for result in results:
        contacts = result.get('contacts', [])
        for contact in contacts:
            if not contact.get('is_valid', False):
                # Try to infer why it's invalid
                score = contact.get('validation_score', 0)
                validation_score_distribution[score] += 1

                sources = contact.get('sources', [])
                email = contact.get('email', '')
                phone = contact.get('phone', '')
                name = contact.get('name', '')
                title = contact.get('title', '')

                # Categorize reasons
                if score == 0:
                    invalid_reasons['zero_score'] += 1
                elif score < 50:
                    invalid_reasons['below_threshold'] += 1

                if not email and not phone:
                    invalid_reasons['no_contact_info'] += 1
                if not name:
                    invalid_reasons['no_name'] += 1
                if not sources:
                    invalid_reasons['no_sources'] += 1
                if email and '@' not in email:
                    invalid_reasons['invalid_email_format'] += 1

    return {
        'invalid_reasons': dict(invalid_reasons.most_common()),
        'validation_score_distribution': dict(sorted(validation_score_distribution.items()))
    }

def print_report(analysis: Dict[str, Any], invalid_analysis: Dict[str, Any]):
    """Print formatted analysis report."""

    print("=" * 80)
    print("SMB CONTACT DISCOVERY - FAILURE ANALYSIS REPORT")
    print("=" * 80)
    print()

    # Summary
    summary = analysis['summary']
    print("EXECUTIVE SUMMARY")
    print("-" * 80)
    print(f"Total Companies Analyzed: {summary['total_companies']}")
    print(f"Complete Failures: {summary['total_failures']} ({summary['total_failure_rate']})")
    print(f"  - No Contacts Found: {summary['no_contacts_found']} ({summary['no_contacts_rate']})")
    print(f"  - All Contacts Invalid: {summary['all_invalid_contacts']} ({summary['all_invalid_rate']})")
    print(f"Success (Valid Contacts): {summary['has_valid_contacts']} ({summary['has_valid_rate']})")
    print(f"Companies with Errors: {summary['has_errors']} ({summary['has_errors_rate']})")
    print()

    # Error patterns
    print("MOST COMMON ERROR MESSAGES")
    print("-" * 80)
    for error, count in analysis['error_patterns']['top_10_errors']:
        pct = (count / summary['total_companies']) * 100
        print(f"{count:4d} ({pct:5.1f}%) - {error}")
    print()

    # Vertical analysis
    print("FAILURE RATES BY VERTICAL")
    print("-" * 80)
    print(f"{'Vertical':<30} {'No Contacts':<15} {'All Invalid':<15} {'Total Failures':<15}")
    print("-" * 80)

    all_verticals = set(
        list(analysis['vertical_analysis']['no_contacts_by_vertical'].keys()) +
        list(analysis['vertical_analysis']['all_invalid_by_vertical'].keys()) +
        list(analysis['vertical_analysis']['total_failures_by_vertical'].keys())
    )

    for vertical in sorted(all_verticals):
        no_contacts = analysis['vertical_analysis']['no_contacts_by_vertical'].get(vertical, 0)
        all_invalid = analysis['vertical_analysis']['all_invalid_by_vertical'].get(vertical, 0)
        total_fail = analysis['vertical_analysis']['total_failures_by_vertical'].get(vertical, 0)
        print(f"{vertical:<30} {no_contacts:<15} {all_invalid:<15} {total_fail:<15}")
    print()

    # Invalid contact reasons
    print("WHY CONTACTS ARE MARKED INVALID")
    print("-" * 80)
    for reason, count in invalid_analysis['invalid_reasons'].items():
        print(f"{count:4d} - {reason}")
    print()

    print("VALIDATION SCORE DISTRIBUTION (Invalid Contacts)")
    print("-" * 80)
    for score, count in list(invalid_analysis['validation_score_distribution'].items())[:20]:
        print(f"Score {score:3d}: {count:4d} contacts")
    print()

    # Sample failures
    print("SAMPLE FAILURES - NO CONTACTS FOUND")
    print("-" * 80)
    for i, sample in enumerate(analysis['failure_samples']['no_contacts_sample'], 1):
        print(f"{i}. {sample['company']} ({sample['vertical']})")
        if sample['errors']:
            print(f"   Errors: {sample['errors'][:2]}")
    print()

    print("SAMPLE FAILURES - ALL CONTACTS INVALID")
    print("-" * 80)
    for i, sample in enumerate(analysis['failure_samples']['all_invalid_sample'], 1):
        print(f"{i}. {sample['company']} ({sample['vertical']}) - {sample['contacts_count']} contacts found")
        if sample['contacts']:
            for c in sample['contacts'][:2]:
                print(f"   - {c.get('name', 'N/A')} ({c.get('title', 'N/A')}) - Score: {c.get('validation_score', 0)}")
    print()

    # Recommendations
    print("RECOMMENDATIONS TO REDUCE FAILURES")
    print("-" * 80)

    recommendations = []

    # Based on no contacts
    no_contact_rate = float(summary['no_contacts_rate'].rstrip('%'))
    if no_contact_rate > 30:
        recommendations.append(
            f"1. HIGH NO-CONTACT RATE ({summary['no_contacts_rate']}): "
            "Add more discovery sources or improve Google Maps/website scraping accuracy"
        )

    # Based on invalid contacts
    invalid_rate = float(summary['all_invalid_rate'].rstrip('%'))
    if invalid_rate > 20:
        recommendations.append(
            f"2. HIGH INVALID RATE ({summary['all_invalid_rate']}): "
            "Lower validation threshold from 50 or improve data quality scoring"
        )

    # Based on error patterns
    top_error = analysis['error_patterns']['top_10_errors'][0] if analysis['error_patterns']['top_10_errors'] else None
    if top_error:
        error_msg, error_count = top_error
        error_pct = (error_count / summary['total_companies']) * 100
        if error_pct > 10:
            recommendations.append(
                f"3. FREQUENT ERROR ({error_pct:.1f}%): '{error_msg}' - "
                "Investigate and fix this specific failure mode"
            )

    # Vertical-specific
    worst_vertical = max(
        analysis['vertical_analysis']['total_failures_by_vertical'].items(),
        key=lambda x: x[1]
    ) if analysis['vertical_analysis']['total_failures_by_vertical'] else None

    if worst_vertical:
        vertical_name, vertical_failures = worst_vertical
        recommendations.append(
            f"4. VERTICAL-SPECIFIC ISSUES: '{vertical_name}' has {vertical_failures} failures - "
            "Consider vertical-specific discovery strategies"
        )

    # Invalid reasons
    if invalid_analysis['invalid_reasons']:
        top_invalid_reason = max(invalid_analysis['invalid_reasons'].items(), key=lambda x: x[1])
        reason, count = top_invalid_reason
        recommendations.append(
            f"5. VALIDATION IMPROVEMENT: {count} contacts marked invalid due to '{reason}' - "
            "Review validation logic for this category"
        )

    for rec in recommendations:
        print(rec)
        print()

def main():
    """Main analysis function."""
    results_file = "/Users/jordancrawford/Desktop/Blueprint-GTM-Skills/evaluation/results/yelp_940_results.json"

    print("Loading results...")
    results = load_results(results_file)

    print(f"Analyzing {len(results)} companies...")
    analysis = analyze_failures(results)
    invalid_analysis = analyze_invalid_reasons(results)

    print_report(analysis, invalid_analysis)

    # Save detailed analysis
    output_file = results_file.replace('.json', '_failure_analysis.json')
    with open(output_file, 'w') as f:
        json.dump({
            'failure_analysis': analysis,
            'invalid_analysis': invalid_analysis
        }, f, indent=2)

    print(f"\nDetailed analysis saved to: {output_file}")

if __name__ == "__main__":
    main()
