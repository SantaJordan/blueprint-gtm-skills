"""
Email Permutation Generator
Generate common email permutations from a person's name and company domain
"""

import re
import unicodedata
from dataclasses import dataclass
from typing import Optional


# Company name indicators that should not be used for email permutations
COMPANY_INDICATORS = {
    'llc', 'inc', 'corp', 'corporation', 'company', 'co', 'ltd', 'limited',
    'group', 'holdings', 'partners', 'associates', 'enterprises', 'services',
    'solutions', 'consulting', 'agency', 'studio', 'shop', 'store', 'restaurant',
    'bar', 'cafe', 'salon', 'spa', 'clinic', 'dental', 'medical', 'law', 'firm',
    'plumbing', 'electric', 'electrical', 'hvac', 'construction', 'roofing',
    'landscaping', 'cleaning', 'auto', 'automotive', 'repair', 'maintenance',
    'dba', 'pllc', 'llp', 'pc', 'pa', 'md', 'dds', 'dvm'
}

# Common name prefixes/suffixes to strip
NAME_PREFIXES = {'mr', 'mrs', 'ms', 'dr', 'prof', 'rev'}
NAME_SUFFIXES = {'jr', 'sr', 'ii', 'iii', 'iv', 'phd', 'md', 'esq', 'cpa'}


@dataclass
class NameComponents:
    """Parsed name components"""
    first_name: str
    last_name: Optional[str]
    first_initial: str
    last_initial: Optional[str]
    original: str
    is_valid: bool
    rejection_reason: Optional[str] = None


def normalize_text(text: str) -> str:
    """Remove accents and normalize unicode to ASCII"""
    if not text:
        return ""
    # Normalize unicode (NFD decomposition) then remove diacritics
    normalized = unicodedata.normalize('NFD', text)
    ascii_text = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
    return ascii_text.lower().strip()


def clean_name_part(name: str) -> str:
    """Clean a name part for use in email (lowercase, no special chars)"""
    if not name:
        return ""
    # Normalize and convert to ASCII
    name = normalize_text(name)
    # Remove anything that's not alphanumeric
    name = re.sub(r'[^a-z0-9]', '', name)
    return name


def split_name(full_name: str) -> tuple[str, Optional[str]]:
    """
    Split a full name into first and last name.
    Handles prefixes (Mr., Dr.) and suffixes (Jr., III).

    Args:
        full_name: Full name like "John Smith" or "Dr. John Smith Jr."

    Returns:
        Tuple of (first_name, last_name) - last_name may be None
    """
    if not full_name:
        return "", None

    # Normalize and split
    parts = full_name.strip().split()
    if not parts:
        return "", None

    # Remove common prefixes
    while parts and parts[0].lower().rstrip('.') in NAME_PREFIXES:
        parts.pop(0)

    # Remove common suffixes
    while parts and parts[-1].lower().rstrip('.') in NAME_SUFFIXES:
        parts.pop()

    if len(parts) == 0:
        return "", None
    elif len(parts) == 1:
        return parts[0], None
    else:
        # First word is first name, rest is last name
        # For "John David Smith", returns ("John", "David Smith")
        # We'll use just the last word as last name for email purposes
        return parts[0], parts[-1]


def is_valid_for_permutation(name: str) -> tuple[bool, Optional[str]]:
    """
    Check if a name is valid for email permutation generation.
    Rejects company names, single characters, etc.

    Args:
        name: Name to check

    Returns:
        Tuple of (is_valid, rejection_reason)
    """
    if not name:
        return False, "empty_name"

    # Normalize for checking
    name_lower = name.lower()
    words = name_lower.split()

    # Check for company indicators
    for word in words:
        # Remove punctuation for comparison
        clean_word = re.sub(r'[^a-z]', '', word)
        if clean_word in COMPANY_INDICATORS:
            return False, f"company_indicator:{clean_word}"

    # Get first name part
    first_name, last_name = split_name(name)
    first_clean = clean_name_part(first_name)

    # First name too short
    if len(first_clean) < 2:
        return False, "first_name_too_short"

    # Check for numeric content (likely a business name)
    if re.search(r'\d', name):
        return False, "contains_numbers"

    # Check for special patterns that indicate business names
    if re.search(r'[@#$%&]', name):
        return False, "contains_special_chars"

    return True, None


