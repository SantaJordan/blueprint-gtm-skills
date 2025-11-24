#!/usr/bin/env python3
"""
Test Dataset Builder - People Data Labs Approach

Downloads and filters companies from People Data Labs free dataset
Creates test datasets across 5 diverse industries
"""
import pandas as pd
import sys
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Industry definitions with keywords
INDUSTRIES = {
    'Healthcare': {
        'keywords': ['hospital', 'medical center', 'urgent care', 'clinic', 'healthcare',
                    'health system', 'medical', 'physician', 'surgery center'],
        'naics_codes': ['622', '621'],  # Hospitals, Ambulatory Healthcare
        'description': 'Hospitals & Medical Facilities - Heavily regulated, patient-focused, CMS oversight'
    },
    'Manufacturing': {
        'keywords': ['chemical', 'manufacturing', 'industrial', 'fabrication', 'factory',
                    'production', 'assembly', 'metal', 'plastic', 'machinery'],
        'naics_codes': ['325', '332', '333'],  # Chemical, Fabricated Metal, Machinery
        'description': 'Chemical/Industrial Manufacturing - Physical production, EPA/OSHA oversight'
    },
    'Food Service': {
        'keywords': ['restaurant', 'food service', 'catering', 'dining', 'cafe',
                    'fast food', 'quick service', 'hospitality', 'culinary'],
        'naics_codes': ['722'],  # Food Services
        'description': 'Restaurants/QSR - Consumer-facing, local health inspections'
    },
    'Technology': {
        'keywords': ['software', 'saas', 'cloud', 'technology', 'platform',
                    'it services', 'data', 'analytics', 'cybersecurity', 'ai'],
        'naics_codes': ['511', '518'],  # Software Publishers, Cloud Computing
        'description': 'SaaS/Software - Zero regulatory footprint, subscription model'
    },
    'Transportation': {
        'keywords': ['trucking', 'logistics', 'freight', 'transportation', 'shipping',
                    'delivery', 'courier', 'warehousing', 'distribution'],
        'naics_codes': ['484', '493'],  # Truck Transportation, Warehousing
        'description': 'Trucking/Logistics - DOT regulated, fleet operations, FMCSA compliance'
    }
}


def load_pdl_dataset(csv_path: str) -> pd.DataFrame:
    """
    Load People Data Labs dataset

    Args:
        csv_path: Path to companies CSV file

    Returns:
        DataFrame with company data
    """
    logger.info(f"Loading dataset from: {csv_path}")

    try:
        df = pd.read_csv(csv_path)
        logger.info(f"✓ Loaded {len(df):,} companies")
        return df
    except FileNotFoundError:
        logger.error(f"Dataset not found: {csv_path}")
        logger.info("\nPlease download the People Data Labs dataset:")
        logger.info("1. Visit: https://www.kaggle.com/datasets/peopledatalabssf/free-7-million-company-dataset")
        logger.info("2. Download companies_sorted.csv")
        logger.info("3. Place in this directory or specify path")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error loading dataset: {e}")
        sys.exit(1)


def filter_by_industry(df: pd.DataFrame, industry_name: str,
                      keywords: list, sample_size: int = 50) -> pd.DataFrame:
    """
    Filter companies by industry keywords

    Args:
        df: Full companies DataFrame
        industry_name: Industry name for tracking
        keywords: List of keywords to match
        sample_size: Number of companies to sample

    Returns:
        Filtered DataFrame
    """
    logger.info(f"\nFiltering {industry_name}...")

    # Create keyword pattern
    pattern = '|'.join(keywords)

    # Filter by industry field (case-insensitive)
    industry_df = df[df['industry'].str.contains(pattern, case=False, na=False)]

    logger.info(f"  Found {len(industry_df):,} companies matching keywords")

    # Additional filters for quality
    industry_df = industry_df[
        (industry_df['domain'].notna()) &  # Must have domain
        (industry_df['country'] == 'united states') &  # US only for consistency
        (industry_df['locality'].notna())  # Must have city
    ]

    logger.info(f"  After quality filters: {len(industry_df):,} companies")

    if len(industry_df) == 0:
        logger.warning(f"  ⚠️ No companies found for {industry_name}")
        return pd.DataFrame()

    # Sample companies
    sample = industry_df.sample(min(sample_size, len(industry_df)), random_state=42)

    logger.info(f"  ✓ Sampled {len(sample)} companies")

    # Add industry label
    sample = sample.copy()
    sample['test_industry'] = industry_name

    return sample


