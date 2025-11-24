#!/usr/bin/env python3
"""
Testing framework for domain resolver
Validates accuracy against ground truth dataset
"""
import asyncio
import pandas as pd
import yaml
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from domain_resolver import DomainResolver, setup_logging


def calculate_metrics(df_results: pd.DataFrame, df_truth: pd.DataFrame) -> dict:
    """
    Calculate accuracy metrics by comparing results to ground truth

    Args:
        df_results: Results from resolver
        df_truth: Ground truth data

    Returns:
        Dict with metrics
    """
    # Merge on company name
    merged = df_results.merge(
        df_truth,
        left_on='company_name',
        right_on='name',
        how='inner',
        suffixes=('_result', '_truth')
    )

    total = len(merged)

    if total == 0:
        return {'error': 'No matching companies between results and ground truth'}

    # True Positives: Correct domain found
    merged['correct'] = merged.apply(
        lambda row: row['domain'] == row['expected_domain'] if pd.notna(row['domain']) else False,
        axis=1
    )

    true_positives = merged['correct'].sum()

    # False Positives: Wrong domain found
    merged['false_positive'] = merged.apply(
        lambda row: (pd.notna(row['domain']) and
                    row['domain'] != row['expected_domain']),
        axis=1
    )
    false_positives = merged['false_positive'].sum()

    # False Negatives: Correct domain not found
    merged['false_negative'] = merged.apply(
        lambda row: (pd.isna(row['domain']) and
                    pd.notna(row['expected_domain'])),
        axis=1
    )
    false_negatives = merged['false_negative'].sum()

    # True Negatives: Correctly identified as not found (if applicable)
    merged['true_negative'] = merged.apply(
        lambda row: (pd.isna(row['domain']) and
                    pd.isna(row['expected_domain'])),
        axis=1
    )
    true_negatives = merged['true_negative'].sum()

    # Calculate metrics
    accuracy = (true_positives + true_negatives) / total if total > 0 else 0
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    # Confidence calibration
    high_conf_correct = merged[(merged['confidence'] >= 85) & merged['correct']].shape[0]
    high_conf_total = merged[merged['confidence'] >= 85].shape[0]
    high_conf_accuracy = high_conf_correct / high_conf_total if high_conf_total > 0 else 0

    medium_conf_correct = merged[(merged['confidence'] >= 70) & (merged['confidence'] < 85) & merged['correct']].shape[0]
    medium_conf_total = merged[(merged['confidence'] >= 70) & (merged['confidence'] < 85)].shape[0]
    medium_conf_accuracy = medium_conf_correct / medium_conf_total if medium_conf_total > 0 else 0

    return {
        'total_companies': total,
        'true_positives': true_positives,
        'false_positives': false_positives,
        'false_negatives': false_negatives,
        'true_negatives': true_negatives,
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1_score': f1_score,
        'coverage': (true_positives + false_positives) / total,
        'high_conf_accuracy': high_conf_accuracy,
        'high_conf_count': high_conf_total,
        'medium_conf_accuracy': medium_conf_accuracy,
        'medium_conf_count': medium_conf_total
    }


def print_metrics_report(metrics: dict):
    """Print formatted metrics report"""
    print("\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)
    print(f"Total companies tested: {metrics['total_companies']}")
    print(f"\nConfusion Matrix:")
    print(f"  True Positives:  {metrics['true_positives']}")
    print(f"  False Positives: {metrics['false_positives']}")
    print(f"  False Negatives: {metrics['false_negatives']}")
    print(f"  True Negatives:  {metrics['true_negatives']}")
    print(f"\nPerformance Metrics:")
    print(f"  Accuracy:  {metrics['accuracy']*100:.1f}%")
    print(f"  Precision: {metrics['precision']*100:.1f}%")
    print(f"  Recall:    {metrics['recall']*100:.1f}%")
    print(f"  F1 Score:  {metrics['f1_score']*100:.1f}%")
    print(f"  Coverage:  {metrics['coverage']*100:.1f}%")
    print(f"\nConfidence Calibration:")
    print(f"  High confidence (≥85): {metrics['high_conf_accuracy']*100:.1f}% accurate ({metrics['high_conf_count']} companies)")
    print(f"  Medium confidence (70-84): {metrics['medium_conf_accuracy']*100:.1f}% accurate ({metrics['medium_conf_count']} companies)")
    print("="*60 + "\n")


def analyze_failures(df_results: pd.DataFrame, df_truth: pd.DataFrame):
    """Analyze and print failure cases"""
    merged = df_results.merge(
        df_truth,
        left_on='company_name',
        right_on='name',
        how='inner'
    )

    failures = merged[
        (merged['domain'] != merged['expected_domain']) |
        (pd.isna(merged['domain']) & pd.notna(merged['expected_domain']))
    ]

    if len(failures) == 0:
        print("✓ No failures - perfect accuracy!")
        return

    print("\n" + "="*60)
    print(f"FAILURE ANALYSIS ({len(failures)} cases)")
    print("="*60)

    for idx, row in failures.iterrows():
        print(f"\nCompany: {row['company_name']}")
        print(f"  Expected: {row['expected_domain']}")
        print(f"  Got:      {row['domain'] if pd.notna(row['domain']) else 'NOT FOUND'}")
        print(f"  Confidence: {row['confidence']}")
        print(f"  Source: {row['source']}")
        print(f"  Method: {row['method']}")
        if 'error' in row and pd.notna(row['error']):
            print(f"  Error: {row['error']}")

    print("="*60 + "\n")


async def run_tests():
    """Run test suite"""
    # Load config
    config_path = Path(__file__).parent.parent / "config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)

    setup_logging(config)

    # Load test data
    test_companies_path = Path(__file__).parent / "test_companies.csv"
    ground_truth_path = Path(__file__).parent / "ground_truth.csv"

    if not test_companies_path.exists():
        print(f"Error: Test data not found: {test_companies_path}")
        sys.exit(1)

    if not ground_truth_path.exists():
        print(f"Error: Ground truth not found: {ground_truth_path}")
        print("Please create ground_truth.csv with columns: name, expected_domain")
        sys.exit(1)

    df_test = pd.read_csv(test_companies_path)
    df_truth = pd.read_csv(ground_truth_path)

    print(f"\nLoaded {len(df_test)} test companies")
    print(f"Loaded {len(df_truth)} ground truth entries")

    # Run resolver
    companies = df_test.to_dict('records')
    resolver = DomainResolver(config)

    print("\nRunning domain resolution...\n")
    df_results = await resolver.resolve_batch(companies, max_workers=5)

    # Calculate metrics
    metrics = calculate_metrics(df_results, df_truth)

    # Print reports
    print_metrics_report(metrics)
    analyze_failures(df_results, df_truth)

    # Save test results
    output_path = Path(__file__).parent / "test_results.csv"
    df_results.to_csv(output_path, index=False)
    print(f"✓ Test results saved to: {output_path}")

    # Pass/fail decision
    if metrics['accuracy'] >= 0.95 and metrics['high_conf_accuracy'] >= 0.98:
        print("\n✓✓ TESTS PASSED - Accuracy targets met!")
        return 0
    else:
        print("\n✗ TESTS FAILED - Accuracy below target")
        print(f"  Target: 95% overall, 98% high-confidence")
        print(f"  Actual: {metrics['accuracy']*100:.1f}% overall, {metrics['high_conf_accuracy']*100:.1f}% high-confidence")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_tests())
    sys.exit(exit_code)
