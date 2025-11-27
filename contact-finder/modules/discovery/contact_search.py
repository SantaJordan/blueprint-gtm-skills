"""
Contact Search Engine
Find contacts at companies using multiple sources in parallel
"""

import asyncio
from dataclasses import dataclass, field
from typing import Any
from enum import Enum

from ..validation.linkedin_normalizer import normalize_linkedin_url, is_valid_linkedin_in_url
from ..validation.email_validator import EmailOrigin


class ContactSource(Enum):
    """Where a contact candidate came from"""
    SCRAPIN = "scrapin"           # FREE - LinkedIn scraping
    EXA = "exa"                   # FREE - Semantic search
    BLITZ_WATERFALL = "blitz"     # CHEAP - ICP waterfall
    LEADMAGIC = "leadmagic"       # PAID - Email enrichment
    SITE_SCRAPE = "site_scrape"   # FREE - Website scraping
    GOOGLE_MAPS = "google_maps"   # FREE - Maps listing


@dataclass
class ContactCandidate:
    """A contact candidate from search"""
    name: str | None
    first_name: str | None
    last_name: str | None
    title: str | None
    email: str | None
    phone: str | None
    linkedin_url: str | None  # Normalized linkedin.com/in/xxx
    source: ContactSource
    email_origin: EmailOrigin | None
    confidence: float  # 0-100
    evidence: list[str] = field(default_factory=list)
    raw_data: dict = field(default_factory=dict)


