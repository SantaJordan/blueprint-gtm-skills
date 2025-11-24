"""
Utility functions for domain resolution
"""
import re
import tldextract
import dns.resolver
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def normalize_company_name(name: str) -> str:
    """
    Normalize company name for matching
    Removes common suffixes like Inc, LLC, Corp, etc.
    """
    if not name:
        return ""

    stopwords = [
        'inc', 'incorporated', 'llc', 'corp', 'corporation', 'ltd', 'limited',
        'company', 'co', 'the', 'and', '&', 'l.l.c.', 'l.p.', 'lp', 'plc',
        'group', 'holdings', 'international', 'enterprises', 'solutions'
    ]

    # Convert to lowercase
    clean = name.lower().strip()

    # Remove punctuation except hyphens
    clean = re.sub(r'[^\w\s-]', ' ', clean)

    # Remove stopwords
    words = clean.split()
    filtered_words = [w for w in words if w not in stopwords]

    # Join back
    result = ' '.join(filtered_words).strip()

    # Remove extra whitespace
    result = re.sub(r'\s+', ' ', result)

    return result


def clean_domain(url: str) -> str:
    """
    Extract clean domain from URL
    Examples:
        https://www.example.com/path -> example.com
        http://subdomain.example.co.uk -> example.co.uk
    """
    if not url:
        return ""

    # Add scheme if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    extracted = tldextract.extract(url)

    # Return domain.suffix (e.g., example.com)
    if extracted.domain and extracted.suffix:
        return f"{extracted.domain}.{extracted.suffix}"

    return ""


def get_base_domain(url: str) -> str:
    """
    Get just the domain part without TLD
    Examples:
        example.com -> example
        subdomain.example.co.uk -> example
    """
    if not url:
        return ""

    extracted = tldextract.extract(url)
    return extracted.domain.lower()


def verify_dns(domain: str) -> bool:
    """
    Verify domain exists via DNS lookup
    Returns True if domain resolves, False otherwise
    """
    if not domain:
        return False

    try:
        # Try A record
        dns.resolver.resolve(domain, 'A')
        return True
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.Timeout, dns.exception.DNSException):
        try:
            # Try AAAA record (IPv6)
            dns.resolver.resolve(domain, 'AAAA')
            return True
        except:
            return False


def phone_fuzzy_match(phone1: Optional[str], phone2: Optional[str], min_digits: int = 4) -> bool:
    """
    Fuzzy match phone numbers by comparing last N digits
    Handles different formats: (555) 123-4567, 555-123-4567, +1 555 123 4567, etc.
    """
    if not phone1 or not phone2:
        return False

    # Extract digits only
    digits1 = re.sub(r'\D', '', str(phone1))
    digits2 = re.sub(r'\D', '', str(phone2))

    if not digits1 or not digits2:
        return False

    # Compare last N digits
    return digits1[-min_digits:] == digits2[-min_digits:]


def is_blacklisted(url: str, blacklist: list) -> bool:
    """
    Check if URL matches blacklisted domains
    """
    if not url:
        return False

    domain = clean_domain(url)
    base_domain = get_base_domain(url)

    for blocked in blacklist:
        blocked_base = get_base_domain(blocked)
        if blocked_base in domain or blocked_base == base_domain:
            return True

    return False


def extract_city_from_address(address: str) -> str:
    """
    Extract city from address string
    Very basic extraction - looks for common patterns
    """
    if not address:
        return ""

    # Try to extract city before state/zip
    # Pattern: "123 Main St, Boston, MA 02101"
    parts = address.split(',')
    if len(parts) >= 2:
        # City is usually second-to-last part
        city = parts[-2].strip()
        # Remove numbers (likely zip code)
        city = re.sub(r'\d+', '', city).strip()
        return city

    return ""


def create_search_query(name: str, city: Optional[str] = None,
                       context: Optional[str] = None, query_type: str = "official") -> str:
    """
    Create optimized search query for Serper

    Args:
        name: Company name
        city: City or location
        context: Additional context (industry, keywords)
        query_type: "official", "places", or "generic"
    """
    parts = [name]

    if city:
        parts.append(city)

    if context and query_type != "places":
        # Add context for disambiguation
        parts.append(context)

    if query_type == "official":
        parts.append("official website")
    elif query_type == "places":
        # For Places API, keep it simple
        pass

    return ' '.join(parts)
