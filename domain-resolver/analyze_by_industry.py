#!/usr/bin/env python3
"""
Industry-Specific Analysis Tool

Analyzes domain resolver results grouped by industry
Compares performance across different industries
"""
import pandas as pd
import sys
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_data(results_path: str, ground_truth_path: str, test_input_path: str) -> tuple:
    """Load all required data files"""

    logger.info("Loading data files...")

    try:
        results = pd.read_csv(results_path)
        ground_truth = pd.read_csv(ground_truth_path)
        test_input = pd.read_csv(test_input_path)

        logger.info(f"✓ Results: {len(results)} companies")
        logger.info(f"✓ Ground truth: {len(ground_truth)} companies")
        logger.info(f"✓ Test input: {len(test_input)} companies")

        return results, ground_truth, test_input

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)


def merge_datasets(results: pd.DataFrame, ground_truth: pd.DataFrame,
                  test_input: pd.DataFrame) -> pd.DataFrame:
    """Merge all datasets on company name"""

    # Merge results with ground truth
    merged = results.merge(
        ground_truth,
        left_on='company_name',
        right_on='name',
        how='inner',
        suffixes=('_result', '_truth')
    )

    # Merge with test input to get industry
    merged = merged.merge(
        test_input[['name', 'context']],
        left_on='company_name',
        right_on='name',
        how='inner'
    )

    # Extract industry from context
    merged['industry'] = merged['context'].str.split().str[0]

    return merged


