"""
Domain parking detection module
Identifies parked domains and "for sale" pages
"""
import re
from typing import Optional


# Comprehensive list of parking indicators
PARKING_KEYWORDS = [
    'domain for sale',
    'buy this domain',
    'domain name is for sale',
    'purchase this domain',
    'domain available',
    'this domain may be for sale',
    'make an offer',
    'premium domain',
    'parked free',
    'domain parked',
    'courtesy of',
    'is for sale',
    'coming soon',
    'under construction',
    'site coming soon',
    'placeholder page'
]

PARKING_SERVICES = [
    'godaddy',
    'sedo.com',
    'sedo domain',
    'afternic',
    'dan.com',
    'bodis.com',
    'namecheap',
    'dynadot',
    'hugedomains',
    'parkingcrew',
    'sedoparking'
]

PARKING_PATTERNS = [
    r'buy.*domain',
    r'domain.*sale',
    r'for sale.*domain',
    r'premium.*domain',
    r'acquire.*domain',
    r'own.*domain',
    r'register.*domain'
]


def is_parked_domain(text: Optional[str], url: Optional[str] = None) -> tuple[bool, Optional[str]]:
    """
    Detect if content indicates a parked domain or for-sale page

    Args:
        text: Webpage text content or snippet
        url: Optional URL to check for parking service domains

    Returns:
        (is_parked: bool, reason: str or None)
    """
    if not text:
        return False, None

    text_lower = text.lower()

    # Check for exact keyword matches
    for keyword in PARKING_KEYWORDS:
        if keyword in text_lower:
            return True, f"Parking keyword: '{keyword}'"

    # Check for parking service mentions
    for service in PARKING_SERVICES:
        if service in text_lower:
            return True, f"Parking service: '{service}'"

    # Check for parking patterns (regex)
    for pattern in PARKING_PATTERNS:
        if re.search(pattern, text_lower):
            return True, f"Parking pattern: '{pattern}'"

    # Check URL if provided
    if url:
        url_lower = url.lower()
        for service in PARKING_SERVICES:
            if service in url_lower:
                return True, f"Parking service in URL: '{service}'"

    # Check for suspicious short content (often indicates parking page)
    word_count = len(text.split())
    if word_count < 50:
        # Very short pages are often parked
        if any(keyword in text_lower for keyword in ['domain', 'for sale', 'coming soon']):
            return True, "Short page with parking indicators"

    return False, None


def has_coming_soon_page(text: str) -> bool:
    """
    Detect "coming soon" or "under construction" pages
    These aren't technically parked but are also not active business sites
    """
    if not text:
        return False

    coming_soon_indicators = [
        'coming soon',
        'under construction',
        'site under construction',
        'website coming soon',
        'launching soon',
        'stay tuned',
        'check back soon',
        'placeholder page'
    ]

    text_lower = text.lower()
    return any(indicator in text_lower for indicator in coming_soon_indicators)


def is_generic_landing_page(text: str) -> bool:
    """
    Detect generic landing pages that aren't specific to the company
    """
    if not text:
        return False

    generic_indicators = [
        'lorem ipsum',
        'sample text',
        'default page',
        'welcome to nginx',
        'apache.*default page',
        'it works',
        'test page',
        'hello world'
    ]

    text_lower = text.lower()

    for indicator in generic_indicators:
        if re.search(indicator, text_lower):
            return True

    return False


def get_parking_confidence(text: str, url: Optional[str] = None) -> float:
    """
    Return confidence score (0-100) that this is a parked domain
    Higher score = more likely parked

    Args:
        text: Webpage content
        url: Optional URL

    Returns:
        Confidence score 0-100
    """
    if not text:
        return 0.0

    score = 0.0

    # Check for parking indicators
    is_parked, reason = is_parked_domain(text, url)
    if is_parked:
        if 'keyword' in (reason or '').lower():
            score += 80  # Direct keyword match
        elif 'service' in (reason or '').lower():
            score += 90  # Parking service mention
        elif 'pattern' in (reason or '').lower():
            score += 70  # Pattern match

    # Check for coming soon
    if has_coming_soon_page(text):
        score += 60

    # Check for generic landing
    if is_generic_landing_page(text):
        score += 50

    # Check content length
    word_count = len(text.split())
    if word_count < 100:
        score += 20
    elif word_count < 50:
        score += 40

    # Cap at 100
    return min(score, 100.0)
