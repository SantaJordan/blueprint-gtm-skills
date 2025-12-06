#!/usr/bin/env python3
"""
Analyze SMB contact discovery results by vertical/category.
"""

import json
from collections import defaultdict
from typing import Dict, List, Any
from pathlib import Path


def analyze_by_vertical(results_file: str) -> Dict[str, Any]:
    """Analyze results grouped by vertical."""

    # Load results
    with open(results_file, 'r') as f:
        data = json.load(f)

    results = data.get('results', [])

    # Group by vertical
    vertical_stats = defaultdict(lambda: {
        'total': 0,
        'successful': 0,
        'confidence_scores': [],
        'contact_counts': [],
        'processing_times': [],
        'sources_used': defaultdict(int),
        'has_email': 0,
        'has_phone': 0,
        'has_owner': 0,
        'high_confidence': 0,  # confidence >= 70
        'medium_confidence': 0,  # 50 <= confidence < 70
        'low_confidence': 0,  # confidence < 50
    })

    # Process each result
    for result in results:
        vertical = result.get('vertical', 'unknown')
        stats = vertical_stats[vertical]

        stats['total'] += 1

        # Success metrics - a company is successful if it has at least one valid contact
        contacts = result.get('contacts', [])
        valid_contacts = [c for c in contacts if c.get('is_valid', False)]
        success = len(valid_contacts) > 0
        if success:
            stats['successful'] += 1

        # Confidence scores - use highest confidence from valid contacts, or 0
        if valid_contacts:
            confidence = max(c.get('confidence', 0) for c in valid_contacts)
        else:
            confidence = 0
        stats['confidence_scores'].append(confidence)

        if confidence >= 70:
            stats['high_confidence'] += 1
        elif confidence >= 50:
            stats['medium_confidence'] += 1
        else:
            stats['low_confidence'] += 1

        # Contact counts - only count valid contacts
        stats['contact_counts'].append(len(valid_contacts))

        # Processing time
        processing_time = result.get('processing_time_ms', 0) / 1000  # Convert ms to seconds
        stats['processing_times'].append(processing_time)

        # Data sources - only from valid contacts
        for contact in valid_contacts:
            sources = contact.get('sources', [])
            for source in sources:
                stats['sources_used'][source] += 1

            # Contact details
            if contact.get('email'):
                stats['has_email'] += 1
            if contact.get('phone'):
                stats['has_phone'] += 1
            if contact.get('name') and contact.get('name') != result.get('company_name'):
                stats['has_owner'] += 1

    # Calculate aggregates
    vertical_summary = {}
    for vertical, stats in vertical_stats.items():
        if stats['total'] == 0:
            continue

        vertical_summary[vertical] = {
            'total_companies': stats['total'],
            'successful': stats['successful'],
            'success_rate': round(stats['successful'] / stats['total'] * 100, 2),
            'avg_confidence': round(sum(stats['confidence_scores']) / len(stats['confidence_scores']), 2) if stats['confidence_scores'] else 0,
            'avg_contacts_per_company': round(sum(stats['contact_counts']) / len(stats['contact_counts']), 2) if stats['contact_counts'] else 0,
            'avg_processing_time': round(sum(stats['processing_times']) / len(stats['processing_times']), 2) if stats['processing_times'] else 0,
            'has_email_pct': round(stats['has_email'] / stats['total'] * 100, 2),
            'has_phone_pct': round(stats['has_phone'] / stats['total'] * 100, 2),
            'has_owner_pct': round(stats['has_owner'] / stats['total'] * 100, 2),
            'high_confidence_pct': round(stats['high_confidence'] / stats['total'] * 100, 2),
            'medium_confidence_pct': round(stats['medium_confidence'] / stats['total'] * 100, 2),
            'low_confidence_pct': round(stats['low_confidence'] / stats['total'] * 100, 2),
            'top_sources': dict(sorted(stats['sources_used'].items(), key=lambda x: x[1], reverse=True)[:5])
        }

    return vertical_summary


