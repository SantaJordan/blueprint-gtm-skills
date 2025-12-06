"""
SMB Contact Pipeline - Data-driven pipeline for SMB owner discovery

Adapts to input data structure, uses cheap Serper queries liberally,
extracts from websites, and validates with simple rules (no LLM).
"""

import asyncio
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ..input.csv_explorer import CSVExplorer, CSVAnalysis
from ..discovery.serper_filler import SerperDataFiller
from ..discovery.website_extractor import WebsiteContactExtractor, ExtractedContact
from ..discovery.openweb_ninja import (
    OpenWebNinjaClient,
    LocalBusinessResult,
    OpenWebContactResult,
    SocialLinksResult,
)
from ..enrichment.leadmagic import LeadMagicClient, split_name
from ..validation.simple_validator import (
    SimpleContactValidator,
    ContactCandidate,
    ValidationResult,
    dict_to_candidate
)
from ..validation.contact_judge import ContactJudge, ContactJudgment, create_evidence_bundle
from ..llm.openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)


@dataclass
class ContactResult:
    """Result for a single contact"""
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    title: str | None = None
    linkedin_url: str | None = None
    sources: list[str] = field(default_factory=list)
    validation: ValidationResult | None = None


@dataclass
class CompanyResult:
    """Result for a single company"""
    company_name: str
    domain: str | None = None
    city: str | None = None
    state: str | None = None
    vertical: str | None = None

    # Discovery results
    website_contacts: list[ExtractedContact] = field(default_factory=list)
    serper_owner: str | None = None

    # OpenWeb Ninja results
    google_maps_result: LocalBusinessResult | None = None
    openweb_contacts_result: OpenWebContactResult | None = None
    social_links_result: SocialLinksResult | None = None

    # Final validated contacts
    contacts: list[ContactResult] = field(default_factory=list)

    # Pipeline stats
    stages_completed: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    processing_time_ms: float = 0


@dataclass
class SMBPipelineResult:
    """Overall pipeline result"""
    total_companies: int
    companies_processed: int
    contacts_found: int
    contacts_validated: int

    # Per-stage stats
    stage_stats: dict[str, dict] = field(default_factory=dict)

    # Cost tracking
    serper_queries: int = 0
    leadmagic_credits: int = 0
    zenrows_requests: int = 0
    openweb_ninja_queries: int = 0  # $0.002 per query

    # Results
    results: list[CompanyResult] = field(default_factory=list)

    # Timing
    start_time: datetime | None = None
    end_time: datetime | None = None

    @property
    def total_cost(self) -> float:
        """Estimate total cost"""
        serper_cost = self.serper_queries * 0.001
        leadmagic_cost = self.leadmagic_credits * 0.01  # Approx
        zenrows_cost = self.zenrows_requests * 0.01  # Approx
        openweb_cost = self.openweb_ninja_queries * 0.002  # $0.002/query
        return serper_cost + leadmagic_cost + zenrows_cost + openweb_cost


