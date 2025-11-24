#!/usr/bin/env python3
"""
API Comparison Test Suite
Compares Discolike vs Ocean.io vs Both for domain resolution
"""
import asyncio
import pandas as pd
import yaml
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from domain_resolver import DomainResolver, setup_logging

logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def calculate_metrics(df_results: pd.DataFrame, df_truth: pd.DataFrame) -> dict:
    """Calculate accuracy metrics by comparing results to ground truth"""
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

    # True Negatives
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

    # Source breakdown
    source_stats = {}
    for source in merged['source'].unique():
        if pd.notna(source):
            source_df = merged[merged['source'] == source]
            source_stats[source] = {
                'count': len(source_df),
                'correct': source_df['correct'].sum(),
                'accuracy': source_df['correct'].sum() / len(source_df) if len(source_df) > 0 else 0
            }

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
        'medium_conf_count': medium_conf_total,
        'source_breakdown': source_stats,
        'merged_data': merged  # For detailed analysis
    }


async def run_test_configuration(config: Dict[str, Any],
                                 companies: List[Dict[str, Any]],
                                 config_name: str) -> tuple:
    """
    Run domain resolution with a specific configuration

    Args:
        config: Configuration dict
        companies: List of company dicts to resolve
        config_name: Name of this configuration (for logging)

    Returns:
        Tuple of (DataFrame results, duration in seconds)
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"RUNNING TEST: {config_name}")
    logger.info(f"{'='*60}")

    start_time = datetime.now()

    # Create resolver with this config
    resolver = DomainResolver(config)

    # Run resolution
    max_workers = config['processing']['max_workers']
    df_results = await resolver.resolve_batch(companies, max_workers=max_workers)

    duration = (datetime.now() - start_time).total_seconds()

    logger.info(f"\n✓ Test completed in {duration:.1f} seconds")

    return df_results, duration


async def compare_apis(test_input_path: str, ground_truth_path: str, output_dir: str = "test/results"):
    """
    Compare different API configurations

    Args:
        test_input_path: Path to test input CSV
        ground_truth_path: Path to ground truth CSV
        output_dir: Directory for output files
    """
    logger.info(f"\n{'='*60}")
    logger.info("API COMPARISON TEST SUITE")
    logger.info(f"{'='*60}\n")

    # Load base config
    config_path = "config.yaml"
    if not Path(config_path).exists():
        print(f"Error: {config_path} not found")
        sys.exit(1)

    with open(config_path) as f:
        base_config = yaml.safe_load(f)

    # Load test data
    df_input = pd.read_csv(test_input_path)
    df_truth = pd.read_csv(ground_truth_path)

    companies = df_input.to_dict('records')
    logger.info(f"Loaded {len(companies)} companies from: {test_input_path}")
    logger.info(f"Loaded {len(df_truth)} ground truth entries from: {ground_truth_path}\n")

    # Test configurations
    test_configs = []

    # 1. Baseline (no B2B enrichment)
    config_baseline = base_config.copy()
    config_baseline['stages']['use_discolike'] = False
    config_baseline['stages']['use_ocean'] = False
    test_configs.append(("Baseline (No B2B Enrichment)", config_baseline))

    # 2. Discolike only
    if base_config['api_keys'].get('discolike'):
        config_discolike = base_config.copy()
        config_discolike['stages']['use_discolike'] = True
        config_discolike['stages']['use_ocean'] = False
        test_configs.append(("Discolike Only", config_discolike))

    # 3. Ocean only
    if base_config['api_keys'].get('ocean'):
        config_ocean = base_config.copy()
        config_ocean['stages']['use_discolike'] = False
        config_ocean['stages']['use_ocean'] = True
        test_configs.append(("Ocean Only", config_ocean))

    # 4. Both enabled (waterfall - Discolike then Ocean)
    if base_config['api_keys'].get('discolike') and base_config['api_keys'].get('ocean'):
        config_both = base_config.copy()
        config_both['stages']['use_discolike'] = True
        config_both['stages']['use_ocean'] = True
        test_configs.append(("Both (Discolike → Ocean)", config_both))

    # Run all test configurations
    results = {}

    for config_name, config in test_configs:
        df_results, duration = await run_test_configuration(config, companies, config_name)

        # Calculate metrics
        metrics = calculate_metrics(df_results, df_truth)
        metrics['duration_seconds'] = duration
        metrics['companies_per_second'] = len(companies) / duration if duration > 0 else 0

        results[config_name] = {
            'metrics': metrics,
            'results_df': df_results,
            'duration': duration
        }

        # Save individual results
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        safe_name = config_name.replace(' ', '_').replace('(', '').replace(')', '').replace('→', 'to')
        df_results.to_csv(f"{output_dir}/results_{safe_name}.csv", index=False)

        logger.info(f"\n✓ Saved results to: {output_dir}/results_{safe_name}.csv")

    # Generate comparison report
    generate_comparison_report(results, output_dir)

    return results


def generate_comparison_report(results: Dict[str, Any], output_dir: str):
    """Generate comprehensive comparison report"""
    logger.info(f"\n{'='*60}")
    logger.info("COMPARISON REPORT")
    logger.info(f"{'='*60}\n")

    # Comparison table
    comparison_data = []

    for config_name, result in results.items():
        metrics = result['metrics']

        comparison_data.append({
            'Configuration': config_name,
            'Accuracy': f"{metrics['accuracy']*100:.1f}%",
            'Precision': f"{metrics['precision']*100:.1f}%",
            'Recall': f"{metrics['recall']*100:.1f}%",
            'F1 Score': f"{metrics['f1_score']*100:.1f}%",
            'Coverage': f"{metrics['coverage']*100:.1f}%",
            'High Conf (≥85) Accuracy': f"{metrics['high_conf_accuracy']*100:.1f}%",
            'High Conf Count': metrics['high_conf_count'],
            'Duration (sec)': f"{metrics['duration_seconds']:.1f}",
            'Companies/sec': f"{metrics['companies_per_second']:.1f}"
        })

    df_comparison = pd.DataFrame(comparison_data)

    # Print table
    print("\n" + df_comparison.to_string(index=False))

    # Save comparison CSV
    comparison_path = f"{output_dir}/api_comparison.csv"
    df_comparison.to_csv(comparison_path, index=False)
    logger.info(f"\n✓ Comparison table saved to: {comparison_path}")

    # Generate detailed markdown report
    markdown_report = generate_markdown_report(results)
    report_path = f"{output_dir}/COMPARISON_REPORT.md"

    with open(report_path, 'w') as f:
        f.write(markdown_report)

    logger.info(f"✓ Detailed report saved to: {report_path}")

    # Determine winner
    best_config = max(results.items(), key=lambda x: x[1]['metrics']['accuracy'])
    logger.info(f"\n{'='*60}")
    logger.info(f"🏆 WINNER: {best_config[0]}")
    logger.info(f"   Accuracy: {best_config[1]['metrics']['accuracy']*100:.1f}%")
    logger.info(f"{'='*60}\n")


def generate_markdown_report(results: Dict[str, Any]) -> str:
    """Generate detailed markdown report"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    report = f"""# API Comparison Test Report