def print_analysis(summary: Dict[str, Any]):
    """Print formatted analysis."""

    # Sort by success rate
    sorted_verticals = sorted(summary.items(), key=lambda x: x[1]['success_rate'], reverse=True)

    print("=" * 100)
    print("SMB CONTACT DISCOVERY - VERTICAL PERFORMANCE ANALYSIS")
    print("=" * 100)
    print()

    # 1. Ranking by Success Rate
    print("1. VERTICAL RANKING BY SUCCESS RATE")
    print("-" * 100)
    print(f"{'Rank':<6} {'Vertical':<25} {'Success Rate':<15} {'Companies':<12} {'Avg Confidence'}")
    print("-" * 100)

    for rank, (vertical, stats) in enumerate(sorted_verticals, 1):
        print(f"{rank:<6} {vertical:<25} {stats['success_rate']:.1f}%{'':<10} {stats['total_companies']:<12} {stats['avg_confidence']:.1f}")

    print()
    print()

    # 2. Detailed Metrics Table
    print("2. DETAILED METRICS BY VERTICAL")
    print("-" * 100)
    print(f"{'Vertical':<20} {'Success%':<10} {'Conf.':<8} {'Contacts':<10} {'Email%':<9} {'Phone%':<9} {'Owner%':<9} {'Time(s)'}")
    print("-" * 100)

    for vertical, stats in sorted_verticals:
        print(f"{vertical:<20} {stats['success_rate']:.1f}%{'':<5} {stats['avg_confidence']:.1f}{'':<4} "
              f"{stats['avg_contacts_per_company']:.2f}{'':<6} {stats['has_email_pct']:.1f}%{'':<4} "
              f"{stats['has_phone_pct']:.1f}%{'':<4} {stats['has_owner_pct']:.1f}%{'':<4} {stats['avg_processing_time']:.2f}")

    print()
    print()

    # 3. Confidence Distribution
    print("3. CONFIDENCE SCORE DISTRIBUTION BY VERTICAL")
    print("-" * 100)
    print(f"{'Vertical':<25} {'High (≥70%)':<15} {'Medium (50-69%)':<18} {'Low (<50%)'}")
    print("-" * 100)

    for vertical, stats in sorted_verticals:
        print(f"{vertical:<25} {stats['high_confidence_pct']:.1f}%{'':<11} "
              f"{stats['medium_confidence_pct']:.1f}%{'':<14} {stats['low_confidence_pct']:.1f}%")

    print()
    print()

    # 4. Top Data Sources by Vertical
    print("4. TOP DATA SOURCES BY VERTICAL")
    print("-" * 100)

    for vertical, stats in sorted_verticals:
        sources_str = ", ".join([f"{source}: {count}" for source, count in list(stats['top_sources'].items())[:3]])
        print(f"{vertical:<25} {sources_str}")

    print()
    print()

    # 5. Key Insights
    print("5. KEY INSIGHTS & ANALYSIS")
    print("-" * 100)

    # Best performers
    top_3 = sorted_verticals[:3]
    print(f"✓ BEST PERFORMERS:")
    for rank, (vertical, stats) in enumerate(top_3, 1):
        print(f"  {rank}. {vertical}: {stats['success_rate']:.1f}% success, {stats['avg_confidence']:.1f} avg confidence")

    print()

    # Worst performers
    bottom_3 = sorted_verticals[-3:]
    print(f"✗ LOWEST PERFORMERS:")
    for rank, (vertical, stats) in enumerate(reversed(bottom_3), 1):
        print(f"  {rank}. {vertical}: {stats['success_rate']:.1f}% success, {stats['avg_confidence']:.1f} avg confidence")

    print()

    # Overall stats
    total_companies = sum(s['total_companies'] for s in summary.values())
    overall_success = sum(s['successful'] for s in summary.values())
    overall_success_rate = overall_success / total_companies * 100 if total_companies > 0 else 0

    print(f"📊 OVERALL STATISTICS:")
    print(f"  Total Companies: {total_companies}")
    print(f"  Overall Success Rate: {overall_success_rate:.1f}%")
    print(f"  Best Vertical: {sorted_verticals[0][0]} ({sorted_verticals[0][1]['success_rate']:.1f}%)")
    print(f"  Worst Vertical: {sorted_verticals[-1][0]} ({sorted_verticals[-1][1]['success_rate']:.1f}%)")
    print(f"  Spread: {sorted_verticals[0][1]['success_rate'] - sorted_verticals[-1][1]['success_rate']:.1f} percentage points")

    print()
    print()

    # 6. Recommendations
    print("6. RECOMMENDATIONS FOR VERTICAL-SPECIFIC OPTIMIZATIONS")
    print("-" * 100)

    # Identify patterns
    high_performers = [v for v, s in sorted_verticals if s['success_rate'] >= 75]
    low_performers = [v for v, s in sorted_verticals if s['success_rate'] < 60]

    if high_performers:
        print(f"🎯 HIGH PERFORMERS ({', '.join(high_performers)}):")
        print(f"   - Already achieving >75% success rate")
        print(f"   - Maintain current data source strategy")
        print(f"   - Consider as benchmark for other verticals")
        print()

    if low_performers:
        print(f"⚠️  LOW PERFORMERS ({', '.join(low_performers)}):")
        print(f"   - Need additional data sources or enrichment")
        print(f"   - Consider vertical-specific crawling strategies")
        print(f"   - May benefit from social media discovery")
        print()

    # Source-specific insights
    print(f"📚 DATA SOURCE INSIGHTS:")
    all_sources = set()
    for stats in summary.values():
        all_sources.update(stats['top_sources'].keys())

    print(f"   - Sources in use: {', '.join(sorted(all_sources))}")
    print(f"   - Consider testing additional sources for low-performing verticals")
    print()

    # Time optimization
    fastest = min(sorted_verticals, key=lambda x: x[1]['avg_processing_time'])
    slowest = max(sorted_verticals, key=lambda x: x[1]['avg_processing_time'])

    print(f"⏱️  PROCESSING TIME:")
    print(f"   - Fastest: {fastest[0]} ({fastest[1]['avg_processing_time']:.2f}s)")
    print(f"   - Slowest: {slowest[0]} ({slowest[1]['avg_processing_time']:.2f}s)")
    if slowest[1]['avg_processing_time'] > fastest[1]['avg_processing_time'] * 2:
        print(f"   - Consider optimizing {slowest[0]} pipeline (>2x slower than fastest)")

    print()
    print("=" * 100)


def main():
    results_file = "/Users/jordancrawford/Desktop/Blueprint-GTM-Skills/evaluation/results/yelp_940_results.json"

    print("Loading and analyzing results...")
    summary = analyze_by_vertical(results_file)

    print_analysis(summary)

    # Save summary to file
    output_file = results_file.replace('.json', '_vertical_analysis.json')
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2)

    print()
    print(f"Detailed analysis saved to: {output_file}")


if __name__ == '__main__':
    main()
