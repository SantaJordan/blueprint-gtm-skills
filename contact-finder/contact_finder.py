"""
Contact Finder - Main Orchestrator
Find and enrich contacts at companies using multiple sources

5-Stage Pipeline:
1. Input Validation
2. LinkedIn Company Discovery
3. Contact Discovery (parallel sources)
4. Enrichment Waterfall
5. LLM Validation

Usage:
    finder = ContactFinder.from_config("config.yaml")
    result = await finder.find_contacts("Acme Corp", "acme.com")

    # Or batch processing with checkpoints
    results = await finder.process_batch(companies, checkpoint_every=100)
"""

import asyncio
import json
import os
import yaml
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

# Internal modules
from modules.llm.provider import get_provider, LLMProvider
from modules.enrichment.blitz import BlitzClient
from modules.enrichment.leadmagic import LeadMagicClient
from modules.enrichment.scrapin import ScrapinClient
from modules.enrichment.exa import ExaClient
from modules.enrichment.site_scraper import SiteScraper
from modules.enrichment.waterfall import EnrichmentWaterfall, EnrichedContact
from modules.discovery.linkedin_company import LinkedInCompanyDiscovery
from modules.discovery.contact_search import ContactSearchEngine, ContactCandidate
from modules.validation.contact_judge import ContactJudge, ContactJudgment, create_evidence_bundle
from modules.validation.email_validator import EmailValidator, EmailOrigin
from modules.validation.linkedin_normalizer import normalize_linkedin_url


@dataclass
class ContactResult:
    """Final output for a single contact"""
    # Required fields
    name: str | None
    email: str | None
    linkedin_url: str | None  # linkedin.com/in/xxx format ONLY

    # Optional fields
    first_name: str | None = None
    last_name: str | None = None
    title: str | None = None
    phone: str | None = None

    # Confidence and reasoning (Truck Day style)
    confidence: float = 0.0
    email_confidence: float = 0.0
    person_match_confidence: float = 0.0
    linkedin_confidence: float = 0.0
    reasoning: str = ""
    red_flags: list[str] = field(default_factory=list)

    # Metadata
    email_verified: bool | None = None
    email_origin: str | None = None
    is_catch_all: bool | None = None
    sources: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    cost_credits: float = 0.0


@dataclass
class CompanyContactResult:
    """Result for a company"""
    company_name: str
    domain: str | None
    linkedin_company_url: str | None

    # Contacts found
    contacts: list[ContactResult] = field(default_factory=list)
    best_contact: ContactResult | None = None

    # Processing metadata
    success: bool = False
    stage_reached: str = "input"  # input, linkedin, search, enrich, validate
    processing_time_ms: float = 0.0
    total_cost_credits: float = 0.0
    errors: list[str] = field(default_factory=list)

    # Search metadata
    candidates_found: int = 0
    candidates_enriched: int = 0
    candidates_validated: int = 0


@dataclass
class BatchResult:
    """Result of batch processing"""
    total_companies: int
    successful: int
    failed: int
    results: list[CompanyContactResult] = field(default_factory=list)
    total_cost_credits: float = 0.0
    processing_time_seconds: float = 0.0
    checkpoint_file: str | None = None