def calculate_industry_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate metrics per industry"""

    # Mark correct matches
    df['correct'] = df.apply(
        lambda row: row['domain'] == row['expected_domain'] if pd.notna(row['domain']) else False,
        axis=1
    )

    # Group by industry
    industry_stats = []

    for industry in df['industry'].unique():
        industry_df = df[df['industry'] == industry]

        total = len(industry_df)
        correct = industry_df['correct'].sum()
        found = industry_df['domain'].notna().sum()

        accuracy = (correct / total * 100) if total > 0 else 0
        coverage = (found / total * 100) if total > 0 else 0

        # Confidence stats
        avg_confidence = industry_df['confidence'].mean()
        high_conf_count = (industry_df['confidence'] >= 85).sum()
        high_conf_accuracy = 100.0

        high_conf_df = industry_df[industry_df['confidence'] >= 85]
        if len(high_conf_df) > 0:
            high_conf_correct = high_conf_df['correct'].sum()
            high_conf_accuracy = (high_conf_correct / len(high_conf_df) * 100)

        # Stage distribution
        stage_counts = industry_df['source'].value_counts().to_dict()

        # Manual review rate
        manual_review_rate = (industry_df['needs_manual_review'].sum() / total * 100) if total > 0 else 0

        industry_stats.append({
            'Industry': industry,
            'Total': total,
            'Correct': correct,
            'Found': found,
            'Accuracy %': round(accuracy, 1),
            'Coverage %': round(coverage, 1),
            'Avg Confidence': round(avg_confidence, 1),
            'High Conf (≥85)': high_conf_count,
            'High Conf Acc %': round(high_conf_accuracy, 1),
            'Manual Review %': round(manual_review_rate, 1),
            'Stages': stage_counts
        })

    return pd.DataFrame(industry_stats)


def print_industry_report(stats_df: pd.DataFrame):
    """Print formatted industry comparison report"""

    print("\n" + "="*80)
    print("INDUSTRY-SPECIFIC PERFORMANCE ANALYSIS")
    print("="*80)

    for idx, row in stats_df.iterrows():
        print(f"\n{row['Industry'].upper()}")
        print("-" * 60)
        print(f"  Total Companies:       {row['Total']}")
        print(f"  Domains Found:         {row['Found']} ({row['Coverage %']:.1f}% coverage)")
        print(f"  Correct Matches:       {row['Correct']} ({row['Accuracy %']:.1f}% accuracy)")
        print(f"  Average Confidence:    {row['Avg Confidence']:.1f}")
        print(f"  High Confidence (≥85): {row['High Conf (≥85)']} ({row['High Conf Acc %']:.1f}% accurate)")
        print(f"  Manual Review Needed:  {row['Manual Review %']:.1f}%")

        # Stage breakdown
        print(f"\n  Resolution Sources:")
        stages = row['Stages']
        if isinstance(stages, dict):
            for stage, count in sorted(stages.items(), key=lambda x: -x[1]):
                pct = (count / row['Total'] * 100)
                print(f"    - {stage}: {count} ({pct:.1f}%)")

    print("\n" + "="*80)
    print("COMPARATIVE SUMMARY")
    print("="*80)

    # Sort by accuracy
    sorted_stats = stats_df.sort_values('Accuracy %', ascending=False)

    print(f"\n{'Industry':<15} {'Accuracy':<12} {'Coverage':<12} {'Avg Conf':<12} {'Manual Review'}")
    print("-" * 70)

    for _, row in sorted_stats.iterrows():
        print(f"{row['Industry']:<15} {row['Accuracy %']:<11.1f}% {row['Coverage %']:<11.1f}% "
              f"{row['Avg Confidence']:<11.1f} {row['Manual Review %']:.1f}%")

    print("\n" + "="*80)


def analyze_failures_by_industry(df: pd.DataFrame):
    """Analyze failure patterns per industry"""

    print("\n" + "="*80)
    print("FAILURE ANALYSIS BY INDUSTRY")
    print("="*80)

    failures = df[~df['correct'] | df['domain'].isna()]

    if len(failures) == 0:
        print("\n✓ No failures detected!")
        return

    for industry in df['industry'].unique():
        industry_failures = failures[failures['industry'] == industry]

        if len(industry_failures) == 0:
            continue

        print(f"\n{industry.upper()} - {len(industry_failures)} failures")
        print("-" * 60)

        # Failure types
        not_found = industry_failures[industry_failures['domain'].isna()]
        wrong_domain = industry_failures[industry_failures['domain'].notna()]

        print(f"  Not Found:     {len(not_found)} ({len(not_found)/len(industry_failures)*100:.1f}%)")
        print(f"  Wrong Domain:  {len(wrong_domain)} ({len(wrong_domain)/len(industry_failures)*100:.1f}%)")

        # Sample failures
        if len(industry_failures) > 0:
            print(f"\n  Sample Failures:")
            for idx, row in industry_failures.head(3).iterrows():
                print(f"    - {row['company_name']}")
                print(f"      Expected: {row['expected_domain']}")
                print(f"      Got:      {row['domain'] if pd.notna(row['domain']) else 'NOT FOUND'}")
                print(f"      Confidence: {row['confidence']}")

    print("\n" + "="*80)


def save_industry_report(stats_df: pd.DataFrame, output_path: str = "output/industry_analysis.csv"):
    """Save industry stats to CSV"""

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Drop the Stages dict column for CSV export
    export_df = stats_df.drop('Stages', axis=1)
    export_df.to_csv(output_path, index=False)

    logger.info(f"\n✓ Industry analysis saved to: {output_path}")


def main():
    """Main entry point"""

    if len(sys.argv) < 4:
        print("Usage: python analyze_by_industry.py <results_csv> <ground_truth_csv> <test_input_csv>")
        print("\nExample:")
        print("  python analyze_by_industry.py output/test_diverse_results.csv \\")
        print("         test/ground_truth_diverse.csv test/test_companies_diverse.csv")
        sys.exit(1)

    results_path = sys.argv[1]
    ground_truth_path = sys.argv[2]
    test_input_path = sys.argv[3]

    # Load data
    results, ground_truth, test_input = load_data(results_path, ground_truth_path, test_input_path)

    # Merge datasets
    merged = merge_datasets(results, ground_truth, test_input)

    # Calculate industry metrics
    stats_df = calculate_industry_metrics(merged)

    # Print reports
    print_industry_report(stats_df)
    analyze_failures_by_industry(merged)

    # Save results
    save_industry_report(stats_df)

    print("\n✓✓ Industry analysis complete!")


if __name__ == "__main__":
    main()
