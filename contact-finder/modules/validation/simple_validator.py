"""
Simple Contact Validator - Rule-based validation for SMB contacts

No LLM needed! Owner title + company match = good enough.
"""

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ValidationResult:
    """Result of contact validation"""
    is_valid: bool
    confidence: float  # 0-100
    score_breakdown: dict = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)
    method: str = "simple_rules"


@dataclass
class ContactCandidate:
    """A contact candidate to validate"""
    name: str | None = None
    email: str | None = None
    title: str | None = None
    linkedin_url: str | None = None
    phone: str | None = None
    company_domain: str | None = None
    sources: list[str] = field(default_factory=list)

    # SMB-specific fields for enhanced validation
    google_maps_place_id: str | None = None
    google_maps_reviews: int | None = None
    google_maps_rating: float | None = None
    facebook_url: str | None = None
    instagram_url: str | None = None
    twitter_url: str | None = None
    address: str | None = None


class SimpleContactValidator:
    """
    SMB-appropriate validation using simple rules.

    No LLM needed - owner title + company match is good enough.

    RELAXED SCORING (user requirement: just find person name, not require email/phone):
    - Owner/founder title: +40 points
    - 2+ sources agree: +30 points
    - Has LinkedIn URL: +20 points (INCREASED - secondary goal)
    - Has Facebook URL: +15 points (SMB owners use Facebook)
    - Email matches domain: +10 points (nice-to-have)
    - Google Maps high reviews: +10 points
    - Has phone number: +5 points (nice-to-have)
    - Social presence (FB/IG): +10 points

    Source-based scoring:
    - google_maps: +35 points (structured, verified)
    - google_maps_owner: +40 points (explicit owner field)
    - openweb_contacts: +25 points (structured website scrape)
    - website_schema: +25 points (Schema.org data)
    - website_scrape: +15 points (page content extraction)
    - serper_osint: +10 points (text extraction)
    - social_links: +20 points (found LinkedIn via social search)
    - social_links_fb: +15 points (found Facebook via social search)

    Threshold: 50 points = valid

    CONTENT VALIDATION: Reject if name contains company patterns (LLC, Inc, etc.)
    """

    # Source-based scoring for SMBs
    SOURCE_SCORES = {
        "google_maps": 35,           # Structured Google Maps data
        "google_maps_owner": 40,     # Explicit owner field from GMaps
        "openweb_contacts": 25,      # OpenWeb Ninja website scrape
        "website_schema": 25,        # Schema.org structured data
        "website_scrape": 15,        # Page content extraction
        "serper_osint": 10,          # Text extraction from search
        "input_csv": 20,             # From input file (assumed valid)
        "social_links": 20,          # Found LinkedIn via social search
        "social_links_fb": 15,       # Found Facebook via social search
    }

    # SMB-focused bonus points (RELAXED - email/phone are nice-to-have, not required)
    REVIEW_BONUS = 10              # Google Maps reviews > 50
    PHONE_BONUS = 5                # Has phone (reduced from 15 - nice-to-have)
    SOCIAL_BONUS = 10              # Has FB/Instagram presence
    LINKEDIN_BONUS = 20            # Has LinkedIn URL (INCREASED - secondary goal)
    FACEBOOK_BONUS = 15            # Has Facebook URL (SMB owners use FB)

    # Patterns that indicate company name (not person name)
    COMPANY_NAME_PATTERNS = [
        "LLC", "L.L.C.", "Inc", "Inc.", "Corp", "Corp.", "Corporation",
        "Ltd", "Ltd.", "LTD", "Company", "Co.", "& Co", "Services",
        "Enterprises", "Solutions", "Group", "Holdings", "Partners",
        " & ", " and ", "Associates", "Consulting", "Agency",
    ]

    # Owner-related titles (case insensitive)
    OWNER_TITLES = [
        "owner",
        "founder",
        "co-founder",
        "president",
        "ceo",
        "chief executive",
        "proprietor",
        "principal",
        "managing partner",
        "general manager",
        "gm",
        "operator",
        "head",
        "director",
    ]

    # Strong owner titles (higher confidence)
    STRONG_OWNER_TITLES = [
        "owner",
        "founder",
        "co-founder",
        "president",
        "ceo",
        "proprietor",
    ]

    def __init__(self, min_confidence: int = 50):
        self.min_confidence = min_confidence

    def _is_owner_title(self, title: str | None) -> tuple[bool, bool]:
        """
        Check if title indicates owner/decision-maker.

        Returns:
            (is_owner, is_strong_owner)
        """
        if not title:
            return False, False

        title_lower = title.lower()

        # Check strong titles first
        for strong in self.STRONG_OWNER_TITLES:
            if strong in title_lower:
                return True, True

        # Check regular owner titles
        for owner in self.OWNER_TITLES:
            if owner in title_lower:
                return True, False

        return False, False

    def _email_matches_domain(self, email: str | None, domain: str | None) -> bool:
        """Check if email domain matches company domain"""
        if not email or not domain:
            return False

        try:
            email_domain = email.split("@")[1].lower()
            company_domain = domain.lower().replace("www.", "")

            # Exact match
            if email_domain == company_domain:
                return True

            # Domain without TLD
            email_base = email_domain.split(".")[0]
            company_base = company_domain.split(".")[0]

            if email_base == company_base:
                return True

            return False
        except:
            return False

    def _is_personal_email(self, email: str | None) -> bool:
        """Check if email is a personal provider (might still be owner)"""
        if not email:
            return False

        personal_domains = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "aol.com"]
        email_domain = email.split("@")[1].lower() if "@" in email else ""

        return email_domain in personal_domains

    def _is_company_name(self, name: str | None) -> tuple[bool, str | None]:
        """
        Check if a name looks like a company name instead of a person name.

        Returns:
            (is_company, matched_pattern) - True if name appears to be a company name
        """
        if not name:
            return False, None

        name_upper = name.upper()

        # Check for company patterns
        for pattern in self.COMPANY_NAME_PATTERNS:
            if pattern.upper() in name_upper:
                return True, pattern

        # Check for typical company structure (lacks first+last name structure)
        # e.g., "ABC Plumbing" vs "John Smith"
        words = name.split()
        if len(words) >= 1:
            # All caps is typically a company
            if name == name.upper() and len(name) > 5:
                return True, "ALL_CAPS"

            # Single word that's not a common first name is likely company
            # (but don't reject short single names like "Joe")

        return False, None

    def validate(self, contact: ContactCandidate) -> ValidationResult:
        """
        Validate a contact using simple rules.

        Args:
            contact: ContactCandidate to validate

        Returns:
            ValidationResult with score and reasons
        """
        score = 0
        breakdown = {}
        reasons = []

        # 0. CONTENT VALIDATION: Reject company names in person field
        is_company, pattern = self._is_company_name(contact.name)
        if is_company:
            return ValidationResult(
                is_valid=False,
                confidence=0,
                score_breakdown={"rejected_company_name": -100},
                reasons=[f"Name appears to be company name (matched: '{pattern}'): {contact.name}"],
                method="simple_rules"
            )

        # 1. Owner/founder title (up to 40 points)
        is_owner, is_strong = self._is_owner_title(contact.title)
        if is_strong:
            score += 40
            breakdown["title_strong_owner"] = 40
            reasons.append(f"Strong owner title: {contact.title}")
        elif is_owner:
            score += 30
            breakdown["title_owner"] = 30
            reasons.append(f"Owner-related title: {contact.title}")
        elif contact.title:
            score += 10
            breakdown["title_present"] = 10
            reasons.append(f"Has title: {contact.title}")

        # 2. Multiple sources agree (30 points)
        if len(contact.sources) >= 3:
            score += 30
            breakdown["multiple_sources"] = 30
            reasons.append(f"Found in {len(contact.sources)} sources")
        elif len(contact.sources) >= 2:
            score += 20
            breakdown["two_sources"] = 20
            reasons.append(f"Found in {len(contact.sources)} sources")
        elif len(contact.sources) == 1:
            score += 10
            breakdown["one_source"] = 10
            reasons.append(f"Found in 1 source: {contact.sources[0]}")

        # 3. Email (RELAXED - nice-to-have, not required)
        if self._email_matches_domain(contact.email, contact.company_domain):
            score += 10  # Reduced from 20 - nice-to-have
            breakdown["email_matches_domain"] = 10
            reasons.append("Email matches company domain")
        elif contact.email:
            if self._is_personal_email(contact.email):
                # Personal email might be owner's personal address
                score += 5
                breakdown["personal_email"] = 5
                reasons.append("Has personal email (may be owner)")
            else:
                score += 5  # Reduced from 10 - just nice-to-have
                breakdown["has_email"] = 5
                reasons.append("Has email address")

        # 4. Has LinkedIn URL (INCREASED - secondary goal per user requirement)
        if contact.linkedin_url:
            score += self.LINKEDIN_BONUS  # 20 points
            breakdown["has_linkedin"] = self.LINKEDIN_BONUS
            reasons.append("Has LinkedIn profile (secondary goal)")

        # 4b. Has Facebook URL (SMB owners use Facebook)
        if contact.facebook_url:
            score += self.FACEBOOK_BONUS  # 15 points
            breakdown["has_facebook"] = self.FACEBOOK_BONUS
            reasons.append("Has Facebook profile (SMB bonus)")

        # 5. Has phone (REDUCED - nice-to-have)
        if contact.phone:
            score += self.PHONE_BONUS  # 5 points (reduced from 15)
            breakdown["has_phone"] = self.PHONE_BONUS
            reasons.append("Has phone number")

        # 6. Google Maps reviews bonus (10 points if > 20 reviews - SMB appropriate)
        if contact.google_maps_reviews and contact.google_maps_reviews > 20:
            score += self.REVIEW_BONUS
            breakdown["google_maps_reviews"] = self.REVIEW_BONUS
            reasons.append(f"Established business ({contact.google_maps_reviews} Google reviews)")

        # 7. Social presence bonus (10 points for FB/IG)
        has_social = contact.facebook_url or contact.instagram_url or contact.twitter_url
        if has_social:
            score += self.SOCIAL_BONUS
            breakdown["social_presence"] = self.SOCIAL_BONUS
            social_list = []
            if contact.facebook_url:
                social_list.append("Facebook")
            if contact.instagram_url:
                social_list.append("Instagram")
            if contact.twitter_url:
                social_list.append("Twitter")
            reasons.append(f"Has social presence: {', '.join(social_list)}")

        # 8. Source-based scoring (pick highest scoring source)
        source_score = 0
        best_source = None
        for source in contact.sources:
            src_score = self.SOURCE_SCORES.get(source, 5)
            if src_score > source_score:
                source_score = src_score
                best_source = source
        if best_source:
            score += source_score
            breakdown[f"source_{best_source}"] = source_score
            reasons.append(f"Source: {best_source} (+{source_score})")

        # 9. Has name (required, but add points)
        if contact.name:
            # Check if name looks real (first + last)
            name_parts = contact.name.split()
            if len(name_parts) >= 2:
                score += 5
                breakdown["full_name"] = 5
                reasons.append("Has full name")

        # Cap at 100
        score = min(score, 100)

        return ValidationResult(
            is_valid=score >= self.min_confidence,
            confidence=score,
            score_breakdown=breakdown,
            reasons=reasons,
            method="simple_rules"
        )

    def validate_batch(self, contacts: list[ContactCandidate]) -> list[ValidationResult]:
        """Validate multiple contacts"""
        return [self.validate(c) for c in contacts]


