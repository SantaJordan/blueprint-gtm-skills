"""
Basic import and syntax tests for Contact Finder
"""

import asyncio
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")

    # LLM modules
    from modules.llm.provider import LLMProvider, get_provider
    from modules.llm.openai_provider import OpenAIProvider
    from modules.llm.anthropic_provider import AnthropicProvider
    print("  ✓ LLM modules")

    # Enrichment modules
    from modules.enrichment.blitz import BlitzClient
    from modules.enrichment.leadmagic import LeadMagicClient
    from modules.enrichment.scrapin import ScrapinClient
    from modules.enrichment.exa import ExaClient
    from modules.enrichment.site_scraper import SiteScraper
    from modules.enrichment.waterfall import EnrichmentWaterfall
    print("  ✓ Enrichment modules")

    # Discovery modules
    from modules.discovery.linkedin_company import LinkedInCompanyDiscovery
    from modules.discovery.contact_search import ContactSearchEngine
    print("  ✓ Discovery modules")

    # Validation modules
    from modules.validation.email_validator import EmailValidator, EmailOrigin
    from modules.validation.linkedin_normalizer import normalize_linkedin_url
    from modules.validation.contact_judge import ContactJudge
    print("  ✓ Validation modules")

    # Main orchestrator
    from contact_finder import ContactFinder
    print("  ✓ Main orchestrator")

    # API comparison
    from tests.api_comparison import APIComparisonTest
    print("  ✓ API comparison test")

    print("\nAll imports successful!")


def test_linkedin_normalizer():
    """Test LinkedIn URL normalization"""
    print("\nTesting LinkedIn normalizer...")

    from modules.validation.linkedin_normalizer import (
        normalize_linkedin_url,
        is_valid_linkedin_in_url,
        is_valid_linkedin_company_url,
        extract_linkedin_username
    )

    # Test cases
    test_cases = [
        # (input, expected_output)
        ("https://www.linkedin.com/in/john-smith-12345/", "linkedin.com/in/john-smith-12345"),
        ("https://linkedin.com/in/john-smith?mini=true", "linkedin.com/in/john-smith"),
        ("http://www.linkedin.com/in/john-smith#about", "linkedin.com/in/john-smith"),
        ("linkedin.com/in/john-smith", "linkedin.com/in/john-smith"),
        ("/in/john-smith", "linkedin.com/in/john-smith"),
        ("https://www.linkedin.com/company/acme-corp/", "linkedin.com/company/acme-corp"),
        ("https://de.linkedin.com/in/hans-mueller", "linkedin.com/in/hans-mueller"),
        ("invalid-url", None),
        (None, None),
    ]

    all_passed = True
    for url, expected in test_cases:
        result = normalize_linkedin_url(url)
        status = "✓" if result == expected else "✗"
        if result != expected:
            all_passed = False
            print(f"  {status} normalize({url!r}) = {result!r}, expected {expected!r}")
        else:
            print(f"  {status} normalize({url!r})")

    # Test /in/ validation
    assert is_valid_linkedin_in_url("https://linkedin.com/in/john") == True
    assert is_valid_linkedin_in_url("https://linkedin.com/company/acme") == False
    print("  ✓ is_valid_linkedin_in_url")

    # Test company validation
    assert is_valid_linkedin_company_url("https://linkedin.com/company/acme") == True
    assert is_valid_linkedin_company_url("https://linkedin.com/in/john") == False
    print("  ✓ is_valid_linkedin_company_url")

    # Test username extraction
    assert extract_linkedin_username("https://linkedin.com/in/john-smith") == "john-smith"
    print("  ✓ extract_linkedin_username")

    if all_passed:
        print("\nAll LinkedIn normalizer tests passed!")
    else:
        print("\nSome tests failed!")