class ContactFinder:
    """
    Main orchestrator for contact finding.

    Cost-optimized pipeline that finds contacts at companies
    using multiple sources in parallel, with LLM validation.
    """

    def __init__(
        self,
        config: dict,
        llm_provider: LLMProvider | None = None,
        blitz_client: BlitzClient | None = None,
        leadmagic_client: LeadMagicClient | None = None,
        scrapin_client: ScrapinClient | None = None,
        exa_client: ExaClient | None = None,
        site_scraper: SiteScraper | None = None
    ):
        self.config = config
        self.llm = llm_provider

        # API clients
        self.blitz = blitz_client
        self.leadmagic = leadmagic_client
        self.scrapin = scrapin_client
        self.exa = exa_client
        self.site_scraper = site_scraper

        # Pipeline components (initialized lazily)
        self._linkedin_discovery: LinkedInCompanyDiscovery | None = None
        self._contact_search: ContactSearchEngine | None = None
        self._enrichment: EnrichmentWaterfall | None = None
        self._judge: ContactJudge | None = None
        self._email_validator: EmailValidator | None = None

        # Settings
        self.target_titles = config.get("target_titles", [
            "Owner", "CEO", "President", "Founder",
            "General Manager", "Manager", "Director"
        ])
        self.max_contacts_per_company = config.get("max_contacts_per_company", 3)
        self.include_phone = config.get("include_phone", False)
        self.min_confidence = config.get("min_confidence", 50)
        self.use_llm_judge = config.get("use_llm_judge", True)

    @classmethod
    def from_config(cls, config_path: str = "config.yaml") -> "ContactFinder":
        """Create ContactFinder from config file"""
        with open(config_path) as f:
            config = yaml.safe_load(f)

        api_keys = config.get("api_keys", {})

        # Initialize LLM provider
        llm_config = config.get("llm", {})
        llm_provider = get_provider(llm_config) if llm_config else None

        # Initialize API clients
        blitz_client = None
        blitz_keys = api_keys.get("blitz", {})
        if blitz_keys:
            # Use first available key
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

        site_scraper = SiteScraper(
            zenrows_api_key=api_keys.get("zenrows"),
            max_pages=config.get("scraping", {}).get("max_pages", 5)
        )

        return cls(
            config=config,
            llm_provider=llm_provider,
            blitz_client=blitz_client,
            leadmagic_client=leadmagic_client,
            scrapin_client=scrapin_client,
            exa_client=exa_client,
            site_scraper=site_scraper
        )

    def _get_linkedin_discovery(self) -> LinkedInCompanyDiscovery:
        """Get or create LinkedIn discovery component"""
        if not self._linkedin_discovery:
            self._linkedin_discovery = LinkedInCompanyDiscovery(
                serper_api_key=self.config.get("api_keys", {}).get("serper"),
                scrapin_client=self.scrapin,
                exa_client=self.exa
            )
        return self._linkedin_discovery

    def _get_contact_search(self) -> ContactSearchEngine:
        """Get or create contact search component"""
        if not self._contact_search:
            self._contact_search = ContactSearchEngine(
                scrapin_client=self.scrapin,
                exa_client=self.exa,
                blitz_client=self.blitz,
                site_scraper=self.site_scraper,
                target_titles=self.target_titles
            )
        return self._contact_search

    def _get_enrichment(self) -> EnrichmentWaterfall:
        """Get or create enrichment component"""
        if not self._enrichment:
            self._enrichment = EnrichmentWaterfall(
                scrapin_client=self.scrapin,
                blitz_client=self.blitz,
                leadmagic_client=self.leadmagic,
                email_validator=self._get_email_validator()
            )
        return self._enrichment

    def _get_judge(self) -> ContactJudge | None:
        """Get or create LLM judge component"""
        if not self._judge and self.llm and self.use_llm_judge:
            self._judge = ContactJudge(self.llm)
        return self._judge

    def _get_email_validator(self) -> EmailValidator:
        """Get or create email validator"""
        if not self._email_validator:
            self._email_validator = EmailValidator(blitz_client=self.blitz)
        return self._email_validator

    async def find_contacts(
        self,
        company_name: str,
        domain: str | None = None,
        location: str | None = None,
        industry: str | None = None,
        target_titles: list[str] | None = None
    ) -> CompanyContactResult:
        """
        Find contacts at a company.

        This is the main entry point for single-company contact finding.

        Args:
            company_name: Company name
            domain: Company domain (highly recommended)
            location: Company location (optional, helps disambiguation)
            industry: Industry (optional, helps title matching)
            target_titles: Override default target titles

        Returns:
            CompanyContactResult with all found contacts
        """
        start_time = datetime.now()
        titles = target_titles or self.target_titles

        result = CompanyContactResult(
            company_name=company_name,
            domain=domain,
            linkedin_company_url=None
        )

        try:
            # Stage 1: Input validation
            result.stage_reached = "input"
            if not company_name:
                result.errors.append("Company name is required")
                return result

            # Stage 2: LinkedIn Company Discovery
            result.stage_reached = "linkedin"
            linkedin_discovery = self._get_linkedin_discovery()
            linkedin_result = await linkedin_discovery.discover(
                company_name=company_name,
                domain=domain,
                location=location
            )
            result.linkedin_company_url = linkedin_result.linkedin_url

            # Stage 3: Contact Discovery (parallel sources)
            result.stage_reached = "search"
            contact_search = self._get_contact_search()
            contact_search.target_titles = titles

            search_result = await contact_search.search(
                company_name=company_name,
                domain=domain,
                linkedin_company_url=linkedin_result.linkedin_url,
                location=location
            )
            result.candidates_found = len(search_result.candidates)

            if not search_result.candidates:
                result.errors.append("No contact candidates found")
                result.success = False
                return result

            # Stage 4: Enrichment Waterfall
            result.stage_reached = "enrich"
            enrichment = self._get_enrichment()

            # Enrich top candidates
            candidates_to_enrich = search_result.candidates[:self.max_contacts_per_company * 2]
            enriched_results = await enrichment.batch_enrich(
                contacts=[{
                    "name": c.name,
                    "first_name": c.first_name,
                    "last_name": c.last_name,
                    "title": c.title,
                    "email": c.email,
                    "linkedin_url": c.linkedin_url,
                    "evidence": c.evidence
                } for c in candidates_to_enrich],
                company_name=company_name,
                domain=domain,
                include_phone=self.include_phone
            )

            result.candidates_enriched = len([r for r in enriched_results if r.success])

            # Stage 5: LLM Validation
            result.stage_reached = "validate"
            judge = self._get_judge()

            validated_contacts = []
            for enriched in enriched_results:
                if not enriched.success:
                    continue

                contact = enriched.contact
                result.total_cost_credits += contact.cost_credits

                # Create evidence bundle for judge
                evidence = create_evidence_bundle([
                    {"source": src, "content": ev}
                    for src, ev in zip(contact.enrichment_sources, contact.evidence)
                ])

                # LLM validation
                judgment = None
                if judge:
                    judgment = await judge.validate_contact(
                        company_name=company_name,
                        domain=domain or "",
                        domain_confidence=linkedin_result.confidence,
                        contact_name=contact.name,
                        contact_title=contact.title,
                        contact_email=contact.email,
                        email_source=contact.email_origin.value if contact.email_origin else None,
                        email_verified=contact.email_verified,
                        is_catch_all=contact.is_catch_all,
                        linkedin_url=contact.linkedin_url,
                        phone=contact.phone,
                        evidence=evidence,
                        target_titles=titles,
                        industry=industry,
                        location=location
                    )

                # Build final contact result
                contact_result = ContactResult(
                    name=contact.name,
                    email=contact.email,
                    linkedin_url=contact.linkedin_url,
                    first_name=contact.first_name,
                    last_name=contact.last_name,
                    title=contact.title,
                    phone=contact.phone,
                    confidence=judgment.overall_confidence if judgment else contact.confidence,
                    email_confidence=judgment.email_confidence if judgment else (80 if contact.email_verified else 50),
                    person_match_confidence=judgment.person_match_confidence if judgment else contact.confidence,
                    linkedin_confidence=judgment.linkedin_confidence if judgment else (80 if contact.linkedin_url else 0),
                    reasoning=judgment.reasoning if judgment else "No LLM validation",
                    red_flags=judgment.red_flags if judgment else [],
                    email_verified=contact.email_verified,
                    email_origin=contact.email_origin.value if contact.email_origin else None,
                    is_catch_all=contact.is_catch_all,
                    sources=contact.enrichment_sources,
                    evidence=contact.evidence,
                    cost_credits=contact.cost_credits
                )

                # Apply minimum confidence filter
                if contact_result.confidence >= self.min_confidence:
                    if not judgment or judgment.accept:
                        validated_contacts.append(contact_result)
                        result.candidates_validated += 1

            # Sort by confidence and take top N
            validated_contacts.sort(key=lambda x: x.confidence, reverse=True)
            result.contacts = validated_contacts[:self.max_contacts_per_company]
            result.best_contact = result.contacts[0] if result.contacts else None
            result.success = bool(result.contacts)

        except Exception as e:
            result.errors.append(f"Pipeline error: {str(e)}")
            result.success = False

        # Calculate processing time
        result.processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000

        return result

    async def process_batch(
        self,
        companies: list[dict],
        checkpoint_every: int = 100,
        checkpoint_dir: str = "checkpoints",
        max_concurrent: int = 50,
        resume_from: str | None = None
    ) -> BatchResult:
        """
        Process a batch of companies with checkpointing.

        Args:
            companies: List of dicts with company_name, domain, etc.
            checkpoint_every: Save checkpoint every N companies
            checkpoint_dir: Directory for checkpoint files
            max_concurrent: Max concurrent company lookups
            resume_from: Checkpoint file to resume from

        Returns:
            BatchResult with all results
        """
        start_time = datetime.now()

        # Create checkpoint directory
        Path(checkpoint_dir).mkdir(parents=True, exist_ok=True)

        # Resume from checkpoint if specified
        processed_indices = set()
        results = []
        if resume_from and os.path.exists(resume_from):
            with open(resume_from) as f:
                checkpoint_data = json.load(f)
                results = [CompanyContactResult(**r) for r in checkpoint_data.get("results", [])]
                processed_indices = set(checkpoint_data.get("processed_indices", []))

        # Semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_one(idx: int, company: dict) -> CompanyContactResult | None:
            if idx in processed_indices:
                return None

            async with semaphore:
                return await self.find_contacts(
                    company_name=company.get("company_name", ""),
                    domain=company.get("domain"),
                    location=company.get("location"),
                    industry=company.get("industry"),
                    target_titles=company.get("target_titles")
                )

        # Process in batches for checkpointing
        checkpoint_file = None
        for batch_start in range(0, len(companies), checkpoint_every):
            batch_end = min(batch_start + checkpoint_every, len(companies))
            batch = companies[batch_start:batch_end]

            # Create tasks for this batch
            tasks = [
                process_one(batch_start + i, company)
                for i, company in enumerate(batch)
            ]

            # Run batch
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Collect results
            for i, result in enumerate(batch_results):
                idx = batch_start + i
                if result is None:
                    continue  # Already processed
                if isinstance(result, Exception):
                    results.append(CompanyContactResult(
                        company_name=companies[idx].get("company_name", ""),
                        domain=companies[idx].get("domain"),
                        linkedin_company_url=None,
                        success=False,
                        errors=[str(result)]
                    ))
                else:
                    results.append(result)
                processed_indices.add(idx)

            # Save checkpoint
            checkpoint_file = f"{checkpoint_dir}/checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(checkpoint_file, "w") as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "processed_indices": list(processed_indices),
                    "results": [asdict(r) for r in results]
                }, f, default=str)

        # Calculate final stats
        successful = sum(1 for r in results if r.success)
        total_cost = sum(r.total_cost_credits for r in results)
        processing_time = (datetime.now() - start_time).total_seconds()

        return BatchResult(
            total_companies=len(companies),
            successful=successful,
            failed=len(companies) - successful,
            results=results,
            total_cost_credits=total_cost,
            processing_time_seconds=processing_time,
            checkpoint_file=checkpoint_file
        )

    async def close(self):
        """Close all API client sessions"""
        if self._linkedin_discovery:
            await self._linkedin_discovery.close()
        if self.site_scraper:
            await self.site_scraper.close()
        if self.blitz:
            await self.blitz.close()
        if self.leadmagic:
            await self.leadmagic.close()
        if self.scrapin:
            await self.scrapin.close()
        if self.exa:
            await self.exa.close()


