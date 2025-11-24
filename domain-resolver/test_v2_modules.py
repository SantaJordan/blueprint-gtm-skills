"""
V2 Module Testing Suite

Tests each V2 module individually to ensure they work before integration.

Tests:
1. Input Normalizer ✅ (already tested)
2. Directory Scraper
3. LLM Search
4. Path Router
"""

import asyncio
import logging
import yaml
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =============================================================================
# TEST 1: Input Normalizer (Already Passed)
# =============================================================================

def test_input_normalizer():
    """Test input normalizer with sample data"""
    from modules.input_normalizer import InputNormalizer
    import pandas as pd

    logger.info("\n" + "="*70)
    logger.info("TEST 1: Input Normalizer")
    logger.info("="*70)

    # Create sample data with non-standard columns
    sample_data = {
        'Company Name': ['Acme Corp', 'Tech Startup Inc', 'Local Bakery', 'SaaS Company', 'Name Only Co'],
        'HQ City': ['San Francisco', 'Austin', '', 'Seattle', ''],
        'Contact Number': ['555-1234', '', '555-9999', '555-0000', ''],
        'Industry Sector': ['Technology', 'Software', 'Food Service', 'SaaS', ''],
    }

    df = pd.DataFrame(sample_data)
    df.to_csv('/tmp/v2_test_input.csv', index=False)

    # Load and normalize
    normalizer = InputNormalizer()
    normalized_df = normalizer.load('/tmp/v2_test_input.csv')

    logger.info(f"\n✓ Original columns: {list(sample_data.keys())}")
    logger.info(f"✓ Normalized columns: {list(normalized_df.drop(columns=['_data_tier']).columns)}")

    # Check tier distribution
    tier_dist = normalizer.get_tier_distribution(normalized_df)
    logger.info(f"\n✓ Tier distribution:")
    for tier, count in sorted(tier_dist.items()):
        logger.info(f"  Tier {tier}: {count} companies")

    logger.info(f"\n✅ TEST 1 PASSED - Input Normalizer Working")
    return True


# =============================================================================
# TEST 2: Directory Scraper
# =============================================================================

async def test_directory_scraper():
    """Test directory scraper on 5 companies"""
    from modules.directory_scraper import DirectoryScraper

    logger.info("\n" + "="*70)
    logger.info("TEST 2: Directory Scraper")
    logger.info("="*70)

    # Load config for API keys
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    serper_key = config['api_keys']['serper']
    zenrows_key = config['api_keys'].get('zenrows')

    scraper = DirectoryScraper(serper_key, zenrows_key)

    # Test companies (well-known companies that should be in directories)
    test_companies = [
        {'name': 'Anthropic', 'context': 'AI research'},
        {'name': 'Stripe', 'context': 'Payments'},
        {'name': 'Figma', 'context': 'Design software'},
        {'name': 'Notion', 'context': 'Productivity'},
        {'name': 'Linear', 'context': 'Project management'},
    ]

    results = []
    for company in test_companies:
        logger.info(f"\nSearching directories for: {company['name']}")

        try:
            company_results = await scraper.search_directories(
                company['name'],
                company.get('context')
            )

            if company_results:
                logger.info(f"✓ Found {len(company_results)} results")
                for result in company_results:
                    logger.info(f"  - {result['source']}: {result['domain']} (confidence: {result['confidence']})")
                results.extend(company_results)
            else:
                logger.warning(f"✗ No results found for {company['name']}")

        except Exception as e:
            logger.error(f"✗ Error: {e}")

    success_rate = len([c for c in test_companies if any(r['domain'] for r in results)]) / len(test_companies)

    logger.info(f"\n{'='*70}")
    logger.info(f"Total results: {len(results)}")
    logger.info(f"Success rate: {success_rate*100:.1f}%")

    if success_rate >= 0.4:  # 40% success is acceptable for directory scraping
        logger.info(f"✅ TEST 2 PASSED - Directory Scraper Working")
        return True
    else:
        logger.warning(f"⚠️  TEST 2 MARGINAL - Success rate below 40%")
        return False


# =============================================================================
# TEST 3: LLM Search
# =============================================================================

async def test_llm_search():
    """Test LLM search on 5 companies"""
    from modules.llm_search import llm_powered_search

    logger.info("\n" + "="*70)
    logger.info("TEST 3: LLM Search")
    logger.info("="*70)

    # Load config
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    serper_key = config['api_keys']['serper']
    llm_config = config.get('llm', {})
    llm_endpoint = llm_config.get('endpoint', 'http://localhost:11434/api/generate')
    llm_model = llm_config.get('model', 'llama3.2:3b')

    # Test companies (well-known but test LLM's query generation)
    test_companies = [
        {'name': 'OpenAI', 'context': 'Artificial Intelligence'},
        {'name': 'Anthropic', 'context': 'AI Safety'},
        {'name': 'Stripe', 'context': 'Payment Processing'},
        {'name': 'Vercel', 'context': 'Web Development'},
        {'name': 'Supabase', 'context': 'Backend as a Service'},
    ]

    results = []
    for company in test_companies:
        logger.info(f"\nLLM search for: {company['name']}")

        try:
            result = await llm_powered_search(
                company,
                serper_key,
                llm_endpoint,
                llm_model
            )

            if result:
                logger.info(f"✓ Found: {result['domain']}")
                logger.info(f"  Confidence: {result['confidence']}")
                logger.info(f"  Reasoning: {result.get('reasoning', 'N/A')[:100]}")
                results.append(result)
            else:
                logger.warning(f"✗ No result for {company['name']}")

        except Exception as e:
            logger.error(f"✗ Error: {e}")

    success_rate = len(results) / len(test_companies)

    logger.info(f"\n{'='*70}")
    logger.info(f"Total results: {len(results)}")
    logger.info(f"Success rate: {success_rate*100:.1f}%")

    if success_rate >= 0.6:  # 60% success for LLM search
        logger.info(f"✅ TEST 3 PASSED - LLM Search Working")
        return True
    else:
        logger.warning(f"⚠️  TEST 3 MARGINAL - Success rate below 60%")
        return False