def build_test_dataset(df: pd.DataFrame, companies_per_industry: int = 50) -> tuple:
    """
    Build test dataset across 5 diverse industries

    Args:
        df: Full companies DataFrame
        companies_per_industry: Number of companies to sample per industry

    Returns:
        (test_input_df, ground_truth_df) tuple
    """
    logger.info("\n" + "="*60)
    logger.info("BUILDING DIVERSE TEST DATASET")
    logger.info("="*60)

    all_samples = []

    for industry_name, industry_config in INDUSTRIES.items():
        logger.info(f"\n{industry_name}: {industry_config['description']}")

        sample = filter_by_industry(
            df,
            industry_name,
            industry_config['keywords'],
            companies_per_industry
        )

        if len(sample) > 0:
            all_samples.append(sample)

    if not all_samples:
        logger.error("No samples collected! Check dataset and keywords.")
        sys.exit(1)

    # Combine all samples
    test_dataset = pd.concat(all_samples, ignore_index=True)

    logger.info("\n" + "="*60)
    logger.info(f"Total companies: {len(test_dataset)}")
    logger.info("="*60)

    # Show distribution
    logger.info("\nDistribution by industry:")
    for industry, count in test_dataset['test_industry'].value_counts().items():
        logger.info(f"  {industry}: {count}")

    # Create ground truth (name + expected domain)
    ground_truth = test_dataset[['name', 'domain']].copy()
    ground_truth.columns = ['name', 'expected_domain']

    # Clean domains (remove http://, www., etc.)
    ground_truth['expected_domain'] = ground_truth['expected_domain'].apply(clean_domain)

    # Create test input (without domains)
    test_input = test_dataset[[
        'name',
        'locality',
        'size range',
        'test_industry'
    ]].copy()

    test_input.columns = ['name', 'city', 'size', 'context']

    # Convert size to context string
    test_input['context'] = test_input.apply(
        lambda row: f"{row['context']} {row['size'] if pd.notna(row['size']) else ''}".strip(),
        axis=1
    )

    test_input = test_input[['name', 'city', 'context']]

    return test_input, ground_truth


def clean_domain(url: str) -> str:
    """Clean domain from URL"""
    if pd.isna(url):
        return ''

    url = str(url).lower().strip()

    # Remove protocol
    url = url.replace('http://', '').replace('https://', '')

    # Remove www.
    url = url.replace('www.', '')

    # Remove trailing slash and path
    url = url.split('/')[0]

    # Remove query params
    url = url.split('?')[0]

    return url


def save_datasets(test_input: pd.DataFrame, ground_truth: pd.DataFrame, output_dir: str = "test"):
    """Save test datasets"""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    test_input_file = output_path / "test_companies_diverse.csv"
    ground_truth_file = output_path / "ground_truth_diverse.csv"

    test_input.to_csv(test_input_file, index=False)
    ground_truth.to_csv(ground_truth_file, index=False)

    logger.info("\n" + "="*60)
    logger.info("SAVED DATASETS")
    logger.info("="*60)
    logger.info(f"✓ Test input (no domains): {test_input_file}")
    logger.info(f"✓ Ground truth (with domains): {ground_truth_file}")
    logger.info("\nNext steps:")
    logger.info(f"  1. Run: python domain_resolver.py {test_input_file}")
    logger.info(f"  2. Validate: cd test && python test_runner.py --input test_companies_diverse.csv --ground-truth ground_truth_diverse.csv")


def main():
    """Main entry point"""

    # Check for dataset path argument
    if len(sys.argv) < 2:
        print("Usage: python build_test_dataset.py <path_to_companies_csv> [companies_per_industry]")
        print("\nExample:")
        print("  python build_test_dataset.py companies_sorted.csv 50")
        print("\nDownload dataset from:")
        print("  https://www.kaggle.com/datasets/peopledatalabssf/free-7-million-company-dataset")
        sys.exit(1)

    csv_path = sys.argv[1]
    companies_per_industry = int(sys.argv[2]) if len(sys.argv) > 2 else 50

    # Load dataset
    df = load_pdl_dataset(csv_path)

    # Build test dataset
    test_input, ground_truth = build_test_dataset(df, companies_per_industry)

    # Save
    save_datasets(test_input, ground_truth)

    logger.info("\n✓✓ Dataset generation complete!")


if __name__ == "__main__":
    main()