# CLI entry point
async def main():
    """CLI entry point for testing"""
    import argparse

    parser = argparse.ArgumentParser(description="Contact Finder")
    parser.add_argument("--company", "-c", help="Company name")
    parser.add_argument("--domain", "-d", help="Company domain")
    parser.add_argument("--config", default="config.yaml", help="Config file path")
    parser.add_argument("--batch", "-b", help="Batch input file (JSON/CSV)")
    parser.add_argument("--output", "-o", help="Output file")

    args = parser.parse_args()

    finder = ContactFinder.from_config(args.config)

    try:
        if args.batch:
            # Batch processing
            with open(args.batch) as f:
                if args.batch.endswith(".json"):
                    companies = json.load(f)
                else:
                    # CSV
                    import csv
                    reader = csv.DictReader(f)
                    companies = list(reader)

            result = await finder.process_batch(companies)
            print(f"Processed {result.total_companies} companies")
            print(f"Successful: {result.successful}, Failed: {result.failed}")
            print(f"Total cost: {result.total_cost_credits} credits")

            if args.output:
                with open(args.output, "w") as f:
                    json.dump(asdict(result), f, indent=2, default=str)

        elif args.company:
            # Single company
            result = await finder.find_contacts(
                company_name=args.company,
                domain=args.domain
            )

            print(f"\nCompany: {result.company_name}")
            print(f"Domain: {result.domain}")
            print(f"LinkedIn: {result.linkedin_company_url}")
            print(f"Success: {result.success}")
            print(f"Stage reached: {result.stage_reached}")

            if result.contacts:
                print(f"\nFound {len(result.contacts)} contacts:")
                for c in result.contacts:
                    print(f"\n  Name: {c.name}")
                    print(f"  Title: {c.title}")
                    print(f"  Email: {c.email} (verified: {c.email_verified})")
                    print(f"  LinkedIn: {c.linkedin_url}")
                    print(f"  Confidence: {c.confidence:.0f}")
                    print(f"  Reasoning: {c.reasoning}")
                    if c.red_flags:
                        print(f"  Red flags: {c.red_flags}")

            if result.errors:
                print(f"\nErrors: {result.errors}")

            if args.output:
                with open(args.output, "w") as f:
                    json.dump(asdict(result), f, indent=2, default=str)

        else:
            parser.print_help()

    finally:
        await finder.close()


if __name__ == "__main__":
    asyncio.run(main())