def parse_name(full_name: str) -> NameComponents:
    """
    Parse a full name into components for email generation.

    Args:
        full_name: Full name like "John Smith"

    Returns:
        NameComponents with parsed data
    """
    is_valid, rejection_reason = is_valid_for_permutation(full_name)

    if not is_valid:
        return NameComponents(
            first_name="",
            last_name=None,
            first_initial="",
            last_initial=None,
            original=full_name,
            is_valid=False,
            rejection_reason=rejection_reason
        )

    first_name, last_name = split_name(full_name)
    first_clean = clean_name_part(first_name)
    last_clean = clean_name_part(last_name) if last_name else None

    return NameComponents(
        first_name=first_clean,
        last_name=last_clean,
        first_initial=first_clean[0] if first_clean else "",
        last_initial=last_clean[0] if last_clean else None,
        original=full_name,
        is_valid=True
    )


def generate_permutations(
    first_name: str,
    last_name: Optional[str],
    domain: str
) -> list[str]:
    """
    Generate email permutations from name components.

    Args:
        first_name: Cleaned first name (lowercase, no special chars)
        last_name: Cleaned last name (optional)
        domain: Company domain (e.g., "example.com")

    Returns:
        List of email permutations to try
    """
    if not first_name or not domain:
        return []

    domain = domain.lower().strip()
    # Remove any protocol prefix
    if domain.startswith(('http://', 'https://')):
        domain = domain.split('://', 1)[1]
    # Remove www prefix
    if domain.startswith('www.'):
        domain = domain[4:]
    # Remove trailing slash
    domain = domain.rstrip('/')

    emails = []

    # firstname@ (always include)
    emails.append(f"{first_name}@{domain}")

    if last_name:
        first_initial = first_name[0]
        last_initial = last_name[0]

        # All patterns with last name
        patterns = [
            f"{last_name}@{domain}",              # smith@
            f"{first_name}{last_name}@{domain}",  # johnsmith@
            f"{first_name}.{last_name}@{domain}", # john.smith@
            f"{first_initial}{last_name}@{domain}",   # jsmith@
            f"{first_name}{last_initial}@{domain}",   # johns@
            f"{first_initial}.{last_name}@{domain}",  # j.smith@
            f"{first_name}_{last_name}@{domain}",     # john_smith@
        ]
        emails.extend(patterns)

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for email in emails:
        if email not in seen:
            seen.add(email)
            unique.append(email)

    return unique


def generate_email_permutations(full_name: str, domain: str) -> list[str]:
    """
    Generate email permutations from a full name and domain.
    Convenience function that handles parsing.

    Args:
        full_name: Full name like "John Smith"
        domain: Company domain like "example.com"

    Returns:
        List of email permutations, or empty list if name is invalid
    """
    components = parse_name(full_name)

    if not components.is_valid:
        return []

    return generate_permutations(
        first_name=components.first_name,
        last_name=components.last_name,
        domain=domain
    )


# Additional common patterns for aggressive search
def generate_extended_permutations(
    first_name: str,
    last_name: Optional[str],
    domain: str
) -> list[str]:
    """
    Generate extended email permutations including less common patterns.

    Args:
        first_name: Cleaned first name
        last_name: Cleaned last name (optional)
        domain: Company domain

    Returns:
        Extended list of email permutations
    """
    # Start with standard patterns
    emails = generate_permutations(first_name, last_name, domain)

    if not emails:
        return []

    domain = domain.lower().strip()
    if domain.startswith(('http://', 'https://')):
        domain = domain.split('://', 1)[1]
    if domain.startswith('www.'):
        domain = domain[4:]
    domain = domain.rstrip('/')

    if last_name:
        first_initial = first_name[0]
        last_initial = last_name[0]

        # Additional patterns
        extra_patterns = [
            f"{last_name}.{first_name}@{domain}",     # smith.john@
            f"{last_name}{first_name}@{domain}",      # smithjohn@
            f"{last_name}{first_initial}@{domain}",   # smithj@
            f"{first_name}-{last_name}@{domain}",     # john-smith@
            f"{first_initial}{last_initial}@{domain}",  # js@
        ]

        for pattern in extra_patterns:
            if pattern not in emails:
                emails.append(pattern)

    return emails