class SMBContactPipeline:
    """
    Multi-stage pipeline for finding SMB owner contacts.

    Stages:
    1. Input Analysis - Explore CSV/JSON structure
    2. Google Maps Discovery - Owner, phone, email from Google Maps (OpenWeb Ninja)
    3. Website Contacts - Extract emails/phones/socials from domain (OpenWeb Ninja)
    4. Data Fill - Use Serper to fill missing domains/phones (fallback)
    5. Website Extraction - Schema.org + page scraping (fallback if OpenWeb fails)
    6. Serper OSINT - Owner name discovery
    7. Social Links Search - Find LinkedIn for discovered names (OpenWeb Ninja)
    8. Email Enrichment - LeadMagic email-to-LinkedIn
    9. Validation - Simple rule-based scoring
    """

    def __init__(
        self,
        serper_api_key: str | None = None,
        leadmagic_api_key: str | None = None,
        zenrows_api_key: str | None = None,
        rapidapi_key: str | None = None,
        openai_api_key: str | None = None,
        min_validation_score: int = 50,
        concurrency: int = 10,
        use_llm_validation: bool = True
    ):
        self.serper_api_key = serper_api_key or os.environ.get("SERPER_API_KEY")
        self.leadmagic_api_key = leadmagic_api_key or os.environ.get("LEADMAGIC_API_KEY")
        self.zenrows_api_key = zenrows_api_key or os.environ.get("ZENROWS_API_KEY")
        self.rapidapi_key = rapidapi_key or os.environ.get("RAPIDAPI_KEY")
        self.openai_api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
        self.min_validation_score = min_validation_score
        self.concurrency = concurrency
        self.use_llm_validation = use_llm_validation

        # Initialize components
        self.csv_explorer = CSVExplorer()
        self.serper_filler = SerperDataFiller(self.serper_api_key) if self.serper_api_key else None
        self.website_extractor = WebsiteContactExtractor(
            zenrows_api_key=self.zenrows_api_key,
            max_pages=3,
            concurrency=5
        )
        self.leadmagic = LeadMagicClient(self.leadmagic_api_key) if self.leadmagic_api_key else None
        self.validator = SimpleContactValidator(min_confidence=min_validation_score)

        # OpenWeb Ninja client ($0.002/query - primary for SMBs)
        self.openweb_ninja = OpenWebNinjaClient(self.rapidapi_key) if self.rapidapi_key else None

        # LLM Judge for validation (primary for SMBs when enabled)
        self.llm_judge: ContactJudge | None = None
        if use_llm_validation and self.openai_api_key:
            try:
                llm_provider = OpenAIProvider(api_key=self.openai_api_key)
                self.llm_judge = ContactJudge(llm_provider)
                logger.info("LLM validation enabled (GPT-4o-mini)")
            except Exception as e:
                logger.warning(f"Failed to initialize LLM judge: {e}. Using rule-based fallback.")

        # Stats tracking
        self._serper_queries = 0
        self._leadmagic_credits = 0
        self._zenrows_requests = 0
        self._openweb_ninja_queries = 0
        self._llm_validations = 0

    async def close(self):
        """Cleanup resources"""
        await self.website_extractor.close()
        if self.leadmagic:
            await self.leadmagic.close()
        if self.openweb_ninja:
            await self.openweb_ninja.close()

    async def run(
        self,
        input_file: str,
        limit: int | None = None,
        skip_stages: list[str] | None = None
    ) -> SMBPipelineResult:
        """
        Run the full pipeline on input file.

        Args:
            input_file: Path to CSV or JSON file
            limit: Optional limit on companies to process
            skip_stages: Stages to skip (data_fill, website, serper_osint, enrichment)

        Returns:
            SMBPipelineResult with all results and stats
        """
        skip_stages = skip_stages or []
        result = SMBPipelineResult(
            total_companies=0,
            companies_processed=0,
            contacts_found=0,
            contacts_validated=0,
            start_time=datetime.now()
        )

        try:
            # Stage 1: Analyze input
            logger.info(f"Stage 1: Analyzing input file: {input_file}")

            if input_file.endswith('.json'):
                analysis = self.csv_explorer.analyze_json(input_file, limit=limit)
            else:
                analysis = self.csv_explorer.analyze(input_file, limit=limit)

            result.total_companies = len(analysis.companies)
            result.stage_stats["input_analysis"] = {
                "total_rows": analysis.total_rows,
                "companies_loaded": len(analysis.companies),
                "detected_fields": analysis.detected_fields,
                "missing_fields": analysis.missing_fields,
                "has_domain": f"{analysis.has_domain:.1%}",
                "has_owner": f"{analysis.has_owner:.1%}"
            }

            logger.info(f"  Loaded {len(analysis.companies)} companies")
            logger.info(f"  Detected fields: {analysis.detected_fields}")
            logger.info(f"  Domain coverage: {analysis.has_domain:.1%}")

            # Process companies in batches
            semaphore = asyncio.Semaphore(self.concurrency)

            async def process_company(company: dict) -> CompanyResult:
                async with semaphore:
                    return await self._process_single_company(company, skip_stages)

            # Run all companies
            company_results = await asyncio.gather(
                *[process_company(c) for c in analysis.companies],
                return_exceptions=True
            )

            # Collect results
            for i, cr in enumerate(company_results):
                if isinstance(cr, Exception):
                    logger.error(f"Company {i} failed: {cr}")
                    continue

                result.results.append(cr)
                result.companies_processed += 1
                result.contacts_found += len(cr.contacts)
                result.contacts_validated += sum(
                    1 for c in cr.contacts
                    if c.validation and c.validation.is_valid
                )

            # Update cost tracking
            result.serper_queries = self._serper_queries
            result.leadmagic_credits = self._leadmagic_credits
            result.zenrows_requests = self._zenrows_requests
            result.openweb_ninja_queries = self._openweb_ninja_queries

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            raise
        finally:
            result.end_time = datetime.now()
            await self.close()

        return result

    async def _process_single_company(
        self,
        company: dict,
        skip_stages: list[str]
    ) -> CompanyResult:
        """Process a single company through the pipeline"""
        import time
        start_time = time.time()

        result = CompanyResult(
            company_name=company.get("company_name", "Unknown"),
            domain=company.get("domain"),
            city=company.get("city"),
            state=company.get("state"),
            vertical=company.get("vertical")
        )

        try:
            # Stage 1: Google Maps Discovery (OpenWeb Ninja - PRIMARY for SMBs)
            # $0.002/query - Returns owner, phone, email, website, social links
            if "google_maps" not in skip_stages and self.openweb_ninja:
                try:
                    location = f"{result.city}, {result.state}" if result.city and result.state else None
                    gmaps_result = await self.openweb_ninja.search_local_business(
                        result.company_name,
                        location=location
                    )
                    self._openweb_ninja_queries += 1

                    if gmaps_result.success:
                        result.google_maps_result = gmaps_result

                        # Fill missing domain from Google Maps
                        if not result.domain and gmaps_result.website:
                            from urllib.parse import urlparse
                            parsed = urlparse(gmaps_result.website)
                            result.domain = parsed.netloc.replace("www.", "")

                        result.stages_completed.append("google_maps")
                        logger.debug(f"Google Maps found: {gmaps_result.name}, owner={gmaps_result.owner_name}")

                except Exception as e:
                    result.errors.append(f"Google Maps failed: {e}")
                    logger.debug(f"Google Maps error for {result.company_name}: {e}")

            # Stage 2: Website Contacts Scraper (OpenWeb Ninja - PRIMARY)
            # $0.002/query - Returns emails, phones, social links from domain
            if "openweb_contacts" not in skip_stages and self.openweb_ninja and result.domain:
                try:
                    contacts_result = await self.openweb_ninja.scrape_contacts(result.domain)
                    self._openweb_ninja_queries += 1

                    if contacts_result.success:
                        result.openweb_contacts_result = contacts_result
                        result.stages_completed.append("openweb_contacts")
                        logger.debug(f"OpenWeb found {len(contacts_result.emails)} emails for {result.domain}")

                except Exception as e:
                    result.errors.append(f"OpenWeb contacts failed: {e}")
                    logger.debug(f"OpenWeb contacts error for {result.domain}: {e}")

            # Stage 3: Fill missing data with Serper (FALLBACK)
            if "data_fill" not in skip_stages and self.serper_filler:
                missing = []
                if not result.domain:
                    missing.append("domain")
                if not company.get("phone"):
                    missing.append("phone")
                if not company.get("owner"):
                    missing.append("owner")

                if missing:
                    fill_result = await self.serper_filler.fill_missing(company, missing)
                    self._serper_queries += fill_result.queries_run

                    # Update result with filled data
                    if fill_result.filled.get("domain"):
                        result.domain = fill_result.filled["domain"]
                    if fill_result.filled.get("owner"):
                        result.serper_owner = fill_result.filled["owner"]

                    result.stages_completed.append("data_fill")

            # Stage 4: Website extraction (FALLBACK - only if OpenWeb Ninja didn't find contacts)
            openweb_had_contacts = (
                result.openweb_contacts_result and
                result.openweb_contacts_result.success and
                len(result.openweb_contacts_result.emails) > 0
            )
            if "website" not in skip_stages and result.domain and not openweb_had_contacts:
                try:
                    web_result = await self.website_extractor.extract(result.domain)
                    self._zenrows_requests += web_result.pages_scraped

                    result.website_contacts = web_result.contacts
                    result.stages_completed.append("website_fallback")

                except Exception as e:
                    result.errors.append(f"Website extraction failed: {e}")

            # Stage 5: Serper OSINT for owner (FALLBACK - only if no owner from Google Maps)
            gmaps_has_owner = result.google_maps_result and result.google_maps_result.owner_name
            if "serper_osint" not in skip_stages and self.serper_filler:
                if not result.serper_owner and not gmaps_has_owner and not result.website_contacts:
                    # Run owner search
                    owner_result = await self.serper_filler.fill_missing(
                        {"company_name": result.company_name, "city": result.city, "state": result.state},
                        ["owner"]
                    )
                    self._serper_queries += owner_result.queries_run

                    if owner_result.filled.get("owner"):
                        result.serper_owner = owner_result.filled["owner"]

                    result.stages_completed.append("serper_osint")

            # Collect all candidate contacts
            candidates = self._collect_candidates(result, company)

            # Stage 6: Social Links Search (OpenWeb Ninja - find LinkedIn/Facebook for names without it)
            # $0.002/query - searches for LinkedIn profiles, then Facebook as fallback for SMBs
            if "social_links" not in skip_stages and self.openweb_ninja:
                for candidate in candidates:
                    if candidate.get("name") and not candidate.get("linkedin_url"):
                        try:
                            # Search for LinkedIn profile
                            search_query = f"{candidate['name']} {result.company_name}"
                            social_result = await self.openweb_ninja.search_social_links(
                                search_query,
                                platform="linkedin"
                            )
                            self._openweb_ninja_queries += 1

                            if social_result.success and social_result.primary_linkedin:
                                candidate["linkedin_url"] = social_result.primary_linkedin
                                if "social_links" not in candidate.get("sources", []):
                                    candidate.setdefault("sources", []).append("social_links")
                                result.social_links_result = social_result
                                logger.debug(f"Found LinkedIn for {candidate['name']}: {social_result.primary_linkedin}")
                            else:
                                # SMB fallback: Search Facebook when LinkedIn fails
                                # Many SMB owners have Facebook but not LinkedIn
                                if not candidate.get("facebook_url"):
                                    try:
                                        fb_result = await self.openweb_ninja.search_social_links(
                                            search_query,
                                            platform="facebook"
                                        )
                                        self._openweb_ninja_queries += 1

                                        if fb_result.facebook_urls:
                                            candidate["facebook_url"] = fb_result.facebook_urls[0]
                                            if "social_links_fb" not in candidate.get("sources", []):
                                                candidate.setdefault("sources", []).append("social_links_fb")
                                            logger.debug(f"Found Facebook for {candidate['name']}: {fb_result.facebook_urls[0]}")
                                    except Exception as e:
                                        logger.debug(f"Facebook search failed for {candidate.get('name')}: {e}")

                        except Exception as e:
                            logger.debug(f"Social Links Search failed for {candidate.get('name')}: {e}")

                result.stages_completed.append("social_links")

            # Stage 7: Enrichment (if we have emails and LeadMagic)
            if "enrichment" not in skip_stages and self.leadmagic:
                for candidate in candidates:
                    if candidate.get("email") and not candidate.get("linkedin_url"):
                        try:
                            enrich_result = await self.leadmagic.email_to_linkedin(
                                candidate["email"]
                            )
                            if enrich_result.success and enrich_result.linkedin_url:
                                candidate["linkedin_url"] = enrich_result.linkedin_url
                                self._leadmagic_credits += enrich_result.credits_consumed
                        except Exception as e:
                            logger.debug(f"LeadMagic enrichment failed: {e}")

                result.stages_completed.append("enrichment")

            # Stage 8: Validation (LLM primary, rule-based fallback)
            for candidate in candidates:
                validation = None
                llm_judgment = None

                # Try LLM validation first
                if self.llm_judge:
                    try:
                        # Build evidence bundle from discovery results
                        evidence = self._build_evidence_bundle(result, candidate)

                        llm_judgment = await self.llm_judge.validate_contact(
                            company_name=result.company_name,
                            domain=result.domain or "",
                            domain_confidence=100.0,  # We have the domain
                            contact_name=candidate.get("name"),
                            contact_title=candidate.get("title"),
                            contact_email=candidate.get("email"),
                            email_source="discovery",
                            email_verified=None,
                            is_catch_all=None,
                            linkedin_url=candidate.get("linkedin_url"),
                            phone=candidate.get("phone"),
                            evidence=evidence,
                            target_titles=["Owner", "Founder", "CEO", "President", "Manager"],
                            industry=result.vertical,
                            location=f"{result.city}, {result.state}" if result.city and result.state else None
                        )
                        self._llm_validations += 1

                        # Convert LLM judgment to ValidationResult
                        # Note: red_flags stored in reasons for compatibility
                        reasons = [llm_judgment.reasoning]
                        if llm_judgment.red_flags:
                            reasons.extend([f"RED FLAG: {rf}" for rf in llm_judgment.red_flags])

                        # For SMB validation, use confidence threshold (40%)
                        # LLM doesn't always follow the accept rule consistently
                        smb_accept_threshold = 40  # Lower for SMBs
                        is_valid = llm_judgment.overall_confidence >= smb_accept_threshold

                        validation = ValidationResult(
                            is_valid=is_valid,
                            confidence=llm_judgment.overall_confidence,
                            reasons=reasons,
                            method="llm"
                        )
                        logger.debug(f"LLM validated {candidate.get('name')}: accept={llm_judgment.accept}, confidence={llm_judgment.overall_confidence}")

                    except Exception as e:
                        logger.warning(f"LLM validation failed for {candidate.get('name')}: {e}")
                        # Fall through to rule-based

                # Fallback to rule-based if LLM failed or not available
                if validation is None:
                    contact_candidate = dict_to_candidate(candidate, result.domain)
                    validation = self.validator.validate(contact_candidate)

                contact_result = ContactResult(
                    name=candidate.get("name"),
                    email=candidate.get("email"),
                    phone=candidate.get("phone"),
                    title=candidate.get("title"),
                    linkedin_url=candidate.get("linkedin_url"),
                    sources=candidate.get("sources", []),
                    validation=validation
                )

                result.contacts.append(contact_result)

            result.stages_completed.append("validation")

        except Exception as e:
            result.errors.append(str(e))
            logger.error(f"Error processing {result.company_name}: {e}")

        result.processing_time_ms = (time.time() - start_time) * 1000
        return result

    def _collect_candidates(self, result: CompanyResult, original_company: dict) -> list[dict]:
        """Collect all candidate contacts from various sources"""
        candidates = []
        seen_names = set()

        # From original data (if owner was in CSV)
        if original_company.get("owner"):
            candidates.append({
                "name": original_company["owner"],
                "title": original_company.get("owner_title", "Owner"),
                "email": original_company.get("email"),
                "phone": original_company.get("phone"),
                "sources": ["input_csv"]
            })
            seen_names.add(original_company["owner"].lower())

        # From Google Maps (OpenWeb Ninja) - PRIMARY for SMBs
        if result.google_maps_result and result.google_maps_result.success:
            gmaps = result.google_maps_result
            if gmaps.owner_name and gmaps.owner_name.lower() not in seen_names:
                candidate = {
                    "name": gmaps.owner_name,
                    "title": "Owner",
                    "phone": gmaps.phone,
                    "email": gmaps.email,
                    "sources": ["google_maps_owner"],
                    # SMB validation fields
                    "google_maps_place_id": gmaps.place_id,
                    "google_maps_reviews": gmaps.reviews_count,
                    "google_maps_rating": gmaps.rating,
                    "address": gmaps.address,
                }
                # Add social links if available
                if gmaps.social_links.get("facebook"):
                    candidate["facebook_url"] = gmaps.social_links["facebook"]
                if gmaps.social_links.get("instagram"):
                    candidate["instagram_url"] = gmaps.social_links["instagram"]
                if gmaps.social_links.get("linkedin"):
                    candidate["linkedin_url"] = gmaps.social_links["linkedin"]

                candidates.append(candidate)
                seen_names.add(gmaps.owner_name.lower())

        # From OpenWeb Ninja Website Contacts - extract ALL emails
        if result.openweb_contacts_result and result.openweb_contacts_result.success:
            contacts = result.openweb_contacts_result
            # Add all email contacts (SMBs may have multiple relevant emails)
            for email_info in contacts.emails:
                email = email_info.get("value")
                if email:
                    candidate = {
                        "email": email,
                        "phone": contacts.primary_phone,
                        "sources": ["openweb_contacts"],
                        "email_source": email_info.get("sources", []),  # Track source metadata
                    }
                    # Add social links
                    if contacts.linkedin:
                        candidate["linkedin_url"] = contacts.linkedin
                    if contacts.facebook:
                        candidate["facebook_url"] = contacts.facebook
                    if contacts.instagram:
                        candidate["instagram_url"] = contacts.instagram
                    if contacts.twitter:
                        candidate["twitter_url"] = contacts.twitter
                    candidates.append(candidate)
                    # Continue to add all emails, not just first

        # From Serper owner discovery
        if result.serper_owner and result.serper_owner.lower() not in seen_names:
            candidates.append({
                "name": result.serper_owner,
                "title": "Owner",
                "sources": ["serper_osint"]
            })
            seen_names.add(result.serper_owner.lower())

        # From website extraction
        for contact in result.website_contacts:
            if contact.name and contact.name.lower() not in seen_names:
                candidates.append({
                    "name": contact.name,
                    "title": contact.title,
                    "email": contact.email,
                    "phone": contact.phone,
                    "linkedin_url": contact.linkedin_url,
                    "sources": [contact.source_type]
                })
                seen_names.add(contact.name.lower())
            elif contact.email and not contact.name:
                # Email without name
                candidates.append({
                    "email": contact.email,
                    "sources": [contact.source_type]
                })

        # Merge sources for duplicate names
        merged = {}
        for c in candidates:
            name_key = (c.get("name") or c.get("email") or "").lower()
            if name_key not in merged:
                merged[name_key] = c
            else:
                # Merge sources and fill missing fields
                existing = merged[name_key]
                existing["sources"] = list(set(existing.get("sources", []) + c.get("sources", [])))
                # Include all fields, including new SMB-specific ones
                merge_fields = [
                    "email", "phone", "title", "linkedin_url",
                    "google_maps_place_id", "google_maps_reviews", "google_maps_rating",
                    "facebook_url", "instagram_url", "twitter_url", "address"
                ]
                for field in merge_fields:
                    if not existing.get(field) and c.get(field):
                        existing[field] = c[field]

        return list(merged.values())

    def _build_evidence_bundle(self, result: CompanyResult, candidate: dict) -> str:
        """Build evidence bundle for LLM validation from discovery results"""
        sources = []

        # Google Maps evidence (primary for SMBs)
        if result.google_maps_result and result.google_maps_result.success:
            gmaps = result.google_maps_result
            content = f"Business: {gmaps.name}"
            if gmaps.owner_name:
                content += f"\nOwner: {gmaps.owner_name}"
            if gmaps.phone:
                content += f"\nPhone: {gmaps.phone}"
            if gmaps.email:
                content += f"\nEmail: {gmaps.email}"
            if gmaps.address:
                content += f"\nAddress: {gmaps.address}"
            if gmaps.rating:
                content += f"\nRating: {gmaps.rating} ({gmaps.reviews_count} reviews)"
            if gmaps.category:
                content += f"\nCategory: {gmaps.category}"

            sources.append({
                "source": "google_maps",
                "url": f"https://maps.google.com/?cid={gmaps.place_id}" if gmaps.place_id else "",
                "content": content
            })

        # OpenWeb Ninja website contacts evidence
        if result.openweb_contacts_result and result.openweb_contacts_result.success:
            contacts = result.openweb_contacts_result
            content = f"Domain: {contacts.domain}"
            if contacts.emails:
                content += f"\nEmails: {[e.get('value') for e in contacts.emails]}"
            if contacts.phone_numbers:
                content += f"\nPhones: {[p.get('value') for p in contacts.phone_numbers]}"
            if contacts.linkedin:
                content += f"\nLinkedIn: {contacts.linkedin}"
            if contacts.facebook:
                content += f"\nFacebook: {contacts.facebook}"

            sources.append({
                "source": "website_contacts",
                "url": f"https://{contacts.domain}",
                "content": content
            })

        # Serper OSINT evidence
        if result.serper_owner:
            sources.append({
                "source": "serper_osint",
                "url": "",
                "content": f"Owner name found via search: {result.serper_owner}"
            })

        # Candidate-specific evidence from sources
        if candidate.get("sources"):
            candidate_sources = ", ".join(candidate["sources"])
            candidate_content = f"Candidate sources: {candidate_sources}"
            if candidate.get("google_maps_reviews"):
                candidate_content += f"\nGoogle Maps reviews: {candidate['google_maps_reviews']}"
            if candidate.get("google_maps_rating"):
                candidate_content += f"\nGoogle Maps rating: {candidate['google_maps_rating']}"
            if candidate.get("address"):
                candidate_content += f"\nAddress: {candidate['address']}"

            sources.append({
                "source": "candidate_metadata",
                "url": "",
                "content": candidate_content
            })

        return create_evidence_bundle(sources)


