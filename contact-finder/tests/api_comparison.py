"""
API Comparison Test Framework
Compare different enrichment APIs to determine cost/quality tradeoffs

This test helps decide:
1. Which APIs provide best data quality
2. Cost per successful enrichment
3. Whether to keep LeadMagic subscription

Test methodology:
- Run same companies through different API combinations
- Track success rate, data completeness, cost
- Score results for quality
"""

import asyncio
import json
import csv
import os
import yaml
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.enrichment.blitz import BlitzClient
from modules.enrichment.leadmagic import LeadMagicClient
from modules.enrichment.scrapin import ScrapinClient
from modules.enrichment.exa import ExaClient
from modules.validation.email_validator import EmailValidator
from modules.validation.linkedin_normalizer import normalize_linkedin_url


@dataclass
class APITestResult:
    """Result from a single API test"""
    api_name: str
    company_name: str
    domain: str | None

    # What we found
    found_email: bool = False
    found_linkedin: bool = False
    found_phone: bool = False
    found_name: bool = False
    found_title: bool = False

    # Quality indicators
    email_verified: bool | None = None
    linkedin_valid: bool = False  # Is it a real /in/ URL

    # Cost
    credits_used: float = 0.0

    # Timing
    latency_ms: float = 0.0

    # Raw data
    raw_response: dict = field(default_factory=dict)
    error: str | None = None


@dataclass
class ComparisonResult:
    """Comparison result for one company across all APIs"""
    company_name: str
    domain: str | None
    results: dict[str, APITestResult] = field(default_factory=dict)

    # Which API "won" for each field
    best_email_source: str | None = None
    best_linkedin_source: str | None = None

    # Agreement between APIs
    email_agreement: bool = False  # Did multiple APIs find same email
    linkedin_agreement: bool = False


@dataclass
class ComparisonSummary:
    """Summary of comparison across all companies"""
    total_companies: int = 0

    # Success rates by API
    api_success_rates: dict[str, dict] = field(default_factory=dict)

    # Cost analysis
    cost_per_success: dict[str, float] = field(default_factory=dict)
    total_cost: dict[str, float] = field(default_factory=dict)

    # Quality metrics
    verified_email_rate: dict[str, float] = field(default_factory=dict)
    valid_linkedin_rate: dict[str, float] = field(default_factory=dict)

    # Agreement analysis
    email_agreement_rate: float = 0.0
    linkedin_agreement_rate: float = 0.0

    # Recommendations
    recommendations: list[str] = field(default_factory=list)


