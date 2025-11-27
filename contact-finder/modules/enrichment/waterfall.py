"""
Enrichment Waterfall
Cost-optimized enrichment pipeline for contacts
"""

import asyncio
from dataclasses import dataclass, field
from typing import Any

from .blitz import BlitzClient
from .leadmagic import LeadMagicClient
from .scrapin import ScrapinClient
from ..validation.email_validator import EmailOrigin, EmailValidator, EmailValidationResult
from ..validation.linkedin_normalizer import normalize_linkedin_url


@dataclass
class EnrichedContact:
    """Fully enriched contact"""
    # Identity
    name: str | None
    first_name: str | None
    last_name: str | None
    title: str | None

    # Contact info
    email: str | None
    email_verified: bool | None
    email_origin: EmailOrigin | None
    is_catch_all: bool | None

    phone: str | None
    phone_verified: bool | None

    # LinkedIn
    linkedin_url: str | None  # Normalized linkedin.com/in/xxx

    # Metadata
    company_name: str
    domain: str | None
    confidence: float  # 0-100
    enrichment_sources: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    cost_credits: float = 0.0
    raw_data: dict = field(default_factory=dict)


@dataclass
class EnrichmentResult:
    """Result of enrichment waterfall"""
    contact: EnrichedContact
    success: bool
    errors: list[str] = field(default_factory=list)
    cost_breakdown: dict = field(default_factory=dict)


