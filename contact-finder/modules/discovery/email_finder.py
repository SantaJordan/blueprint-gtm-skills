"""
Email Finder Service
Orchestrates email permutation generation and verification using MillionVerifier
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Optional

from .email_permutator import (
    generate_email_permutations,
    parse_name,
    NameComponents
)
from ..validation.million_verifier import (
    MillionVerifierClient,
    VerificationResult,
    EmailResult,
    EmailQuality
)

logger = logging.getLogger(__name__)


@dataclass
class EmailCandidate:
    """An email candidate with verification results"""
    email: str
    verification: Optional[VerificationResult] = None
    source: str = "permutation"  # permutation, discovered, input

    @property
    def is_verified(self) -> bool:
        return self.verification is not None

    @property
    def is_valid(self) -> bool:
        if not self.verification:
            return False
        return self.verification.is_valid

    @property
    def is_deliverable(self) -> bool:
        if not self.verification:
            return False
        return self.verification.is_deliverable

    @property
    def confidence(self) -> int:
        if not self.verification:
            return 0
        return self.verification.confidence_score

    @property
    def result_type(self) -> Optional[str]:
        if not self.verification:
            return None
        return self.verification.result.value


@dataclass
class EmailFinderResult:
    """Result from email finding operation"""
    # Best email found
    best_email: Optional[str] = None
    best_verification: Optional[VerificationResult] = None

    # All candidates checked
    candidates_checked: list[EmailCandidate] = field(default_factory=list)

    # Statistics
    permutations_generated: int = 0
    existing_emails_checked: int = 0
    total_verifications: int = 0
    credits_used: int = 0

    # Name parsing
    name_components: Optional[NameComponents] = None
    name_rejected: bool = False
    name_rejection_reason: Optional[str] = None

    @property
    def found_valid_email(self) -> bool:
        return self.best_email is not None and self.best_verification is not None

    @property
    def best_result_type(self) -> Optional[str]:
        if not self.best_verification:
            return None
        return self.best_verification.result.value

    @property
    def best_confidence(self) -> int:
        if not self.best_verification:
            return 0
        return self.best_verification.confidence_score


class EmailFinder:
    """
    Service for finding verified email addresses.

    Flow:
    1. Parse name into components
    2. Generate email permutations
    3. Verify existing emails (if any)
    4. Verify all permutations
    5. Select best email based on verification results
    """

    def __init__(
        self,
        million_verifier_api_key: Optional[str] = None,
        max_concurrent: int = 10,
        verification_timeout: int = 20
    ):
        """
        Initialize EmailFinder.

        Args:
            million_verifier_api_key: API key for MillionVerifier
            max_concurrent: Max concurrent verification requests
            verification_timeout: Timeout per verification in seconds
        """
        self.verifier = MillionVerifierClient(
            api_key=million_verifier_api_key,
            timeout_seconds=verification_timeout,
            max_concurrent=max_concurrent
        )

    async def close(self):
        """Close the verifier client"""
        await self.verifier.close()

    async def find_email(
        self,
        full_name: str,
        domain: str,
        existing_emails: Optional[list[str]] = None,
        skip_permutations: bool = False
    ) -> EmailFinderResult:
        """
        Find and verify the best email for a person at a company.

        Args:
            full_name: Person's full name (e.g., "John Smith")
            domain: Company domain (e.g., "example.com")
            existing_emails: Pre-discovered emails to verify first
            skip_permutations: If True, only verify existing emails

        Returns:
            EmailFinderResult with best email and all candidates
        """
        result = EmailFinderResult()
        existing_emails = existing_emails or []

        # Parse name
        name_components = parse_name(full_name)
        result.name_components = name_components

        if not name_components.is_valid:
            result.name_rejected = True
            result.name_rejection_reason = name_components.rejection_reason
            logger.debug(f"Name rejected for permutation: {full_name} - {name_components.rejection_reason}")

            # Still verify existing emails even if name is invalid
            if existing_emails:
                return await self._verify_existing_only(existing_emails, result)
            return result

        # Generate permutations
        if not skip_permutations:
            permutations = generate_email_permutations(full_name, domain)
            result.permutations_generated = len(permutations)
        else:
            permutations = []

        # Collect all emails to verify (existing + permutations)
        all_emails = []
        email_sources = {}

        # Add existing emails first (they get priority in selection)
        for email in existing_emails:
            email_lower = email.lower().strip()
            if email_lower and email_lower not in email_sources:
                all_emails.append(email_lower)
                email_sources[email_lower] = "discovered"
                result.existing_emails_checked += 1

        # Add permutations
        for email in permutations:
            email_lower = email.lower()
            if email_lower not in email_sources:
                all_emails.append(email_lower)
                email_sources[email_lower] = "permutation"

        if not all_emails:
            return result

        # Verify all emails concurrently
        logger.debug(f"Verifying {len(all_emails)} emails for {full_name}")
        verifications = await self.verifier.verify_emails(all_emails)
        result.total_verifications = len(verifications)
        result.credits_used = len(verifications)

        # Build candidate list
        for email, verification in zip(all_emails, verifications):
            candidate = EmailCandidate(
                email=email,
                verification=verification,
                source=email_sources[email]
            )
            result.candidates_checked.append(candidate)

        # Select best email
        self._select_best_email(result)

        return result

    async def _verify_existing_only(
        self,
        existing_emails: list[str],
        result: EmailFinderResult
    ) -> EmailFinderResult:
        """Verify only existing emails when name is invalid"""
        emails = [e.lower().strip() for e in existing_emails if e]
        if not emails:
            return result

        result.existing_emails_checked = len(emails)
        verifications = await self.verifier.verify_emails(emails)
        result.total_verifications = len(verifications)
        result.credits_used = len(verifications)

        for email, verification in zip(emails, verifications):
            candidate = EmailCandidate(
                email=email,
                verification=verification,
                source="discovered"
            )
            result.candidates_checked.append(candidate)

        self._select_best_email(result)
        return result

    def _select_best_email(self, result: EmailFinderResult):
        """
        Select the best email from candidates.

        Priority:
        1. result=ok, quality=good (confidence 100)
        2. result=ok, quality=risky (confidence 70)
        3. result=catch_all (confidence 60)
        4. Discovered emails get slight preference over permutations

        Rejected:
        - result=invalid
        - result=disposable
        - result=unknown (unless nothing else)
        """
        if not result.candidates_checked:
            return

        # Score each candidate
        scored = []
        for candidate in result.candidates_checked:
            if not candidate.verification:
                continue

            v = candidate.verification

            # Skip definitely bad emails
            if v.result in (EmailResult.INVALID, EmailResult.DISPOSABLE):
                continue

            # Calculate score
            score = v.confidence_score

            # Bonus for discovered emails (slight preference)
            if candidate.source == "discovered":
                score += 5

            # Penalty for role accounts
            if v.is_role:
                score -= 10

            # Penalty for free email providers in business context
            if v.is_free:
                score -= 5

            scored.append((score, candidate))

        if not scored:
            # No valid emails found - try unknown as last resort
            for candidate in result.candidates_checked:
                if candidate.verification and candidate.verification.result == EmailResult.UNKNOWN:
                    if candidate.source == "discovered":
                        result.best_email = candidate.email
                        result.best_verification = candidate.verification
                        return
            return

        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)

        # Select best
        best_score, best_candidate = scored[0]
        result.best_email = best_candidate.email
        result.best_verification = best_candidate.verification

    async def verify_single(self, email: str) -> VerificationResult:
        """Verify a single email address"""
        return await self.verifier.verify_email(email)

    @property
    def credits_used(self) -> int:
        """Total credits used by this finder"""
        return self.verifier.credits_used


async def find_email_for_contact(
    full_name: str,
    domain: str,
    existing_email: Optional[str] = None,
    api_key: Optional[str] = None
) -> EmailFinderResult:
    """
    Convenience function to find email for a single contact.

    Args:
        full_name: Person's full name
        domain: Company domain
        existing_email: Optional existing email to verify
        api_key: MillionVerifier API key

    Returns:
        EmailFinderResult
    """
    finder = EmailFinder(million_verifier_api_key=api_key)
    try:
        existing = [existing_email] if existing_email else []
        return await finder.find_email(full_name, domain, existing)
    finally:
        await finder.close()
