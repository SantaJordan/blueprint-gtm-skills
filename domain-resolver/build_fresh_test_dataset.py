#!/usr/bin/env python3
"""
Fresh Test Dataset Builder - Using Live APIs

Uses Serper Places API to find real, current companies with verified domains.
Creates high-quality test datasets with known ground truth.
"""
import asyncio
import aiohttp
import pandas as pd
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any
import yaml
import random

logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Industry definitions with search queries
INDUSTRIES = {
    'Healthcare': {
        'queries': [
            'hospital in Boston, MA',
            'medical center in Chicago, IL',
            'urgent care in Seattle, WA',
            'health clinic in Austin, TX',
            'medical group in San Diego, CA',
        ],
        'description': 'Hospitals & Medical Facilities'
    },
    'Manufacturing': {
        'queries': [
            'manufacturing company in Detroit, MI',
            'industrial manufacturer in Cleveland, OH',
            'factory in Charlotte, NC',
            'chemical company in Houston, TX',
            'aerospace manufacturing in Phoenix, AZ',
        ],
        'description': 'Industrial Manufacturing'
    },
    'Food Service': {
        'queries': [
            'restaurant in Portland, OR',
            'cafe in Nashville, TN',
            'food service in Denver, CO',
            'catering company in Miami, FL',
            'dining in Atlanta, GA',
        ],
        'description': 'Restaurants & Food Service'
    },
    'Technology': {
        'queries': [
            'software company in San Francisco, CA',
            'tech startup in New York, NY',
            'SaaS company in Austin, TX',
            'cloud services in Seattle, WA',
            'cybersecurity company in Washington, DC',
        ],
        'description': 'Software & Technology'
    },
    'Transportation': {
        'queries': [
            'trucking company in Dallas, TX',
            'logistics company in Memphis, TN',
            'freight company in Kansas City, MO',
            'delivery service in Los Angeles, CA',
            'shipping company in Baltimore, MD',
        ],
        'description': 'Transportation & Logistics'
    }
}


async def search_serper_places(query: str, api_key: str,
                               session: aiohttp.ClientSession,
                               num_results: int = 20) -> List[Dict[str, Any]]:
    """
    Search for places using Serper Places API

    Args:
        query: Search query (e.g., "hospital in Boston, MA")
        api_key: Serper API key
        session: aiohttp session
        num_results: Number of results to return

    Returns:
        List of company data dicts with verified domains
    """
    url = "https://google.serper.dev/places"

    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }

    payload = {
        'q': query,
        'num': num_results
    }

    try:
        async with session.post(url, json=payload, headers=headers) as response:
            if response.status != 200:
                logger.error(f"Serper API error {response.status} for query: {query}")
                return []

            data = await response.json()
            places = data.get('places', [])

            # Extract relevant fields
            companies = []
            for place in places:
                # Only include if we have a website
                if 'website' in place and place['website']:
                    company = {
                        'name': place.get('title', ''),
                        'domain': clean_domain(place.get('website', '')),
                        'address': place.get('address', ''),
                        'phone': place.get('phoneNumber', ''),
                        'city': extract_city(place.get('address', '')),
                        'rating': place.get('rating', 0),
                        'reviews': place.get('reviews', 0),
                        'category': place.get('category', ''),
                    }

                    # Only add if we have minimum required fields
                    if company['name'] and company['domain'] and company['city']:
                        companies.append(company)

            logger.info(f"  Found {len(companies)} companies with websites for: {query}")
            return companies

    except Exception as e:
        logger.error(f"Error searching Serper: {e}")
        return []


def clean_domain(url: str) -> str:
    """Clean domain from URL"""
    if not url:
        return ''

    # Remove protocol
    domain = url.replace('https://', '').replace('http://', '')

    # Remove www.
    domain = domain.replace('www.', '')

    # Remove trailing slash and path
    domain = domain.split('/')[0]

    # Remove port
    domain = domain.split(':')[0]

    return domain.lower().strip()


def extract_city(address: str) -> str:
    """Extract city from full address"""
    if not address:
        return ''

    # Common format: "Street, City, State ZIP"
    parts = address.split(',')
    if len(parts) >= 2:
        # City is typically the second-to-last part
        city = parts[-2].strip() if len(parts) >= 2 else parts[0].strip()
        # Remove state abbreviation if it's in the city part
        city = ' '.join([w for w in city.split() if not (len(w) == 2 and w.isupper())])
        return city.strip()

    return address.split(',')[0].strip()