class EnrichmentWaterfall:
    """
    Cost-optimized enrichment waterfall.

    Priority (cheapest first):
    1. Scrapin (FREE) - LinkedIn profile enrichment
    2. Blitz (1 credit) - Email enrichment
    3. LeadMagic (pay if found) - Email backup
    4. Blitz phone (3 credits) - Only if requested

    The waterfall stops as soon as we have what we need.
    """

    def __init__(
        self,
        scrapin_client: ScrapinClient | None = None,
        blitz_client: BlitzClient | None = None,
        leadmagic_client: LeadMagicClient | None = None,
        email_validator: EmailValidator | None = None
    ):
        self.scrapin = scrapin_client
        self.blitz = blitz_client
        self.leadmagic = leadmagic_client
        self.email_validator = email_validator or EmailValidator()

    async def _enrich_via_scrapin(
        self,
        linkedin_url: str | None,
        first_name: str | None = None,
        last_name: str | None = None,
        company_name: str | None = None
    ) -> dict | None:
        """
        Try to enrich via Scrapin (FREE).

        If we have LinkedIn URL, get profile directly.
        Otherwise try person matching.
        """
        if not self.scrapin:
            return None

        try:
            if linkedin_url:
                # Get profile directly
                result = await self.scrapin.get_person_profile(linkedin_url)
                if result.name:
                    return {
                        "name": result.name,
                        "first_name": result.first_name,
                        "last_name": result.last_name,
                        "title": result.title,
                        "email": result.email,
                        "phone": result.phone,
                        "linkedin_url": normalize_linkedin_url(result.linkedin_url),
                        "source": "scrapin_profile"
                    }
            elif first_name and company_name:
                # Try person matching
                result = await self.scrapin.match_person(
                    first_name=first_name,
                    last_name=last_name,
                    company_name=company_name
                )
                if result.name:
                    return {
                        "name": result.name,
                        "first_name": result.first_name,
                        "last_name": result.last_name,
                        "title": result.title,
                        "email": result.email,
                        "phone": result.phone,
                        "linkedin_url": normalize_linkedin_url(result.linkedin_url),
                        "source": "scrapin_match"
                    }
        except Exception:
            pass

        return None

    async def _enrich_email_via_scrapin(
        self,
        first_name: str,
        last_name: str | None,
        domain: str
    ) -> dict | None:
        """Try to find email via Scrapin (FREE)"""
        if not self.scrapin:
            return None

        try:
            result = await self.scrapin.find_email(
                first_name=first_name,
                last_name=last_name,
                domain=domain
            )
            if result.email:
                return {
                    "email": result.email,
                    "verified": result.verified,
                    "source": "scrapin_email"
                }
        except Exception:
            pass

        return None

    async def _enrich_email_via_blitz(
        self,
        first_name: str,
        last_name: str | None,
        domain: str | None = None,
        company_name: str | None = None
    ) -> dict | None:
        """Try to find email via Blitz (1 credit)"""
        if not self.blitz:
            return None

        try:
            result = await self.blitz.enrich_email(
                first_name=first_name,
                last_name=last_name,
                domain=domain,
                company_name=company_name
            )
            if result.email:
                return {
                    "email": result.email,
                    "verified": result.email_verified,
                    "source": "blitz_email",
                    "cost": 1.0
                }
        except Exception:
            pass

        return None

    async def _enrich_email_via_leadmagic(
        self,
        first_name: str,
        last_name: str | None,
        domain: str | None = None,
        company_name: str | None = None
    ) -> dict | None:
        """Try to find email via LeadMagic (pay if found)"""
        if not self.leadmagic:
            return None

        try:
            result = await self.leadmagic.find_email(
                first_name=first_name,
                last_name=last_name,
                domain=domain,
                company_name=company_name
            )
            if result.email:
                return {
                    "email": result.email,
                    "verified": result.confidence == "high",
                    "source": "leadmagic_email",
                    "cost": 1.0 if result.email else 0.0  # Pay if found
                }
        except Exception:
            pass

        return None

    async def _enrich_phone_via_blitz(
        self,
        first_name: str,
        last_name: str | None,
        domain: str | None = None,
        company_name: str | None = None
    ) -> dict | None:
        """Try to find phone via Blitz (3 credits)"""
        if not self.blitz:
            return None

        try:
            result = await self.blitz.enrich_phone(
                first_name=first_name,
                last_name=last_name,
                domain=domain,
                company_name=company_name
            )
            if result.phone:
                return {
                    "phone": result.phone,
                    "verified": result.phone_verified,
                    "source": "blitz_phone",
                    "cost": 3.0
                }
        except Exception:
            pass

        return None

    async def _validate_email(self, email: str, origin: EmailOrigin) -> EmailValidationResult:
        """Validate email syntax and optionally deliverability"""
        return await self.email_validator.validate(
            email=email,
            origin=origin,
            check_deliverability=self.blitz is not None
        )

    async def enrich(
        self,
        name: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        title: str | None = None,
        email: str | None = None,
        linkedin_url: str | None = None,
        company_name: str | None = None,
        domain: str | None = None,
        existing_evidence: list[str] | None = None,
        include_phone: bool = False,
        skip_if_email_exists: bool = True
    ) -> EnrichmentResult:
        """
        Enrich a contact using the waterfall.

        Args:
            name: Full name
            first_name: First name (preferred over parsing full name)
            last_name: Last name
            title: Job title
            email: Existing email (if any)
            linkedin_url: LinkedIn URL (normalized or raw)
            company_name: Company name
            domain: Company domain
            existing_evidence: Evidence from discovery phase
            include_phone: Whether to enrich phone (costs 3 credits)
            skip_if_email_exists: Skip email enrichment if we already have one

        Returns:
            EnrichmentResult with enriched contact
        """
        # Normalize LinkedIn URL
        linkedin_url = normalize_linkedin_url(linkedin_url)

        # Parse name if not split
        if name and not first_name:
            parts = name.split()
            if len(parts) >= 2:
                first_name = parts[0]
                last_name = " ".join(parts[1:])
            elif parts:
                first_name = parts[0]

        # Initialize result
        enriched = EnrichedContact(
            name=name,
            first_name=first_name,
            last_name=last_name,
            title=title,
            email=email,
            email_verified=None,
            email_origin=None,
            is_catch_all=None,
            phone=None,
            phone_verified=None,
            linkedin_url=linkedin_url,
            company_name=company_name or "",
            domain=domain,
            confidence=50.0,
            enrichment_sources=[],
            evidence=list(existing_evidence or []),
            cost_credits=0.0,
            raw_data={}
        )

        errors = []
        cost_breakdown = {}

        # Step 1: Scrapin enrichment (FREE)
        if self.scrapin and (linkedin_url or (first_name and company_name)):
            scrapin_data = await self._enrich_via_scrapin(
                linkedin_url=linkedin_url,
                first_name=first_name,
                last_name=last_name,
                company_name=company_name
            )

            if scrapin_data:
                enriched.enrichment_sources.append("scrapin")
                enriched.evidence.append(f"Scrapin profile enrichment: {scrapin_data.get('source')}")

                # Fill in missing data
                if not enriched.name and scrapin_data.get("name"):
                    enriched.name = scrapin_data["name"]
                if not enriched.first_name and scrapin_data.get("first_name"):
                    enriched.first_name = scrapin_data["first_name"]
                if not enriched.last_name and scrapin_data.get("last_name"):
                    enriched.last_name = scrapin_data["last_name"]
                if not enriched.title and scrapin_data.get("title"):
                    enriched.title = scrapin_data["title"]
                if not enriched.linkedin_url and scrapin_data.get("linkedin_url"):
                    enriched.linkedin_url = scrapin_data["linkedin_url"]
                if not enriched.email and scrapin_data.get("email"):
                    enriched.email = scrapin_data["email"]
                    enriched.email_origin = EmailOrigin.LINKEDIN_ENRICHED
                if not enriched.phone and scrapin_data.get("phone"):
                    enriched.phone = scrapin_data["phone"]

                cost_breakdown["scrapin"] = 0.0

        # Step 2: Email enrichment (if needed)
        need_email = not enriched.email or not skip_if_email_exists

        if need_email and enriched.first_name and domain:
            # Try Scrapin email first (FREE)
            email_data = await self._enrich_email_via_scrapin(
                first_name=enriched.first_name,
                last_name=enriched.last_name,
                domain=domain
            )

            if email_data:
                enriched.email = email_data["email"]
                enriched.email_verified = email_data.get("verified")
                enriched.email_origin = EmailOrigin.LINKEDIN_ENRICHED
                enriched.enrichment_sources.append("scrapin_email")
                enriched.evidence.append(f"Email from Scrapin: {email_data['email']}")
                cost_breakdown["scrapin_email"] = 0.0
            else:
                # Try Blitz email (1 credit)
                email_data = await self._enrich_email_via_blitz(
                    first_name=enriched.first_name,
                    last_name=enriched.last_name,
                    domain=domain,
                    company_name=company_name
                )

                if email_data:
                    enriched.email = email_data["email"]
                    enriched.email_verified = email_data.get("verified")
                    enriched.email_origin = EmailOrigin.ENRICHED_API
                    enriched.enrichment_sources.append("blitz_email")
                    enriched.evidence.append(f"Email from Blitz: {email_data['email']}")
                    enriched.cost_credits += email_data.get("cost", 1.0)
                    cost_breakdown["blitz_email"] = email_data.get("cost", 1.0)
                else:
                    # Try LeadMagic as last resort (pay if found)
                    email_data = await self._enrich_email_via_leadmagic(
                        first_name=enriched.first_name,
                        last_name=enriched.last_name,
                        domain=domain,
                        company_name=company_name
                    )

                    if email_data:
                        enriched.email = email_data["email"]
                        enriched.email_verified = email_data.get("verified")
                        enriched.email_origin = EmailOrigin.ENRICHED_API
                        enriched.enrichment_sources.append("leadmagic_email")
                        enriched.evidence.append(f"Email from LeadMagic: {email_data['email']}")
                        enriched.cost_credits += email_data.get("cost", 1.0)
                        cost_breakdown["leadmagic_email"] = email_data.get("cost", 1.0)

        # Step 3: Phone enrichment (if requested, 3 credits)
        if include_phone and not enriched.phone and enriched.first_name:
            phone_data = await self._enrich_phone_via_blitz(
                first_name=enriched.first_name,
                last_name=enriched.last_name,
                domain=domain,
                company_name=company_name
            )

            if phone_data:
                enriched.phone = phone_data["phone"]
                enriched.phone_verified = phone_data.get("verified")
                enriched.enrichment_sources.append("blitz_phone")
                enriched.evidence.append(f"Phone from Blitz: {phone_data['phone']}")
                enriched.cost_credits += phone_data.get("cost", 3.0)
                cost_breakdown["blitz_phone"] = phone_data.get("cost", 3.0)

        # Step 4: Email validation
        if enriched.email:
            validation = await self._validate_email(
                enriched.email,
                enriched.email_origin or EmailOrigin.ENRICHED_API
            )
            enriched.is_catch_all = validation.is_catch_all

            # Update verified status if we did deliverability check
            if validation.is_deliverable is not None:
                enriched.email_verified = validation.is_deliverable

        # Calculate final confidence
        enriched.confidence = self._calculate_confidence(enriched)

        return EnrichmentResult(
            contact=enriched,
            success=bool(enriched.email or enriched.linkedin_url),
            errors=errors,
            cost_breakdown=cost_breakdown
        )

    def _calculate_confidence(self, contact: EnrichedContact) -> float:
        """Calculate confidence score for enriched contact"""
        score = 30.0  # Base score

        # Name components
        if contact.name:
            score += 10
        if contact.first_name and contact.last_name:
            score += 5

        # Title
        if contact.title:
            score += 10

        # Email
        if contact.email:
            score += 20
            if contact.email_verified:
                score += 15
            elif contact.is_catch_all:
                score -= 5  # Catch-all reduces confidence

        # LinkedIn
        if contact.linkedin_url:
            score += 15

        # Multiple sources corroborate
        if len(contact.enrichment_sources) > 1:
            score += 10

        return max(0, min(100, score))

    async def batch_enrich(
        self,
        contacts: list[dict],
        company_name: str,
        domain: str | None = None,
        include_phone: bool = False,
        max_concurrent: int = 10
    ) -> list[EnrichmentResult]:
        """
        Enrich multiple contacts in parallel.

        Args:
            contacts: List of contact dicts with name, linkedin_url, etc.
            company_name: Company name
            domain: Company domain
            include_phone: Whether to enrich phones
            max_concurrent: Max concurrent enrichments

        Returns:
            List of EnrichmentResult
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def enrich_one(contact: dict) -> EnrichmentResult:
            async with semaphore:
                return await self.enrich(
                    name=contact.get("name"),
                    first_name=contact.get("first_name"),
                    last_name=contact.get("last_name"),
                    title=contact.get("title"),
                    email=contact.get("email"),
                    linkedin_url=contact.get("linkedin_url"),
                    company_name=company_name,
                    domain=domain,
                    existing_evidence=contact.get("evidence"),
                    include_phone=include_phone
                )

        tasks = [enrich_one(c) for c in contacts]
        return await asyncio.gather(*tasks)


# Convenience function
async def test_enrichment_waterfall(
    name: str,
    company_name: str,
    domain: str | None = None,
    linkedin_url: str | None = None
):
    """Test enrichment waterfall"""
    waterfall = EnrichmentWaterfall()
    result = await waterfall.enrich(
        name=name,
        company_name=company_name,
        domain=domain,
        linkedin_url=linkedin_url
    )

    print(f"Enriched: {result.contact.name}")
    print(f"Email: {result.contact.email} (verified: {result.contact.email_verified})")
    print(f"LinkedIn: {result.contact.linkedin_url}")
    print(f"Confidence: {result.contact.confidence}")
    print(f"Sources: {result.contact.enrichment_sources}")
    print(f"Cost: {result.contact.cost_credits} credits")
    return result