# Convenience function to create ContactCandidate from dict
def dict_to_candidate(data: dict, company_domain: str | None = None) -> ContactCandidate:
    """Convert a dict to ContactCandidate"""
    return ContactCandidate(
        name=data.get("name"),
        email=data.get("email"),
        title=data.get("title"),
        linkedin_url=data.get("linkedin_url"),
        phone=data.get("phone"),
        company_domain=company_domain or data.get("company_domain"),
        sources=data.get("sources", []),
        # SMB-specific fields
        google_maps_place_id=data.get("google_maps_place_id"),
        google_maps_reviews=data.get("google_maps_reviews"),
        google_maps_rating=data.get("google_maps_rating"),
        facebook_url=data.get("facebook_url"),
        instagram_url=data.get("instagram_url"),
        twitter_url=data.get("twitter_url"),
        address=data.get("address"),
    )


# Test
def test_simple_validator():
    """Test the validator"""
    validator = SimpleContactValidator()

    # Test 1: Strong owner
    result = validator.validate(ContactCandidate(
        name="John Smith",
        title="Owner",
        email="john@joesplumbing.com",
        company_domain="joesplumbing.com",
        sources=["website", "serper"]
    ))
    print(f"Owner: {result.is_valid}, score={result.confidence}")
    print(f"  Breakdown: {result.score_breakdown}")

    # Test 2: Weak contact
    result = validator.validate(ContactCandidate(
        name="Jane Doe",
        title="Assistant",
        email="jane@gmail.com",
        sources=["serper"]
    ))
    print(f"Assistant: {result.is_valid}, score={result.confidence}")

    # Test 3: No title but good evidence
    result = validator.validate(ContactCandidate(
        name="Bob Jones",
        email="bob@acmeplumbing.com",
        linkedin_url="https://linkedin.com/in/bobjones",
        company_domain="acmeplumbing.com",
        sources=["website", "schema_org", "serper"]
    ))
    print(f"No title: {result.is_valid}, score={result.confidence}")


if __name__ == "__main__":
    test_simple_validator()