async def build_fresh_dataset(api_key: str, companies_per_industry: int = 10) -> tuple:
    """
    Build fresh test dataset using Serper Places API

    Args:
        api_key: Serper API key
        companies_per_industry: Number of companies to collect per industry

    Returns:
        Tuple of (test_input DataFrame, ground_truth DataFrame)
    """
    logger.info(f"\n{'='*60}")
    logger.info("BUILDING FRESH TEST DATASET FROM LIVE DATA")
    logger.info(f"{'='*60}\n")

    all_companies = []

    async with aiohttp.ClientSession() as session:
        for industry_name, industry_config in INDUSTRIES.items():
            logger.info(f"\n{industry_name}: {industry_config['description']}")
            logger.info(f"Collecting companies...")

            industry_companies = []

            # Search multiple queries for diversity
            for query in industry_config['queries']:
                companies = await search_serper_places(
                    query=query,
                    api_key=api_key,
                    session=session,
                    num_results=20
                )
                industry_companies.extend(companies)

                # Add delay to respect rate limits
                await asyncio.sleep(0.5)

            # Remove duplicates (by domain)
            seen_domains = set()
            unique_companies = []
            for company in industry_companies:
                if company['domain'] not in seen_domains:
                    seen_domains.add(company['domain'])
                    company['test_industry'] = industry_name
                    unique_companies.append(company)

            # Sample requested number
            if len(unique_companies) > companies_per_industry:
                sampled = random.sample(unique_companies, companies_per_industry)
            else:
                sampled = unique_companies

            logger.info(f"  ✓ Collected {len(sampled)} unique companies")
            all_companies.extend(sampled)

    # Convert to DataFrame
    df = pd.DataFrame(all_companies)

    logger.info(f"\n{'='*60}")
    logger.info(f"Total companies collected: {len(df)}")
    logger.info(f"{'='*60}\n")

    # Show distribution
    logger.info("Distribution by industry:")
    for industry, count in df['test_industry'].value_counts().items():
        logger.info(f"  {industry}: {count}")

    # Create ground truth (name + expected domain)
    ground_truth = df[['name', 'domain']].copy()
    ground_truth.columns = ['name', 'expected_domain']

    # Create test input (without domains)
    test_input = df[[
        'name',
        'city',
        'phone',
        'test_industry'
    ]].copy()

    test_input.columns = ['name', 'city', 'phone', 'context']

    # Add additional context
    test_input['context'] = df.apply(
        lambda row: f"{row['test_industry']} {row['category']}".strip(),
        axis=1
    )

    return test_input, ground_truth


async def main():
    """Main entry point"""
    # Load config for API key
    config_path = "config.yaml"
    if not Path(config_path).exists():
        print(f"Error: {config_path} not found")
        sys.exit(1)

    with open(config_path) as f:
        config = yaml.safe_load(f)

    serper_key = config['api_keys']['serper']

    # Get companies per industry from command line (default: 10)
    companies_per_industry = int(sys.argv[1]) if len(sys.argv) > 1 else 10

    # Build dataset
    test_input, ground_truth = await build_fresh_dataset(
        api_key=serper_key,
        companies_per_industry=companies_per_industry
    )

    # Save files
    Path("test").mkdir(exist_ok=True)

    test_input_path = "test/test_companies_fresh.csv"
    ground_truth_path = "test/ground_truth_fresh.csv"

    test_input.to_csv(test_input_path, index=False)
    ground_truth.to_csv(ground_truth_path, index=False)

    logger.info(f"\n{'='*60}")
    logger.info("SAVED DATASETS")
    logger.info(f"{'='*60}")
    logger.info(f"✓ Test input (no domains): {test_input_path}")
    logger.info(f"✓ Ground truth (with domains): {ground_truth_path}")
    logger.info(f"\nNext steps:")
    logger.info(f"  1. Run: python domain_resolver.py {test_input_path}")
    logger.info(f"  2. Validate: python analyze_by_industry.py <results> {ground_truth_path} {test_input_path}")
    logger.info(f"\n✓✓ Fresh dataset generation complete!")


if __name__ == "__main__":
    asyncio.run(main())