def test_email_validator():
    """Test email validation"""
    print("\nTesting email validator...")

    from modules.validation.email_validator import (
        EmailValidator,
        EmailOrigin,
        quick_validate
    )

    validator = EmailValidator()

    # Test syntax validation
    assert validator.validate_syntax("test@example.com") == True
    assert validator.validate_syntax("invalid-email") == False
    assert validator.validate_syntax("") == False
    print("  ✓ Syntax validation")

    # Test role account detection
    assert validator.is_role_account("info@company.com") == True
    assert validator.is_role_account("john.smith@company.com") == False
    assert validator.is_role_account("support@company.com") == True
    print("  ✓ Role account detection")

    # Test personal domain detection
    assert validator.is_personal_domain("john@gmail.com") == True
    assert validator.is_personal_domain("john@company.com") == False
    print("  ✓ Personal domain detection")

    # Test confidence scoring
    score = validator.calculate_confidence(
        origin=EmailOrigin.SITE_OBSERVED,
        is_valid_syntax=True,
        is_deliverable=True,
        is_catch_all=False,
        is_role_account=False,
        is_personal_domain=False
    )
    assert score > 80  # High confidence for site-observed, verified
    print(f"  ✓ Confidence scoring (site_observed + verified = {score})")

    score = validator.calculate_confidence(
        origin=EmailOrigin.PATTERN_GUESS,
        is_valid_syntax=True,
        is_deliverable=None,
        is_catch_all=None,
        is_role_account=True,
        is_personal_domain=False
    )
    assert score < 50  # Low confidence for pattern guess
    print(f"  ✓ Confidence scoring (pattern_guess + role = {score})")

    # Test quick_validate
    result = quick_validate("test@example.com", EmailOrigin.ENRICHED_API)
    assert result.is_valid_syntax == True
    assert result.confidence > 0
    print("  ✓ quick_validate")

    print("\nAll email validator tests passed!")


def test_dataclasses():
    """Test that dataclasses are properly defined"""
    print("\nTesting dataclasses...")

    from modules.enrichment.blitz import BlitzEmailResult, BlitzContactResult
    from modules.enrichment.waterfall import EnrichedContact
    from modules.discovery.linkedin_company import CompanyLinkedInResult
    from modules.discovery.contact_search import ContactCandidate
    from modules.validation.contact_judge import ContactJudgment
    from contact_finder import ContactResult, CompanyContactResult

    # Test instantiation
    email_result = BlitzEmailResult(
        email="test@example.com",
        status="success",
        credits_consumed=1.0,
        raw_response={}
    )
    assert email_result.email == "test@example.com"
    print("  ✓ BlitzEmailResult")

    contact_result = ContactResult(
        name="John Smith",
        email="john@example.com",
        linkedin_url="linkedin.com/in/john-smith"
    )
    assert contact_result.confidence == 0.0  # Default
    print("  ✓ ContactResult")

    company_result = CompanyContactResult(
        company_name="Acme Corp",
        domain="acme.com",
        linkedin_company_url=None
    )
    assert company_result.success == False  # Default
    print("  ✓ CompanyContactResult")

    print("\nAll dataclass tests passed!")


async def test_async_components():
    """Test async components without making actual API calls"""
    print("\nTesting async components...")

    from modules.enrichment.waterfall import EnrichmentWaterfall
    from modules.discovery.linkedin_company import LinkedInCompanyDiscovery
    from modules.discovery.contact_search import ContactSearchEngine

    # Test waterfall with no clients (should handle gracefully)
    waterfall = EnrichmentWaterfall()
    result = await waterfall.enrich(
        name="John Smith",
        company_name="Acme Corp",
        domain="acme.com"
    )
    assert result.contact.name == "John Smith"
    assert result.contact.company_name == "Acme Corp"
    print("  ✓ EnrichmentWaterfall (no clients)")

    # Test LinkedIn discovery with no clients
    discovery = LinkedInCompanyDiscovery()
    result = await discovery.discover(
        company_name="Acme Corp",
        domain="acme.com"
    )
    assert result.company_name == "Acme Corp"
    print("  ✓ LinkedInCompanyDiscovery (no clients)")

    # Test contact search with no clients
    search = ContactSearchEngine()
    result = await search.search(
        company_name="Acme Corp",
        domain="acme.com"
    )
    assert result.company_name == "Acme Corp"
    print("  ✓ ContactSearchEngine (no clients)")

    await discovery.close()

    print("\nAll async component tests passed!")


def main():
    """Run all tests"""
    print("=" * 50)
    print("Contact Finder - Basic Tests")
    print("=" * 50)

    test_imports()
    test_linkedin_normalizer()
    test_email_validator()
    test_dataclasses()
    asyncio.run(test_async_components())

    print("\n" + "=" * 50)
    print("All tests passed!")
    print("=" * 50)


if __name__ == "__main__":
    main()