def print_pipeline_result(result: SMBPipelineResult):
    """Print a summary of pipeline results"""
    duration = (result.end_time - result.start_time).total_seconds() if result.end_time and result.start_time else 0

    print(f"\n{'='*60}")
    print("SMB Contact Pipeline Results")
    print(f"{'='*60}")
    print(f"Duration: {duration:.1f}s")
    print(f"Companies processed: {result.companies_processed}/{result.total_companies}")
    print(f"Contacts found: {result.contacts_found}")
    print(f"Contacts validated: {result.contacts_validated}")
    print()

    # Rates
    if result.companies_processed > 0:
        find_rate = result.contacts_found / result.companies_processed * 100
        validate_rate = result.contacts_validated / result.companies_processed * 100
        print(f"Find rate: {find_rate:.1f}% (contacts per company)")
        print(f"Validation rate: {validate_rate:.1f}% (validated per company)")

    print()
    print("Cost Estimate:")
    print(f"  OpenWeb Ninja: {result.openweb_ninja_queries} queries (${result.openweb_ninja_queries * 0.002:.3f})")
    print(f"  Serper queries: {result.serper_queries} (${result.serper_queries * 0.001:.3f})")
    print(f"  LeadMagic credits: {result.leadmagic_credits} (${result.leadmagic_credits * 0.01:.2f})")
    print(f"  ZenRows requests: {result.zenrows_requests}")
    print(f"  Total: ${result.total_cost:.3f}")

    print()
    print("Stage Stats:")
    for stage, stats in result.stage_stats.items():
        print(f"  {stage}: {stats}")

    # Sample results
    print()
    print("Sample Results:")
    for r in result.results[:5]:
        print(f"\n  {r.company_name} ({r.domain})")
        print(f"    Stages: {r.stages_completed}")
        print(f"    Contacts: {len(r.contacts)}")
        for c in r.contacts[:2]:
            status = "VALID" if c.validation and c.validation.is_valid else "INVALID"
            score = c.validation.confidence if c.validation else 0
            print(f"      - {c.name} ({c.title}) [{status} {score:.0f}]")
            if c.email:
                print(f"        Email: {c.email}")
            if c.linkedin_url:
                print(f"        LinkedIn: {c.linkedin_url}")

    print(f"\n{'='*60}\n")


# CLI test
async def test_pipeline():
    """Test the pipeline"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python smb_pipeline.py <input_file> [limit]")
        sys.exit(1)

    input_file = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10

    pipeline = SMBContactPipeline(concurrency=5)

    try:
        result = await pipeline.run(input_file, limit=limit)
        print_pipeline_result(result)
    finally:
        await pipeline.close()


if __name__ == "__main__":
    asyncio.run(test_pipeline())
