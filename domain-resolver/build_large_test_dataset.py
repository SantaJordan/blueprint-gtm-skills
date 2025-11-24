#!/usr/bin/env python3
"""
Large Test Dataset Builder - 1000+ Companies
Expands coverage across more cities, industries, and company types
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


# Expanded industry definitions with many more search queries
EXPANDED_INDUSTRIES = {
    'Healthcare': {
        'queries': [
            # Hospitals
            'hospital in Boston, MA', 'hospital in New York, NY', 'hospital in Los Angeles, CA',
            'hospital in Houston, TX', 'hospital in Philadelphia, PA', 'hospital in Phoenix, AZ',
            # Medical Centers
            'medical center in Chicago, IL', 'medical center in Dallas, TX', 'medical center in San Jose, CA',
            'medical center in Columbus, OH', 'medical center in Indianapolis, IN',
            # Clinics
            'health clinic in Austin, TX', 'health clinic in Seattle, WA', 'health clinic in Denver, CO',
            'health clinic in Portland, OR', 'health clinic in Atlanta, GA',
            # Urgent Care
            'urgent care in San Diego, CA', 'urgent care in San Francisco, CA', 'urgent care in Miami, FL',
            'urgent care in Las Vegas, NV', 'urgent care in Nashville, TN',
            # Medical Groups
            'medical group in Minneapolis, MN', 'medical group in Detroit, MI', 'medical group in Baltimore, MD',
            'medical practice in Raleigh, NC', 'medical practice in Tampa, FL',
        ],
        'description': 'Healthcare Providers'
    },
    'Manufacturing': {
        'queries': [
            # Manufacturing
            'manufacturing company in Detroit, MI', 'manufacturing company in Cleveland, OH',
            'manufacturing company in Milwaukee, WI', 'manufacturing company in Pittsburgh, PA',
            'manufacturing company in Buffalo, NY', 'manufacturing company in Cincinnati, OH',
            # Factories
            'factory in Charlotte, NC', 'factory in Indianapolis, IN', 'factory in Columbus, OH',
            'factory in Louisville, KY', 'factory in Nashville, TN',
            # Industrial
            'industrial manufacturer in Houston, TX', 'industrial manufacturer in Chicago, IL',
            'industrial company in Atlanta, GA', 'industrial company in Phoenix, AZ',
            # Specialized
            'chemical company in Baton Rouge, LA', 'chemical company in St Louis, MO',
            'aerospace manufacturing in Seattle, WA', 'aerospace manufacturing in Wichita, KS',
            'automotive manufacturer in Detroit, MI', 'automotive supplier in Grand Rapids, MI',
            'electronics manufacturing in San Jose, CA', 'electronics manufacturing in Austin, TX',
        ],
        'description': 'Manufacturing & Industrial'
    },
    'Food Service': {
        'queries': [
            # Restaurants
            'restaurant in Portland, OR', 'restaurant in San Francisco, CA', 'restaurant in Chicago, IL',
            'restaurant in New Orleans, LA', 'restaurant in Charleston, SC', 'restaurant in Boulder, CO',
            'restaurant in Asheville, NC', 'restaurant in Providence, RI', 'restaurant in Savannah, GA',
            # Cafes
            'cafe in Seattle, WA', 'cafe in Nashville, TN', 'cafe in Austin, TX',
            'cafe in Denver, CO', 'cafe in Minneapolis, MN', 'cafe in Madison, WI',
            # Food Service
            'food service in Miami, FL', 'food service in Los Angeles, CA', 'food service in Phoenix, AZ',
            # Catering
            'catering company in Boston, MA', 'catering company in San Diego, CA',
            'catering company in Philadelphia, PA', 'catering company in Dallas, TX',
            # Dining
            'dining in Atlanta, GA', 'dining in Tampa, FL', 'dining in Orlando, FL',
        ],
        'description': 'Restaurants & Food Service'
    },
    'Technology': {
        'queries': [
            # Software
            'software company in San Francisco, CA', 'software company in Seattle, WA',
            'software company in Austin, TX', 'software company in Boston, MA',
            'software company in New York, NY', 'software company in Raleigh, NC',
            'software company in San Diego, CA', 'software company in Denver, CO',
            # SaaS
            'SaaS company in Palo Alto, CA', 'SaaS company in Mountain View, CA',
            'SaaS company in Chicago, IL', 'SaaS company in Atlanta, GA',
            # Tech Services
            'cloud services in Redmond, WA', 'cloud services in San Jose, CA',
            'IT consulting in Washington, DC', 'IT consulting in Dallas, TX',
            # Security
            'cybersecurity company in Arlington, VA', 'cybersecurity company in Austin, TX',
            'cybersecurity company in San Francisco, CA', 'cybersecurity company in Boston, MA',
            # Tech Startups
            'tech startup in Boulder, CO', 'tech startup in Portland, OR',
            'tech startup in Pittsburgh, PA', 'tech startup in Madison, WI',
        ],
        'description': 'Software & Technology'
    },
    'Transportation': {
        'queries': [
            # Trucking
            'trucking company in Dallas, TX', 'trucking company in Atlanta, GA',
            'trucking company in Kansas City, MO', 'trucking company in Indianapolis, IN',
            'trucking company in Chicago, IL', 'trucking company in Nashville, TN',
            # Logistics
            'logistics company in Memphis, TN', 'logistics company in Houston, TX',
            'logistics company in Los Angeles, CA', 'logistics company in Newark, NJ',
            'logistics company in Charlotte, NC', 'logistics company in Columbus, OH',
            # Freight
            'freight company in Kansas City, MO', 'freight company in Long Beach, CA',
            'freight company in Savannah, GA', 'freight company in Oakland, CA',
            # Delivery
            'delivery service in Miami, FL', 'delivery service in San Francisco, CA',
            'delivery service in Boston, MA', 'delivery service in Phoenix, AZ',
        ],
        'description': 'Transportation & Logistics'
    },
    'Professional Services': {
        'queries': [
            # Legal
            'law firm in New York, NY', 'law firm in Los Angeles, CA', 'law firm in Chicago, IL',
            'law firm in Houston, TX', 'law firm in San Francisco, CA', 'law firm in Washington, DC',
            # Accounting
            'accounting firm in Boston, MA', 'accounting firm in Dallas, TX',
            'accounting firm in Seattle, WA', 'accounting firm in Atlanta, GA',
            # Consulting
            'consulting firm in New York, NY', 'consulting firm in San Francisco, CA',
            'consulting firm in Chicago, IL', 'consulting firm in Boston, MA',
            # Marketing
            'marketing agency in Austin, TX', 'marketing agency in Portland, OR',
            'marketing agency in Denver, CO', 'marketing agency in Nashville, TN',
        ],
        'description': 'Professional Services'
    },
    'Retail': {
        'queries': [
            # General Retail
            'retail store in Seattle, WA', 'retail store in Denver, CO', 'retail store in Portland, OR',
            'retail store in Minneapolis, MN', 'retail store in Nashville, TN',
            # Specialty
            'specialty store in San Francisco, CA', 'specialty store in Austin, TX',
            'specialty store in Charleston, SC', 'specialty store in Savannah, GA',
            # Shopping
            'shopping center in Miami, FL', 'shopping center in Phoenix, AZ',
            'shopping center in Las Vegas, NV', 'shopping center in Orlando, FL',
        ],
        'description': 'Retail & Shopping'
    },
    'Construction': {
        'queries': [
            # General Construction
            'construction company in Dallas, TX', 'construction company in Phoenix, AZ',
            'construction company in Atlanta, GA', 'construction company in Denver, CO',
            'construction company in Charlotte, NC', 'construction company in Austin, TX',
            # Contractors
            'general contractor in Houston, TX', 'general contractor in Las Vegas, NV',
            'general contractor in Tampa, FL', 'general contractor in Nashville, TN',
            # Builders
            'home builder in Raleigh, NC', 'home builder in Orlando, FL',
            'commercial builder in Seattle, WA', 'commercial builder in Portland, OR',
        ],
        'description': 'Construction & Contracting'
    }
}


async def search_serper_places(query: str, api_key: str,
                               session: aiohttp.ClientSession,
                               num_results: int = 20) -> List[Dict[str, Any]]:
    """Search for places using Serper Places API"""
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

            companies = []
            for place in places:
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

                    if company['name'] and company['domain'] and company['city']:
                        companies.append(company)

            logger.debug(f"  Found {len(companies)} companies with websites for: {query}")
            return companies

    except Exception as e:
        logger.error(f"Error searching Serper: {e}")
        return []


def clean_domain(url: str) -> str:
    """Clean domain from URL"""
    if not url:
        return ''

    domain = url.replace('https://', '').replace('http://', '')
    domain = domain.replace('www.', '')
    domain = domain.split('/')[0]
    domain = domain.split(':')[0]

    return domain.lower().strip()


def extract_city(address: str) -> str:
    """Extract city from full address"""
    if not address:
        return ''

    parts = address.split(',')
    if len(parts) >= 2:
        city = parts[-2].strip() if len(parts) >= 2 else parts[0].strip()
        city = ' '.join([w for w in city.split() if not (len(w) == 2 and w.isupper())])
        return city.strip()

    return address.split(',')[0].strip()


async def build_large_dataset(api_key: str, target_companies: int = 1000) -> tuple:
    """
    Build large test dataset targeting 1000+ companies

    Args:
        api_key: Serper API key
        target_companies: Target number of companies (default: 1000)

    Returns:
        Tuple of (test_input DataFrame, ground_truth DataFrame)
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"BUILDING LARGE TEST DATASET - TARGET: {target_companies} COMPANIES")
    logger.info(f"{'='*60}\n")

    all_companies = []
    seen_domains = set()

    async with aiohttp.ClientSession() as session:
        for industry_name, industry_config in EXPANDED_INDUSTRIES.items():
            logger.info(f"\n{industry_name}: {industry_config['description']}")
            logger.info(f"Searching {len(industry_config['queries'])} locations...")

            # Process all queries for this industry
            for i, query in enumerate(industry_config['queries'], 1):
                companies = await search_serper_places(
                    query=query,
                    api_key=api_key,
                    session=session,
                    num_results=20
                )

                # Add unique companies
                new_companies = 0
                for company in companies:
                    if company['domain'] not in seen_domains:
                        seen_domains.add(company['domain'])
                        company['test_industry'] = industry_name
                        all_companies.append(company)
                        new_companies += 1

                if (i % 5) == 0:  # Progress update every 5 queries
                    logger.info(f"  Progress: {i}/{len(industry_config['queries'])} queries, {len(all_companies)} total unique companies")

                # Add delay to respect rate limits
                await asyncio.sleep(0.3)

            logger.info(f"  ✓ {industry_name}: {len([c for c in all_companies if c['test_industry'] == industry_name])} companies")

            # Stop if we've reached our target
            if len(all_companies) >= target_companies:
                logger.info(f"\n✓ Reached target of {target_companies} companies!")
                break

    # Convert to DataFrame
    df = pd.DataFrame(all_companies)

    logger.info(f"\n{'='*60}")
    logger.info(f"Total unique companies collected: {len(df)}")
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

    # Get target from command line (default: 1000)
    target_companies = int(sys.argv[1]) if len(sys.argv) > 1 else 1000

    # Build dataset
    test_input, ground_truth = await build_large_dataset(
        api_key=serper_key,
        target_companies=target_companies
    )

    # Save files
    Path("test").mkdir(exist_ok=True)

    test_input_path = "test/test_companies_large.csv"
    ground_truth_path = "test/ground_truth_large.csv"

    test_input.to_csv(test_input_path, index=False)
    ground_truth.to_csv(ground_truth_path, index=False)

    logger.info(f"\n{'='*60}")
    logger.info("SAVED DATASETS")
    logger.info(f"{'='*60}")
    logger.info(f"✓ Test input (no domains): {test_input_path}")
    logger.info(f"✓ Ground truth (with domains): {ground_truth_path}")
    logger.info(f"\nNext steps:")
    logger.info(f"  1. Run: python domain_resolver.py {test_input_path}")
    logger.info(f"  2. Validate with test/compare_apis.py")
    logger.info(f"\n✓✓ Large dataset generation complete!")


if __name__ == "__main__":
    asyncio.run(main())