@dataclass
class ContactSearchResult:
    """Result of contact search for a company"""
    company_name: str
    domain: str | None
    linkedin_company_url: str | None
    candidates: list[ContactCandidate] = field(default_factory=list)
    sources_tried: list[str] = field(default_factory=list)
    sources_succeeded: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class ContactSearchEngine:
    """
    Search for contacts at companies using multiple sources in parallel.

    Cost-optimized priority:
    1. Scrapin (FREE) - LinkedIn profiles
    2. Exa (FREE) - Semantic search
    3. Site scraping (FREE) - Company website
    4. Blitz waterfall (CHEAP) - ICP search
    5. LeadMagic (PAID) - Only when needed for email

    The engine finds candidates; enrichment/validation happens later.
    """

    def __init__(
        self,
        scrapin_client: Any = None,
        exa_client: Any = None,
        blitz_client: Any = None,
        site_scraper: Any = None,
        target_titles: list[str] | None = None
    ):
        self.scrapin = scrapin_client
        self.exa = exa_client
        self.blitz = blitz_client
        self.site_scraper = site_scraper
        self.target_titles = target_titles or [
            "Owner", "CEO", "President", "Founder",
            "General Manager", "Manager", "Director"
        ]

    async def _search_scrapin(
        self,
        company_name: str,
        domain: str | None,
        linkedin_company_url: str | None
    ) -> list[ContactCandidate]:
        """
        Search using Scrapin (FREE).

        If we have LinkedIn company URL, get employees directly.
        Otherwise search by company name.
        """
        if not self.scrapin:
            return []

        candidates = []

        try:
            # Get company profile if we have LinkedIn URL
            if linkedin_company_url:
                # Extract employees from company profile
                company_data = await self.scrapin.get_company_profile(linkedin_company_url)

                # Look for employee data if available
                employees = company_data.raw_response.get("employees", [])
                for emp in employees[:10]:  # Limit to 10
                    name = emp.get("name")
                    title = emp.get("title", "")

                    # Filter by target titles
                    if not self._matches_target_title(title):
                        continue

                    linkedin_url = emp.get("linkedin_url")
                    normalized_url = normalize_linkedin_url(linkedin_url)

                    candidates.append(ContactCandidate(
                        name=name,
                        first_name=emp.get("first_name"),
                        last_name=emp.get("last_name"),
                        title=title,
                        email=None,  # Scrapin doesn't give emails directly
                        phone=None,
                        linkedin_url=normalized_url,
                        source=ContactSource.SCRAPIN,
                        email_origin=None,
                        confidence=70 if normalized_url else 50,
                        evidence=[f"Found in {company_name} LinkedIn employees"],
                        raw_data=emp
                    ))

            # Also try person matching if we have the company
            if company_name:
                for title in self.target_titles[:3]:  # Try top 3 titles
                    try:
                        result = await self.scrapin.match_person(
                            company_name=company_name,
                            title=title
                        )
                        if result.name:
                            normalized_url = normalize_linkedin_url(result.linkedin_url)

                            # Check if we already have this person
                            if not any(c.linkedin_url == normalized_url and normalized_url for c in candidates):
                                candidates.append(ContactCandidate(
                                    name=result.name,
                                    first_name=result.first_name,
                                    last_name=result.last_name,
                                    title=result.title or title,
                                    email=result.email,
                                    phone=result.phone,
                                    linkedin_url=normalized_url,
                                    source=ContactSource.SCRAPIN,
                                    email_origin=EmailOrigin.LINKEDIN_ENRICHED if result.email else None,
                                    confidence=75 if result.email else 60,
                                    evidence=[f"Scrapin match for {title} at {company_name}"],
                                    raw_data=result.raw_response
                                ))
                    except Exception:
                        continue

        except Exception as e:
            pass  # Will try other sources

        return candidates

    async def _search_exa(
        self,
        company_name: str,
        domain: str | None,
        location: str | None = None
    ) -> list[ContactCandidate]:
        """
        Search using Exa semantic search (FREE).

        Finds people mentioned in context with the company.
        """
        if not self.exa:
            return []

        candidates = []

        try:
            result = await self.exa.find_company_contacts(
                company_name=company_name,
                domain=domain,
                titles=self.target_titles[:3],
                location=location,
                num_results=10
            )

            for r in result.results:
                # Try to extract LinkedIn URL
                url = r.url
                linkedin_url = None

                if url and "linkedin.com/in" in url:
                    linkedin_url = normalize_linkedin_url(url)

                # Extract name from title if LinkedIn
                name = None
                if linkedin_url and r.title:
                    # LinkedIn titles often like "John Smith - CEO at Company"
                    name = r.title.split(" - ")[0].split(" | ")[0].strip()

                # Look for title in content/highlights
                title = None
                for highlight in r.highlights:
                    for target in self.target_titles:
                        if target.lower() in highlight.lower():
                            title = target
                            break
                    if title:
                        break

                if linkedin_url or name:
                    candidates.append(ContactCandidate(
                        name=name,
                        first_name=None,
                        last_name=None,
                        title=title,
                        email=None,
                        phone=None,
                        linkedin_url=linkedin_url,
                        source=ContactSource.EXA,
                        email_origin=None,
                        confidence=60 if linkedin_url else 40,
                        evidence=[f"Exa search: {r.title or 'Unknown'}"],
                        raw_data=r.raw_response
                    ))

        except Exception:
            pass

        return candidates

    async def _search_blitz_waterfall(
        self,
        company_name: str,
        domain: str | None,
        location: str | None = None
    ) -> list[ContactCandidate]:
        """
        Search using Blitz waterfall ICP (CHEAP).

        This is a paid API but cost-effective for finding contacts.
        """
        if not self.blitz:
            return []

        candidates = []

        try:
            result = await self.blitz.waterfall_icp(
                company_name=company_name,
                domain=domain,
                job_titles=self.target_titles,
                location=location,
                max_results=5
            )

            for contact in result.contacts:
                linkedin_url = normalize_linkedin_url(contact.linkedin_url)

                # Determine email origin
                email_origin = None
                if contact.email:
                    if contact.email_verified:
                        email_origin = EmailOrigin.ENRICHED_API
                    else:
                        email_origin = EmailOrigin.PATTERN_GUESS

                candidates.append(ContactCandidate(
                    name=contact.full_name,
                    first_name=contact.first_name,
                    last_name=contact.last_name,
                    title=contact.job_title,
                    email=contact.email,
                    phone=None,  # Phone costs extra, skip by default
                    linkedin_url=linkedin_url,
                    source=ContactSource.BLITZ_WATERFALL,
                    email_origin=email_origin,
                    confidence=contact.confidence_score if contact.confidence_score else 70,
                    evidence=[f"Blitz ICP waterfall: {contact.job_title}"],
                    raw_data=contact.raw_response
                ))

        except Exception:
            pass

        return candidates

    async def _search_site_scrape(
        self,
        company_name: str,
        domain: str | None
    ) -> list[ContactCandidate]:
        """
        Scrape company website for contacts (FREE).

        Looks for team pages, about pages, contact pages.
        """
        if not self.site_scraper or not domain:
            return []

        candidates = []

        try:
            result = await self.site_scraper.scrape_domain(domain)

            # Site emails (highest trust for email)
            for email in result.emails[:5]:
                candidates.append(ContactCandidate(
                    name=None,
                    first_name=None,
                    last_name=None,
                    title=None,
                    email=email,
                    phone=None,
                    linkedin_url=None,
                    source=ContactSource.SITE_SCRAPE,
                    email_origin=EmailOrigin.SITE_OBSERVED,
                    confidence=80,  # Site-observed email is high trust
                    evidence=[f"Email found on {domain}"],
                    raw_data={"email": email, "source": "site_scrape"}
                ))

            # Extracted contacts
            for contact in result.contacts[:5]:
                candidates.append(ContactCandidate(
                    name=contact.name,
                    first_name=None,
                    last_name=None,
                    title=contact.title,
                    email=contact.email,
                    phone=contact.phone,
                    linkedin_url=None,
                    source=ContactSource.SITE_SCRAPE,
                    email_origin=EmailOrigin.SITE_OBSERVED if contact.email else None,
                    confidence=75 if contact.email else 50,
                    evidence=[f"Extracted from {contact.source_url}"],
                    raw_data={"context": contact.context}
                ))

        except Exception:
            pass

        return candidates

    def _matches_target_title(self, title: str | None) -> bool:
        """Check if title matches any target title"""
        if not title:
            return False

        title_lower = title.lower()
        for target in self.target_titles:
            if target.lower() in title_lower:
                return True

        return False

    def _deduplicate_candidates(
        self,
        candidates: list[ContactCandidate]
    ) -> list[ContactCandidate]:
        """
        Deduplicate candidates, merging info from multiple sources.

        Priority: Keep candidate with most info and highest confidence.
        """
        # Group by LinkedIn URL (if available) or email
        groups: dict[str, list[ContactCandidate]] = {}

        for c in candidates:
            # Key by LinkedIn URL if available, else email, else name
            if c.linkedin_url:
                key = c.linkedin_url
            elif c.email:
                key = c.email.lower()
            elif c.name:
                key = c.name.lower()
            else:
                key = f"unknown_{id(c)}"

            if key not in groups:
                groups[key] = []
            groups[key].append(c)

        # Merge each group
        merged = []
        for key, group in groups.items():
            if len(group) == 1:
                merged.append(group[0])
            else:
                # Merge: take best info from each
                best = max(group, key=lambda x: x.confidence)

                # Merge evidence
                all_evidence = []
                for c in group:
                    all_evidence.extend(c.evidence)

                # Fill in missing fields from other candidates
                for c in group:
                    if not best.name and c.name:
                        best.name = c.name
                    if not best.first_name and c.first_name:
                        best.first_name = c.first_name
                    if not best.last_name and c.last_name:
                        best.last_name = c.last_name
                    if not best.title and c.title:
                        best.title = c.title
                    if not best.email and c.email:
                        best.email = c.email
                        best.email_origin = c.email_origin
                    if not best.phone and c.phone:
                        best.phone = c.phone
                    if not best.linkedin_url and c.linkedin_url:
                        best.linkedin_url = c.linkedin_url

                best.evidence = list(set(all_evidence))
                merged.append(best)

        # Sort by confidence
        merged.sort(key=lambda x: x.confidence, reverse=True)

        return merged

    async def search(
        self,
        company_name: str,
        domain: str | None = None,
        linkedin_company_url: str | None = None,
        location: str | None = None,
        use_paid_apis: bool = True
    ) -> ContactSearchResult:
        """
        Search for contacts at a company using all available sources.

        Args:
            company_name: Company name
            domain: Company domain
            linkedin_company_url: Company LinkedIn URL (normalized)
            location: Location for filtering
            use_paid_apis: Whether to use paid APIs (Blitz)

        Returns:
            ContactSearchResult with all candidates
        """
        result = ContactSearchResult(
            company_name=company_name,
            domain=domain,
            linkedin_company_url=linkedin_company_url
        )

        # Build task list (free APIs first)
        tasks = []
        task_names = []

        # FREE: Scrapin
        if self.scrapin:
            tasks.append(self._search_scrapin(company_name, domain, linkedin_company_url))
            task_names.append("scrapin")
            result.sources_tried.append("scrapin")

        # FREE: Exa
        if self.exa:
            tasks.append(self._search_exa(company_name, domain, location))
            task_names.append("exa")
            result.sources_tried.append("exa")

        # FREE: Site scrape
        if self.site_scraper and domain:
            tasks.append(self._search_site_scrape(company_name, domain))
            task_names.append("site_scrape")
            result.sources_tried.append("site_scrape")

        # PAID: Blitz waterfall
        if self.blitz and use_paid_apis:
            tasks.append(self._search_blitz_waterfall(company_name, domain, location))
            task_names.append("blitz")
            result.sources_tried.append("blitz")

        # Run all in parallel
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            all_candidates = []
            for i, res in enumerate(results):
                if isinstance(res, list) and res:
                    all_candidates.extend(res)
                    result.sources_succeeded.append(task_names[i])
                elif isinstance(res, Exception):
                    result.errors.append(f"{task_names[i]}: {str(res)}")

            # Deduplicate and merge
            result.candidates = self._deduplicate_candidates(all_candidates)

        return result


# Convenience function
async def test_contact_search(company_name: str, domain: str | None = None):
    """Test contact search"""
    engine = ContactSearchEngine()
    result = await engine.search(company_name, domain)
    print(f"Company: {company_name}")
    print(f"Found {len(result.candidates)} candidates")
    for c in result.candidates[:5]:
        print(f"  - {c.name or 'Unknown'}: {c.title or 'No title'}")
        print(f"    Email: {c.email or 'None'}")
        print(f"    LinkedIn: {c.linkedin_url or 'None'}")
        print(f"    Confidence: {c.confidence}")
    return result
