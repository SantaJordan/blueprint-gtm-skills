#!/usr/bin/env python3
"""
Generate simple ASCII charts for vertical analysis.
"""

import json


def generate_bar_chart(data, title, width=60):
    """Generate ASCII bar chart."""
    print(f"\n{title}")
    print("=" * width)

    max_val = max(data.values())
    for label, value in sorted(data.items(), key=lambda x: x[1], reverse=True):
        bar_width = int((value / max_val) * (width - 30))
        bar = "█" * bar_width
        print(f"{label:<25} {bar} {value:.1f}%")


def main():
    # Load analysis
    with open('/Users/jordancrawford/Desktop/Blueprint-GTM-Skills/evaluation/results/yelp_940_results_vertical_analysis.json', 'r') as f:
        analysis = json.load(f)

    print("\n" + "=" * 80)
    print("SMB CONTACT DISCOVERY - VISUAL PERFORMANCE SUMMARY")
    print("=" * 80)

    # Success rates
    success_rates = {v: d['success_rate'] for v, d in analysis.items()}
    generate_bar_chart(success_rates, "SUCCESS RATE BY VERTICAL")

    # Average confidence
    confidence_scores = {v: d['avg_confidence'] for v, d in analysis.items()}
    generate_bar_chart(confidence_scores, "\nAVERAGE CONFIDENCE SCORE BY VERTICAL")

    # Email coverage
    email_coverage = {v: d['has_email_pct'] for v, d in analysis.items()}
    generate_bar_chart(email_coverage, "\nEMAIL COVERAGE BY VERTICAL")

    # Phone coverage
    phone_coverage = {v: d['has_phone_pct'] for v, d in analysis.items()}
    generate_bar_chart(phone_coverage, "\nPHONE COVERAGE BY VERTICAL")

    # Processing time
    processing_time = {v: d['avg_processing_time'] for v, d in analysis.items()}
    print(f"\n\nPROCESSING TIME BY VERTICAL")
    print("=" * 60)
    max_time = max(processing_time.values())
    for label, value in sorted(processing_time.items(), key=lambda x: x[1]):
        bar_width = int((value / max_time) * 30)
        bar = "█" * bar_width
        print(f"{label:<25} {bar} {value:.2f}s")

    # Summary stats
    print(f"\n\n{'=' * 80}")
    print("KEY STATISTICS")
    print("=" * 80)

    avg_success = sum(success_rates.values()) / len(success_rates)
    avg_email = sum(email_coverage.values()) / len(email_coverage)
    avg_phone = sum(phone_coverage.values()) / len(phone_coverage)

    print(f"\nOverall Average Success Rate:  {avg_success:.1f}%")
    print(f"Overall Average Email Coverage: {avg_email:.1f}%")
    print(f"Overall Average Phone Coverage: {avg_phone:.1f}%")

    best = max(success_rates.items(), key=lambda x: x[1])
    worst = min(success_rates.items(), key=lambda x: x[1])
    print(f"\nBest Performer:  {best[0]} ({best[1]:.1f}%)")
    print(f"Worst Performer: {worst[0]} ({worst[1]:.1f}%)")
    print(f"Performance Gap: {best[1] - worst[1]:.1f} percentage points")

    print("\n" + "=" * 80 + "\n")


if __name__ == '__main__':
    main()
