"""
Email Validation Module
Validate email addresses and track origin/confidence
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any


class EmailOrigin(Enum):
    """Where the email was found/how it was obtained"""
    SITE_OBSERVED = "site_observed"      # Highest trust: seen directly on website
    DIRECTORY_OBSERVED = "directory"     # Seen on directory (Yelp, BBB, etc.)
    MAPS_OBSERVED = "maps"               # From Google Maps/Places
    ENRICHED_API = "enriched"            # From API (Blitz, LeadMagic, Scrapin)
    LINKEDIN_ENRICHED = "linkedin"       # From LinkedIn enrichment
    PATTERN_GUESS = "pattern_guess"      # Guessed from pattern - LOWEST trust


@dataclass
class EmailValidationResult:
    """Result of email validation"""
    email: str
    is_valid_syntax: bool
    is_deliverable: bool | None  # None if not checked
    is_catch_all: bool | None    # None if not checked
    has_mx_record: bool | None   # None if not checked
    is_role_account: bool        # info@, support@, etc.
    is_personal_domain: bool     # gmail, yahoo, etc.
    origin: EmailOrigin
    confidence: float            # 0-100
    validation_source: str | None  # Which service validated


# Email regex pattern
EMAIL_REGEX = re.compile(
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
)

# Role account prefixes
ROLE_PREFIXES = {
    'info', 'contact', 'support', 'help', 'sales', 'marketing',
    'admin', 'administrator', 'webmaster', 'postmaster',
    'noreply', 'no-reply', 'donotreply', 'do-not-reply',
    'office', 'team', 'hello', 'hi', 'general', 'inquiries',
    'billing', 'accounts', 'hr', 'jobs', 'careers', 'press',
    'media', 'legal', 'privacy', 'security', 'abuse',
}

# Personal email domains
PERSONAL_DOMAINS = {
    'gmail.com', 'googlemail.com',
    'yahoo.com', 'yahoo.co.uk', 'ymail.com',
    'outlook.com', 'hotmail.com', 'live.com', 'msn.com',
    'aol.com', 'icloud.com', 'me.com', 'mac.com',
    'protonmail.com', 'proton.me',
    'mail.com', 'email.com',
}


class EmailValidator:
    """Validate and score email addresses"""

    def __init__(self, blitz_client=None):
        """
        Initialize validator with optional Blitz client for deliverability checks.

        Args:
            blitz_client: Optional BlitzClient for catch-all detection
        """
        self.blitz_client = blitz_client

    def validate_syntax(self, email: str) -> bool:
        """Check if email has valid syntax"""
        if not email:
            return False
        return bool(EMAIL_REGEX.match(email.lower().strip()))

    def is_role_account(self, email: str) -> bool:
        """Check if email is a role/generic account"""
        if not email:
            return False

        local_part = email.lower().split('@')[0]

        # Check exact matches
        if local_part in ROLE_PREFIXES:
            return True

        # Check prefixes
        for prefix in ROLE_PREFIXES:
            if local_part.startswith(f"{prefix}_") or local_part.startswith(f"{prefix}-"):
                return True
            if local_part.startswith(f"{prefix}."):
                return True

        return False

    def is_personal_domain(self, email: str) -> bool:
        """Check if email uses a personal/free email domain"""
        if not email:
            return False

        domain = email.lower().split('@')[1] if '@' in email else ""
        return domain in PERSONAL_DOMAINS

    async def validate_deliverability(self, email: str) -> tuple[bool | None, bool | None]:
        """
        Check email deliverability using Blitz API.

        Returns:
            Tuple of (is_deliverable, is_catch_all)
        """
        if not self.blitz_client:
            return None, None

        try:
            result = await self.blitz_client.validate_email(email)
            return result.valid, result.is_catch_all
        except Exception:
            return None, None

    def calculate_confidence(
        self,
        origin: EmailOrigin,
        is_valid_syntax: bool,
        is_deliverable: bool | None,
        is_catch_all: bool | None,
        is_role_account: bool,
        is_personal_domain: bool
    ) -> float:
        """
        Calculate confidence score for an email.

        Args:
            origin: Where the email came from
            is_valid_syntax: Passes syntax check
            is_deliverable: Verified deliverable (or None)
            is_catch_all: Is catch-all domain (or None)
            is_role_account: Is a role/generic account
            is_personal_domain: Uses Gmail, Yahoo, etc.

        Returns:
            Confidence score 0-100
        """
        if not is_valid_syntax:
            return 0

        # Base score by origin
        origin_scores = {
            EmailOrigin.SITE_OBSERVED: 90,
            EmailOrigin.MAPS_OBSERVED: 85,
            EmailOrigin.DIRECTORY_OBSERVED: 80,
            EmailOrigin.ENRICHED_API: 75,
            EmailOrigin.LINKEDIN_ENRICHED: 70,
            EmailOrigin.PATTERN_GUESS: 40,
        }
        score = origin_scores.get(origin, 50)

        # Adjust based on validation
        if is_deliverable is True:
            score += 10
        elif is_deliverable is False:
            score -= 40  # Major penalty for known-bad email

        if is_catch_all is True:
            score -= 15  # Can't verify actual deliverability

        if is_role_account:
            score -= 10  # Less likely to reach a person

        # Personal domains are okay for SMBs
        if is_personal_domain:
            # Only penalize if we expected a corporate email
            pass

        return max(0, min(100, score))

    async def validate(
        self,
        email: str,
        origin: EmailOrigin,
        check_deliverability: bool = False
    ) -> EmailValidationResult:
        """
        Validate an email address comprehensively.

        Args:
            email: Email address to validate
            origin: Where the email was obtained
            check_deliverability: Whether to check with Blitz API

        Returns:
            EmailValidationResult with all validation data
        """
        email = email.lower().strip()

        is_valid_syntax = self.validate_syntax(email)
        is_role = self.is_role_account(email)
        is_personal = self.is_personal_domain(email)

        is_deliverable = None
        is_catch_all = None
        validation_source = None

        if check_deliverability and is_valid_syntax:
            is_deliverable, is_catch_all = await self.validate_deliverability(email)
            if is_deliverable is not None:
                validation_source = "blitz"

        confidence = self.calculate_confidence(
            origin=origin,
            is_valid_syntax=is_valid_syntax,
            is_deliverable=is_deliverable,
            is_catch_all=is_catch_all,
            is_role_account=is_role,
            is_personal_domain=is_personal
        )

        return EmailValidationResult(
            email=email,
            is_valid_syntax=is_valid_syntax,
            is_deliverable=is_deliverable,
            is_catch_all=is_catch_all,
            has_mx_record=None,  # Could add DNS check
            is_role_account=is_role,
            is_personal_domain=is_personal,
            origin=origin,
            confidence=confidence,
            validation_source=validation_source
        )


def quick_validate(email: str, origin: EmailOrigin = EmailOrigin.ENRICHED_API) -> EmailValidationResult:
    """Quick synchronous validation without deliverability check"""
    validator = EmailValidator()
    email = email.lower().strip()

    is_valid_syntax = validator.validate_syntax(email)
    is_role = validator.is_role_account(email)
    is_personal = validator.is_personal_domain(email)

    confidence = validator.calculate_confidence(
        origin=origin,
        is_valid_syntax=is_valid_syntax,
        is_deliverable=None,
        is_catch_all=None,
        is_role_account=is_role,
        is_personal_domain=is_personal
    )

    return EmailValidationResult(
        email=email,
        is_valid_syntax=is_valid_syntax,
        is_deliverable=None,
        is_catch_all=None,
        has_mx_record=None,
        is_role_account=is_role,
        is_personal_domain=is_personal,
        origin=origin,
        confidence=confidence,
        validation_source=None
    )
