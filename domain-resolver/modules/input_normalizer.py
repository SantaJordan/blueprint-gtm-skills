"""
Input Normalizer - Flexible Input Handling for Domain Resolver V2

Handles any spreadsheet format (CSV, Excel, JSON, TSV) and intelligently maps
column names to expected fields using fuzzy matching.

Features:
- Multi-format support: CSV, XLSX, JSON, TSV
- Fuzzy column name matching
- Data completeness classification (Tier 1-4)
- Validation and error handling
"""

import pandas as pd
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from rapidfuzz import fuzz
import logging

logger = logging.getLogger(__name__)


class InputNormalizer:
    """Normalizes diverse input formats into standardized company data"""

    # Expected field names and their fuzzy match patterns
    FIELD_PATTERNS = {
        'name': [
            'name', 'company', 'company_name', 'business', 'business_name',
            'organization', 'org', 'company name', 'business name'
        ],
        'city': [
            'city', 'location', 'headquarters', 'hq', 'hq_city', 'municipality',
            'town', 'metro', 'metro_area', 'locality', 'hq city'
        ],
        'phone': [
            'phone', 'telephone', 'tel', 'contact', 'contact_number', 'phone_number',
            'contact number', 'phone number', 'tel number', 'mobile'
        ],
        'address': [
            'address', 'street', 'street_address', 'location', 'full_address',
            'street address', 'mailing address', 'physical address'
        ],
        'context': [
            'context', 'industry', 'sector', 'category', 'vertical', 'description',
            'business_type', 'industry sector', 'field', 'domain'
        ],
        'website': [
            'website', 'domain', 'url', 'web', 'site', 'homepage', 'web_address',
            'company website', 'domain name', 'web site'
        ]
    }

    FUZZY_THRESHOLD = 80  # Minimum fuzzy match score for column mapping

    def __init__(self, require_name_only: bool = True):
        """
        Initialize normalizer

        Args:
            require_name_only: Only require 'name' field, all others optional
        """
        self.require_name_only = require_name_only

    def load(self, file_path: str) -> pd.DataFrame:
        """
        Load data from any supported format

        Args:
            file_path: Path to input file (CSV, Excel, JSON, TSV)

        Returns:
            Normalized DataFrame with standard column names

        Raises:
            ValueError: If format is unsupported or required fields missing
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Input file not found: {file_path}")

        logger.info(f"Loading input file: {file_path}")

        # Load based on file extension
        df = self._load_file(file_path)

        logger.info(f"✓ Loaded {len(df)} rows from {file_path.suffix} file")
        logger.info(f"  Original columns: {list(df.columns)}")

        # Map columns to standard names
        df = self._normalize_columns(df)

        logger.info(f"  Mapped columns: {list(df.columns)}")

        # Validate required fields
        self._validate(df)

        # Classify data completeness for each row
        df['_data_tier'] = df.apply(self._classify_tier, axis=1)

        # Log tier distribution
        tier_counts = df['_data_tier'].value_counts().sort_index()
        logger.info(f"\nData completeness tiers:")
        for tier, count in tier_counts.items():
            pct = (count / len(df)) * 100
            logger.info(f"  Tier {tier}: {count} rows ({pct:.1f}%)")

        return df

    def _load_file(self, file_path: Path) -> pd.DataFrame:
        """Load file based on extension"""
        ext = file_path.suffix.lower()

        try:
            if ext == '.csv':
                # Try different encodings and delimiters
                for encoding in ['utf-8', 'latin1', 'cp1252']:
                    try:
                        return pd.read_csv(file_path, encoding=encoding)
                    except UnicodeDecodeError:
                        continue
                raise ValueError(f"Unable to decode CSV file: {file_path}")

            elif ext == '.tsv':
                return pd.read_csv(file_path, sep='\t')

            elif ext in ['.xlsx', '.xls']:
                return pd.read_excel(file_path)

            elif ext == '.json':
                # Handle both array of objects and records format
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return pd.DataFrame(data)
                    elif isinstance(data, dict):
                        # Try to extract records
                        if 'records' in data:
                            return pd.DataFrame(data['records'])
                        elif 'data' in data:
                            return pd.DataFrame(data['data'])
                        else:
                            # Assume it's a single record
                            return pd.DataFrame([data])
                    else:
                        raise ValueError(f"Unsupported JSON structure: {type(data)}")

            else:
                raise ValueError(f"Unsupported file format: {ext}")

        except Exception as e:
            logger.error(f"Error loading file: {e}")
            raise

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Map original column names to standard field names using fuzzy matching

        Args:
            df: Input DataFrame with arbitrary column names

        Returns:
            DataFrame with standardized column names
        """
        column_mapping = {}
        used_columns = set()

        # For each expected field, find best matching column
        for field, patterns in self.FIELD_PATTERNS.items():
            best_col = None
            best_score = 0

            for col in df.columns:
                # Skip already mapped columns
                if col in used_columns:
                    continue

                # Check against all pattern variations
                col_lower = str(col).lower().strip()
                for pattern in patterns:
                    score = fuzz.ratio(col_lower, pattern.lower())
                    if score > best_score and score >= self.FUZZY_THRESHOLD:
                        best_score = score
                        best_col = col

            if best_col:
                column_mapping[best_col] = field
                used_columns.add(best_col)
                logger.debug(f"  Mapped '{best_col}' → '{field}' (score: {best_score})")

        # Rename columns
        df_normalized = df.rename(columns=column_mapping)

        # Ensure all expected fields exist (fill with empty strings if missing)
        for field in ['name', 'city', 'phone', 'address', 'context', 'website']:
            if field not in df_normalized.columns:
                df_normalized[field] = ''
                logger.debug(f"  Added missing field: {field}")

        # Keep only standard columns (drop unmapped columns)
        standard_cols = ['name', 'city', 'phone', 'address', 'context', 'website']
        df_normalized = df_normalized[standard_cols]

        # Fill NaN with empty strings
        df_normalized = df_normalized.fillna('')

        return df_normalized

    def _validate(self, df: pd.DataFrame) -> None:
        """
        Validate that required fields are present

        Args:
            df: Normalized DataFrame

        Raises:
            ValueError: If required fields are missing
        """
        required = ['name'] if self.require_name_only else ['name', 'city']

        missing = [field for field in required if field not in df.columns]
        if missing:
            raise ValueError(f"Required fields missing: {missing}")

        # Check if name column has any non-empty values
        if df['name'].str.strip().eq('').all():
            raise ValueError("'name' column contains no valid values")

        logger.info(f"✓ Validation passed (required: {required})")

    def _classify_tier(self, row: pd.Series) -> int:
        """
        Classify data completeness into tiers

        Tier 1: name + city + phone (High Confidence Path)
        Tier 2: name + city (Local Business Path)
        Tier 3: name + context (General Business Path)
        Tier 4: name only (Aggressive Multi-Source Path)

        Args:
            row: DataFrame row

        Returns:
            Tier number (1-4)
        """
        has_name = bool(str(row.get('name', '')).strip())
        has_city = bool(str(row.get('city', '')).strip())
        has_phone = bool(str(row.get('phone', '')).strip())
        has_context = bool(str(row.get('context', '')).strip())

        if has_name and has_city and has_phone:
            return 1  # Optimal: 90-95% expected accuracy
        elif has_name and has_city:
            return 2  # Good: 65-80% expected accuracy
        elif has_name and has_context:
            return 3  # Challenging: 50-70% expected accuracy
        elif has_name:
            return 4  # Very challenging: 30-50% expected accuracy
        else:
            return 5  # Invalid: No name

    def get_tier_distribution(self, df: pd.DataFrame) -> Dict[int, int]:
        """
        Get count of records in each data tier

        Args:
            df: Normalized DataFrame (must have _data_tier column)

        Returns:
            Dict mapping tier number to count
        """
        if '_data_tier' not in df.columns:
            raise ValueError("DataFrame missing _data_tier column. Run load() first.")

        return df['_data_tier'].value_counts().to_dict()

    def filter_by_tier(self, df: pd.DataFrame, tier: int) -> pd.DataFrame:
        """
        Filter DataFrame to only rows of a specific tier

        Args:
            df: Normalized DataFrame
            tier: Tier number (1-4)

        Returns:
            Filtered DataFrame
        """
        if '_data_tier' not in df.columns:
            raise ValueError("DataFrame missing _data_tier column. Run load() first.")

        return df[df['_data_tier'] == tier].copy()

    def to_dict_list(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Convert normalized DataFrame to list of dicts (for resolver input)

        Args:
            df: Normalized DataFrame

        Returns:
            List of company dicts
        """
        # Drop internal columns (starting with _)
        df_clean = df.drop(columns=[col for col in df.columns if col.startswith('_')])
        return df_clean.to_dict('records')


def demo():
    """Demo usage of InputNormalizer"""

    # Example: Create a sample CSV with non-standard columns
    sample_data = {
        'Company Name': ['Acme Corp', 'Tech Startup Inc', 'Local Bakery'],
        'HQ City': ['San Francisco', 'Austin', ''],
        'Contact Number': ['555-1234', '', '555-9999'],
        'Industry Sector': ['Technology', 'Software', 'Food Service'],
        'Business Address': ['123 Main St', '456 Tech Blvd', '789 Baker St']
    }

    df = pd.DataFrame(sample_data)
    df.to_csv('/tmp/sample_input.csv', index=False)

    # Load and normalize
    normalizer = InputNormalizer()
    normalized_df = normalizer.load('/tmp/sample_input.csv')

    print("\n" + "="*60)
    print("INPUT NORMALIZER DEMO")
    print("="*60)
    print(f"\nOriginal columns: {list(sample_data.keys())}")
    print(f"Normalized columns: {list(normalized_df.columns)}")
    print(f"\nTier distribution: {normalizer.get_tier_distribution(normalized_df)}")
    print(f"\nNormalized data:")
    print(normalized_df.to_string())

    # Convert to dict list for resolver
    companies = normalizer.to_dict_list(normalized_df)
    print(f"\nDicts for resolver: {len(companies)} companies")
    print(f"Example: {companies[0]}")


if __name__ == '__main__':
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(message)s'
    )

    demo()