Generated: {timestamp}

## Summary

"""

    # Summary table
    report += "| Configuration | Accuracy | Precision | Recall | F1 | Coverage | High Conf Acc | Duration |\n"
    report += "|--------------|----------|-----------|--------|----|---------|--------------|---------|\n"

    for config_name, result in results.items():
        m = result['metrics']
        report += f"| {config_name} | {m['accuracy']*100:.1f}% | {m['precision']*100:.1f}% | "
        report += f"{m['recall']*100:.1f}% | {m['f1_score']*100:.1f}% | {m['coverage']*100:.1f}% | "
        report += f"{m['high_conf_accuracy']*100:.1f}% | {m['duration_seconds']:.1f}s |\n"

    report += "\n## Detailed Results\n\n"

    # Detailed breakdown for each config
    for config_name, result in results.items():
        m = result['metrics']

        report += f"### {config_name}\n\n"
        report += f"**Overall Performance:**\n"
        report += f"- Total Companies: {m['total_companies']}\n"
        report += f"- Accuracy: {m['accuracy']*100:.2f}%\n"
        report += f"- Precision: {m['precision']*100:.2f}%\n"
        report += f"- Recall: {m['recall']*100:.2f}%\n"
        report += f"- F1 Score: {m['f1_score']*100:.2f}%\n"
        report += f"- Coverage: {m['coverage']*100:.2f}%\n\n"

        report += f"**Confusion Matrix:**\n"
        report += f"- True Positives: {m['true_positives']}\n"
        report += f"- False Positives: {m['false_positives']}\n"
        report += f"- False Negatives: {m['false_negatives']}\n"
        report += f"- True Negatives: {m['true_negatives']}\n\n"

        report += f"**Confidence Calibration:**\n"
        report += f"- High Confidence (≥85): {m['high_conf_accuracy']*100:.2f}% ({m['high_conf_count']} companies)\n"
        report += f"- Medium Confidence (70-84): {m['medium_conf_accuracy']*100:.2f}% ({m['medium_conf_count']} companies)\n\n"

        if m['source_breakdown']:
            report += f"**Source Breakdown:**\n"
            for source, stats in m['source_breakdown'].items():
                report += f"- {source}: {stats['accuracy']*100:.1f}% accuracy ({stats['correct']}/{stats['count']})\n"
            report += "\n"

        report += f"**Performance:**\n"
        report += f"- Duration: {m['duration_seconds']:.1f} seconds\n"
        report += f"- Throughput: {m['companies_per_second']:.1f} companies/second\n\n"

        report += "---\n\n"

    # Recommendations
    report += "## Recommendations\n\n"

    best_accuracy = max(results.items(), key=lambda x: x[1]['metrics']['accuracy'])
    best_speed = min(results.items(), key=lambda x: x[1]['metrics']['duration_seconds'])

    report += f"- **Best Accuracy:** {best_accuracy[0]} ({best_accuracy[1]['metrics']['accuracy']*100:.1f}%)\n"
    report += f"- **Fastest:** {best_speed[0]} ({best_speed[1]['metrics']['duration_seconds']:.1f}s)\n\n"

    return report


async def main():
    """Main entry point"""
    if len(sys.argv) < 3:
        print("Usage: python compare_apis.py <test_input.csv> <ground_truth.csv> [output_dir]")
        print("Example: python compare_apis.py test/test_companies_large.csv test/ground_truth_large.csv test/results")
        sys.exit(1)

    test_input_path = sys.argv[1]
    ground_truth_path = sys.argv[2]
    output_dir = sys.argv[3] if len(sys.argv) > 3 else "test/results"

    if not Path(test_input_path).exists():
        print(f"Error: Test input file not found: {test_input_path}")
        sys.exit(1)

    if not Path(ground_truth_path).exists():
        print(f"Error: Ground truth file not found: {ground_truth_path}")
        sys.exit(1)

    # Run comparison
    results = await compare_apis(test_input_path, ground_truth_path, output_dir)

    logger.info("\n✓✓ API comparison complete!")


if __name__ == "__main__":
    asyncio.run(main())