class APIComparisonTest:
    """
    Framework for comparing enrichment APIs.

    Tests each API independently on the same set of companies
    to determine quality and cost-effectiveness.
    """

    def __init__(
        self,
        blitz_client: BlitzClient | None = None,
        leadmagic_client: LeadMagicClient | None = None,
        scrapin_client: ScrapinClient | None = None,
        exa_client: ExaClient | None = None
    ):
        self.blitz = blitz_client
        self.leadmagic = leadmagic_client
        self.scrapin = scrapin_client
        self.exa = exa_client

    @classmethod
    def from_config(cls, config_path: str = "config.yaml") -> "APIComparisonTest":
        """Create from config file"""
        with open(config_path) as f:
            config = yaml.safe_load(f)

        api_keys = config.get("api_keys", {})

        blitz_client = None
        blitz_keys = api_keys.get("blitz", {})
        if blitz_keys:
            first_key = list(blitz_keys.values())[0] if isinstance(blitz_keys, dict) else blitz_keys
            blitz_client = BlitzClient(first_key)

        leadmagic_client = None
        if api_keys.get("leadmagic"):
            leadmagic_client = LeadMagicClient(api_keys["leadmagic"])

        scrapin_client = None
        if api_keys.get("scrapin"):
            scrapin_client = ScrapinClient(api_keys["scrapin"])

        exa_client = None
        if api_keys.get("exa"):
            exa_client = ExaClient(api_keys["exa"])

        return cls(
            blitz_client=blitz_client,
            leadmagic_client=leadmagic_client,
            scrapin_client=scrapin_client,
            exa_client=exa_client
        )

    async def _test_blitz_waterfall(
        self,
        company_name: str,
        domain: str | None,
        target_titles: list[str]
    ) -> APITestResult:
        """Test Blitz waterfall ICP endpoint"""
        result = APITestResult(
            api_name="blitz_waterfall",
            company_name=company_name,
            domain=domain
        )

        if not self.blitz:
            result.error = "Blitz client not configured"
            return result

        start = datetime.now()
        try:
            response = await self.blitz.waterfall_icp(
                company_name=company_name,
                domain=domain,
                job_titles=target_titles,
                max_results=1
            )

            result.latency_ms = (datetime.now() - start).total_seconds() * 1000
            result.credits_used = response.credits_used

            if response.contacts:
                contact = response.contacts[0]
                result.found_email = bool(contact.email)
                result.found_linkedin = bool(contact.linkedin_url)
                result.found_name = bool(contact.full_name)
                result.found_title = bool(contact.job_title)
                result.email_verified = contact.email_verified

                if contact.linkedin_url:
                    normalized = normalize_linkedin_url(contact.linkedin_url)
                    result.linkedin_valid = bool(normalized and "/in/" in normalized)

                result.raw_response = contact.raw_response

        except Exception as e:
            result.error = str(e)
            result.latency_ms = (datetime.now() - start).total_seconds() * 1000

        return result

    async def _test_blitz_email(
        self,
        first_name: str,
        last_name: str | None,
        domain: str | None,
        company_name: str
    ) -> APITestResult:
        """Test Blitz email enrichment endpoint"""
        result = APITestResult(
            api_name="blitz_email",
            company_name=company_name,
            domain=domain
        )

        if not self.blitz:
            result.error = "Blitz client not configured"
            return result

        start = datetime.now()
        try:
            response = await self.blitz.enrich_email(
                first_name=first_name,
                last_name=last_name,
                domain=domain,
                company_name=company_name
            )

            result.latency_ms = (datetime.now() - start).total_seconds() * 1000
            result.credits_used = 1.0  # Email enrichment is 1 credit

            result.found_email = bool(response.email)
            result.email_verified = response.email_verified
            result.found_name = bool(first_name)

            result.raw_response = response.raw_response

        except Exception as e:
            result.error = str(e)
            result.latency_ms = (datetime.now() - start).total_seconds() * 1000

        return result

    async def _test_leadmagic(
        self,
        first_name: str,
        last_name: str | None,
        domain: str | None,
        company_name: str
    ) -> APITestResult:
        """Test LeadMagic email finding"""
        result = APITestResult(
            api_name="leadmagic",
            company_name=company_name,
            domain=domain
        )

        if not self.leadmagic:
            result.error = "LeadMagic client not configured"
            return result

        start = datetime.now()
        try:
            response = await self.leadmagic.find_email(
                first_name=first_name,
                last_name=last_name,
                domain=domain,
                company_name=company_name
            )

            result.latency_ms = (datetime.now() - start).total_seconds() * 1000
            result.credits_used = 1.0 if response.email else 0.0  # Pay if found

            result.found_email = bool(response.email)
            result.email_verified = response.confidence == "high"
            result.found_name = bool(first_name)

            result.raw_response = response.raw_response

        except Exception as e:
            result.error = str(e)
            result.latency_ms = (datetime.now() - start).total_seconds() * 1000

        return result

    async def _test_scrapin_person(
        self,
        linkedin_url: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        company_name: str | None = None
    ) -> APITestResult:
        """Test Scrapin person enrichment (FREE)"""
        result = APITestResult(
            api_name="scrapin",
            company_name=company_name or "",
            domain=None
        )

        if not self.scrapin:
            result.error = "Scrapin client not configured"
            return result

        start = datetime.now()
        try:
            if linkedin_url:
                response = await self.scrapin.get_person_profile(linkedin_url)
            else:
                response = await self.scrapin.match_person(
                    first_name=first_name,
                    last_name=last_name,
                    company_name=company_name
                )

            result.latency_ms = (datetime.now() - start).total_seconds() * 1000
            result.credits_used = 0.0  # FREE

            result.found_email = bool(response.email)
            result.found_linkedin = bool(response.linkedin_url)
            result.found_name = bool(response.name)
            result.found_title = bool(response.title)

            if response.linkedin_url:
                normalized = normalize_linkedin_url(response.linkedin_url)
                result.linkedin_valid = bool(normalized and "/in/" in normalized)

            result.raw_response = response.raw_response

        except Exception as e:
            result.error = str(e)
            result.latency_ms = (datetime.now() - start).total_seconds() * 1000

        return result

    async def _test_exa_linkedin(
        self,
        name: str,
        company_name: str,
        title: str | None = None
    ) -> APITestResult:
        """Test Exa LinkedIn person search (FREE)"""
        result = APITestResult(
            api_name="exa",
            company_name=company_name,
            domain=None
        )

        if not self.exa:
            result.error = "Exa client not configured"
            return result

        start = datetime.now()
        try:
            linkedin_url = await self.exa.find_linkedin_person(
                name=name,
                company=company_name,
                title=title
            )

            result.latency_ms = (datetime.now() - start).total_seconds() * 1000
            result.credits_used = 0.0  # FREE for basic search

            result.found_linkedin = bool(linkedin_url)
            result.found_name = bool(name)

            if linkedin_url:
                normalized = normalize_linkedin_url(linkedin_url)
                result.linkedin_valid = bool(normalized and "/in/" in normalized)

            result.raw_response = {"linkedin_url": linkedin_url}

        except Exception as e:
            result.error = str(e)
            result.latency_ms = (datetime.now() - start).total_seconds() * 1000

        return result

    async def test_company(
        self,
        company_name: str,
        domain: str | None = None,
        test_person: dict | None = None,
        target_titles: list[str] | None = None
    ) -> ComparisonResult:
        """
        Test all APIs for a single company.

        Args:
            company_name: Company name
            domain: Company domain
            test_person: Optional dict with first_name, last_name, linkedin_url
                         for testing person-based enrichment
            target_titles: Target job titles for search

        Returns:
            ComparisonResult with all API results
        """
        titles = target_titles or ["Owner", "CEO", "President", "Manager"]

        comparison = ComparisonResult(
            company_name=company_name,
            domain=domain
        )

        # Test Blitz waterfall (finds contacts)
        blitz_result = await self._test_blitz_waterfall(company_name, domain, titles)
        comparison.results["blitz_waterfall"] = blitz_result

        # If we have a test person, test person-based APIs
        if test_person:
            first_name = test_person.get("first_name", "")
            last_name = test_person.get("last_name")
            linkedin_url = test_person.get("linkedin_url")

            # Test Blitz email enrichment
            if first_name and (domain or company_name):
                blitz_email = await self._test_blitz_email(
                    first_name, last_name, domain, company_name
                )
                comparison.results["blitz_email"] = blitz_email

            # Test LeadMagic
            if first_name and (domain or company_name):
                leadmagic = await self._test_leadmagic(
                    first_name, last_name, domain, company_name
                )
                comparison.results["leadmagic"] = leadmagic

            # Test Scrapin
            scrapin = await self._test_scrapin_person(
                linkedin_url=linkedin_url,
                first_name=first_name,
                last_name=last_name,
                company_name=company_name
            )
            comparison.results["scrapin"] = scrapin

            # Test Exa
            name = f"{first_name} {last_name}".strip() if last_name else first_name
            exa = await self._test_exa_linkedin(name, company_name)
            comparison.results["exa"] = exa

        # Determine winners
        email_sources = [
            (name, r) for name, r in comparison.results.items()
            if r.found_email
        ]
        if email_sources:
            # Prefer verified, then by cost
            email_sources.sort(key=lambda x: (not x[1].email_verified, x[1].credits_used))
            comparison.best_email_source = email_sources[0][0]

        linkedin_sources = [
            (name, r) for name, r in comparison.results.items()
            if r.found_linkedin and r.linkedin_valid
        ]
        if linkedin_sources:
            linkedin_sources.sort(key=lambda x: x[1].credits_used)
            comparison.best_linkedin_source = linkedin_sources[0][0]

        # Check agreement
        emails_found = [r.raw_response.get("email") for r in comparison.results.values() if r.found_email]
        comparison.email_agreement = len(set(emails_found)) == 1 and len(emails_found) > 1

        linkedin_found = [
            normalize_linkedin_url(r.raw_response.get("linkedin_url"))
            for r in comparison.results.values()
            if r.found_linkedin
        ]
        comparison.linkedin_agreement = len(set(linkedin_found)) == 1 and len(linkedin_found) > 1

        return comparison

    async def run_comparison(
        self,
        companies: list[dict],
        output_file: str = "api_comparison_results.json",
        max_concurrent: int = 10
    ) -> ComparisonSummary:
        """
        Run comparison test on multiple companies.

        Args:
            companies: List of dicts with company_name, domain, test_person
            output_file: Where to save detailed results
            max_concurrent: Max concurrent API calls

        Returns:
            ComparisonSummary with aggregated metrics
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        results = []

        async def test_one(company: dict) -> ComparisonResult:
            async with semaphore:
                return await self.test_company(
                    company_name=company.get("company_name", ""),
                    domain=company.get("domain"),
                    test_person=company.get("test_person"),
                    target_titles=company.get("target_titles")
                )

        # Run all tests
        tasks = [test_one(c) for c in companies]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        valid_results = [r for r in results if isinstance(r, ComparisonResult)]

        # Calculate summary
        summary = self._calculate_summary(valid_results)

        # Save detailed results
        with open(output_file, "w") as f:
            json.dump({
                "summary": asdict(summary),
                "results": [asdict(r) for r in valid_results],
                "timestamp": datetime.now().isoformat()
            }, f, indent=2, default=str)

        return summary

    def _calculate_summary(self, results: list[ComparisonResult]) -> ComparisonSummary:
        """Calculate summary statistics from results"""
        summary = ComparisonSummary(total_companies=len(results))

        if not results:
            return summary

        # Aggregate by API
        api_stats: dict[str, dict] = {}
        for result in results:
            for api_name, api_result in result.results.items():
                if api_name not in api_stats:
                    api_stats[api_name] = {
                        "total": 0,
                        "email_found": 0,
                        "linkedin_found": 0,
                        "email_verified": 0,
                        "linkedin_valid": 0,
                        "total_cost": 0.0,
                        "errors": 0
                    }

                stats = api_stats[api_name]
                stats["total"] += 1
                if api_result.found_email:
                    stats["email_found"] += 1
                if api_result.found_linkedin:
                    stats["linkedin_found"] += 1
                if api_result.email_verified:
                    stats["email_verified"] += 1
                if api_result.linkedin_valid:
                    stats["linkedin_valid"] += 1
                stats["total_cost"] += api_result.credits_used
                if api_result.error:
                    stats["errors"] += 1

        # Calculate rates
        for api_name, stats in api_stats.items():
            total = stats["total"]
            if total == 0:
                continue

            summary.api_success_rates[api_name] = {
                "email_rate": stats["email_found"] / total * 100,
                "linkedin_rate": stats["linkedin_found"] / total * 100,
                "error_rate": stats["errors"] / total * 100
            }

            summary.total_cost[api_name] = stats["total_cost"]

            if stats["email_found"] > 0:
                summary.cost_per_success[api_name] = stats["total_cost"] / stats["email_found"]

            if stats["email_found"] > 0:
                summary.verified_email_rate[api_name] = stats["email_verified"] / stats["email_found"] * 100

            if stats["linkedin_found"] > 0:
                summary.valid_linkedin_rate[api_name] = stats["linkedin_valid"] / stats["linkedin_found"] * 100

        # Agreement rates
        email_agreements = sum(1 for r in results if r.email_agreement)
        linkedin_agreements = sum(1 for r in results if r.linkedin_agreement)
        summary.email_agreement_rate = email_agreements / len(results) * 100
        summary.linkedin_agreement_rate = linkedin_agreements / len(results) * 100

        # Generate recommendations
        summary.recommendations = self._generate_recommendations(summary, api_stats)

        return summary

    def _generate_recommendations(
        self,
        summary: ComparisonSummary,
        api_stats: dict
    ) -> list[str]:
        """Generate recommendations based on comparison results"""
        recs = []

        # Compare Blitz vs LeadMagic
        blitz_stats = api_stats.get("blitz_email", {})
        leadmagic_stats = api_stats.get("leadmagic", {})

        if blitz_stats and leadmagic_stats:
            blitz_rate = blitz_stats.get("email_found", 0) / max(blitz_stats.get("total", 1), 1)
            leadmagic_rate = leadmagic_stats.get("email_found", 0) / max(leadmagic_stats.get("total", 1), 1)

            blitz_cost = summary.cost_per_success.get("blitz_email", float("inf"))
            leadmagic_cost = summary.cost_per_success.get("leadmagic", float("inf"))

            if blitz_rate > leadmagic_rate * 1.2:  # 20% better
                recs.append(f"Blitz email has {blitz_rate/leadmagic_rate:.1f}x better success rate than LeadMagic")
            elif leadmagic_rate > blitz_rate * 1.2:
                recs.append(f"LeadMagic has {leadmagic_rate/blitz_rate:.1f}x better success rate than Blitz email")

            if blitz_cost < leadmagic_cost * 0.8:  # 20% cheaper per success
                recs.append(f"Blitz is more cost-effective: ${blitz_cost:.2f} vs ${leadmagic_cost:.2f} per success")
            elif leadmagic_cost < blitz_cost * 0.8:
                recs.append(f"LeadMagic is more cost-effective: ${leadmagic_cost:.2f} vs ${blitz_cost:.2f} per success")

        # Check if LeadMagic is worth keeping
        if leadmagic_stats:
            leadmagic_success = leadmagic_stats.get("email_found", 0) / max(leadmagic_stats.get("total", 1), 1)
            if leadmagic_success < 0.3:  # Less than 30% success
                recs.append("CONSIDER: LeadMagic success rate is low (<30%). May not be worth the subscription.")
            elif leadmagic_success > 0.7:  # More than 70% success
                recs.append("KEEP: LeadMagic has strong success rate (>70%)")

        # Free API recommendations
        scrapin_stats = api_stats.get("scrapin", {})
        exa_stats = api_stats.get("exa", {})

        if scrapin_stats.get("linkedin_found", 0) > scrapin_stats.get("total", 1) * 0.5:
            recs.append("Scrapin (FREE) is effective for LinkedIn enrichment - prioritize it")

        if exa_stats.get("linkedin_found", 0) > exa_stats.get("total", 1) * 0.5:
            recs.append("Exa (FREE) is effective for LinkedIn discovery - prioritize it")

        # Waterfall recommendation
        blitz_waterfall = api_stats.get("blitz_waterfall", {})
        if blitz_waterfall.get("email_found", 0) > blitz_waterfall.get("total", 1) * 0.5:
            recs.append("Blitz waterfall ICP is effective as primary search method")

        return recs

    async def close(self):
        """Close all API clients"""
        if self.blitz:
            await self.blitz.close()
        if self.leadmagic:
            await self.leadmagic.close()
        if self.scrapin:
            await self.scrapin.close()
        if self.exa:
            await self.exa.close()


async def main():
    """CLI for running API comparison tests"""
    import argparse

    parser = argparse.ArgumentParser(description="API Comparison Test")
    parser.add_argument("--config", default="../config.yaml", help="Config file")
    parser.add_argument("--input", "-i", help="Input file (JSON) with test companies")
    parser.add_argument("--output", "-o", default="api_comparison_results.json", help="Output file")
    parser.add_argument("--sample", "-s", type=int, default=0, help="Run with N sample companies")

    args = parser.parse_args()

    # Sample companies for testing
    sample_companies = [
        {
            "company_name": "Acme Trucking",
            "domain": "acmetrucking.com",
            "test_person": {"first_name": "John", "last_name": "Smith"}
        },
        {
            "company_name": "Smith Plumbing",
            "domain": "smithplumbing.com",
            "test_person": {"first_name": "Mike", "last_name": "Johnson"}
        },
        {
            "company_name": "Best Dental Care",
            "domain": "bestdentalcare.com",
            "test_person": {"first_name": "Sarah", "last_name": "Williams"}
        },
    ]

    tester = APIComparisonTest.from_config(args.config)

    try:
        if args.input:
            with open(args.input) as f:
                companies = json.load(f)
        elif args.sample > 0:
            companies = sample_companies[:args.sample]
        else:
            companies = sample_companies

        print(f"Running comparison test on {len(companies)} companies...")
        summary = await tester.run_comparison(companies, args.output)

        print("\n=== API COMPARISON SUMMARY ===\n")
        print(f"Total companies tested: {summary.total_companies}")

        print("\n--- Success Rates by API ---")
        for api, rates in summary.api_success_rates.items():
            print(f"  {api}:")
            print(f"    Email: {rates.get('email_rate', 0):.1f}%")
            print(f"    LinkedIn: {rates.get('linkedin_rate', 0):.1f}%")

        print("\n--- Cost per Success ---")
        for api, cost in summary.cost_per_success.items():
            print(f"  {api}: {cost:.2f} credits")

        print("\n--- Recommendations ---")
        for rec in summary.recommendations:
            print(f"  • {rec}")

        print(f"\nDetailed results saved to: {args.output}")

    finally:
        await tester.close()


if __name__ == "__main__":
    asyncio.run(main())