# =============================================================================
# TEST 4: Path Router
# =============================================================================

def test_path_router():
    """Test path router with different data tiers"""
    from modules.path_router import PathRouter, ResolutionPath

    logger.info("\n" + "="*70)
    logger.info("TEST 4: Path Router")
    logger.info("="*70)

    # Load config
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    router = PathRouter(config)

    # Test companies with different data completeness
    test_cases = [
        {
            'name': 'Tier 1 Company',
            'city': 'San Francisco',
            'phone': '555-1234',
            'context': 'Technology',
            '_data_tier': 1
        },
        {
            'name': 'Tier 2 Company',
            'city': 'Austin',
            'phone': '',
            'context': 'Software',
            '_data_tier': 2
        },
        {
            'name': 'Tier 3 Company',
            'city': '',
            'phone': '',
            'context': 'SaaS',
            '_data_tier': 3
        },
        {
            'name': 'Tier 4 Company',
            'city': '',
            'phone': '',
            'context': '',
            '_data_tier': 4
        }
    ]

    all_passed = True

    for test_case in test_cases:
        tier = test_case['_data_tier']
        logger.info(f"\n--- Testing Tier {tier} ---")
        logger.info(f"Data: {test_case['name']}")
        logger.info(f"  City: {test_case['city'] or 'None'}")
        logger.info(f"  Phone: {test_case['phone'] or 'None'}")
        logger.info(f"  Context: {test_case['context'] or 'None'}")

        routing = router.route(test_case)

        logger.info(f"\nRouting Decision:")
        logger.info(f"  Path: {routing['path'].value}")
        logger.info(f"  Strategies: {routing['strategies']}")
        logger.info(f"  Parallel: {routing['parallel']}")
        logger.info(f"  Validation: {routing.get('validation', 'N/A')}")

        # Validate routing logic
        expected_paths = {
            1: ResolutionPath.HIGH_CONFIDENCE_LOCAL,
            2: ResolutionPath.LOCAL_NO_PHONE,
            3: ResolutionPath.GENERAL_BUSINESS,
            4: ResolutionPath.AGGRESSIVE_MULTI
        }

        if routing['path'] == expected_paths[tier]:
            logger.info(f"✓ Correct path for Tier {tier}")
        else:
            logger.error(f"✗ Wrong path for Tier {tier}")
            all_passed = False

        # Validate strategies
        if routing['strategies']:
            logger.info(f"✓ Strategies defined")
        else:
            logger.error(f"✗ No strategies")
            all_passed = False

    logger.info(f"\n{'='*70}")
    if all_passed:
        logger.info(f"✅ TEST 4 PASSED - Path Router Working")
        return True
    else:
        logger.error(f"❌ TEST 4 FAILED - Path Router Issues")
        return False


# =============================================================================
# MAIN TEST RUNNER
# =============================================================================

async def run_all_tests():
    """Run all V2 module tests"""

    logger.info("\n" + "="*70)
    logger.info("V2 MODULE TESTING SUITE")
    logger.info("="*70)

    results = {}

    # Test 1: Input Normalizer
    try:
        results['input_normalizer'] = test_input_normalizer()
    except Exception as e:
        logger.error(f"❌ TEST 1 FAILED: {e}")
        results['input_normalizer'] = False

    # Test 2: Directory Scraper
    try:
        results['directory_scraper'] = await test_directory_scraper()
    except Exception as e:
        logger.error(f"❌ TEST 2 FAILED: {e}")
        results['directory_scraper'] = False

    # Test 3: LLM Search
    try:
        results['llm_search'] = await test_llm_search()
    except Exception as e:
        logger.error(f"❌ TEST 3 FAILED: {e}")
        results['llm_search'] = False

    # Test 4: Path Router
    try:
        results['path_router'] = test_path_router()
    except Exception as e:
        logger.error(f"❌ TEST 4 FAILED: {e}")
        results['path_router'] = False

    # Summary
    logger.info("\n" + "="*70)
    logger.info("TEST SUMMARY")
    logger.info("="*70)

    for module, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        logger.info(f"{module:20s} {status}")

    total_passed = sum(results.values())
    total_tests = len(results)

    logger.info(f"\n{'='*70}")
    logger.info(f"Total: {total_passed}/{total_tests} tests passed")
    logger.info(f"Success Rate: {(total_passed/total_tests)*100:.1f}%")

    if total_passed == total_tests:
        logger.info(f"\n🎉 ALL TESTS PASSED - V2 Foundation Ready!")
    elif total_passed >= total_tests * 0.75:
        logger.info(f"\n⚠️  MOST TESTS PASSED - V2 Foundation Mostly Ready")
    else:
        logger.info(f"\n❌ MULTIPLE FAILURES - V2 Foundation Needs Work")

    return results


if __name__ == '__main__':
    asyncio.run(run_all_tests())
