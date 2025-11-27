"""
LinkedIn URL Normalization
Clean and validate LinkedIn URLs to proper format
"""

import re
from urllib.parse import urlparse, parse_qs


def normalize_linkedin_url(url: str | None) -> str | None:
    """
    Normalize a LinkedIn URL to clean format.

    For person profiles: linkedin.com/in/username
    For company profiles: linkedin.com/company/company-name

    Removes:
    - Protocol (https://, http://)
    - www prefix
    - Trailing slashes
    - Query parameters (?mini=true, etc.)
    - Fragment identifiers (#)
    - Locale prefixes (/en/, /de/, etc.)

    Args:
        url: LinkedIn URL to normalize

    Returns:
        Normalized URL or None if invalid
    """
    if not url:
        return None

    url = url.strip()

    # Handle URLs that are just the path
    if url.startswith('/in/') or url.startswith('/company/'):
        url = f"linkedin.com{url}"

    # Remove protocol
    url = re.sub(r'^https?://', '', url)

    # Remove www
    url = re.sub(r'^www\.', '', url)

    # Handle country-specific subdomains (de.linkedin.com, fr.linkedin.com, etc.)
    url = re.sub(r'^[a-z]{2}\.linkedin\.com', 'linkedin.com', url)

    # Must contain linkedin.com
    if 'linkedin.com' not in url:
        return None

    # Parse to get path
    try:
        # Ensure we have proper URL format for parsing
        if not url.startswith('linkedin.com'):
            # Try to extract just the linkedin.com portion
            match = re.search(r'(linkedin\.com.*)', url)
            if match:
                url = match.group(1)
            else:
                return None

        # Add protocol for parsing
        parsed = urlparse(f"https://{url}")
        path = parsed.path
    except Exception:
        return None

    # Remove locale prefixes like /en/, /de/, /fr/ but NOT /in/
    # Only remove if it's NOT followed by / (which would be /in/username)
    if path.startswith('/in/') or path.startswith('/company/'):
        pass  # Don't modify - these are the patterns we want
    else:
        # Remove country code prefix (e.g., /de/in/username -> /in/username)
        path = re.sub(r'^/[a-z]{2}(?=/)', '', path)

    # Extract the clean path for /in/ or /company/
    # Allow more characters in usernames (numbers can appear anywhere)
    in_match = re.search(r'/in/([a-zA-Z0-9][a-zA-Z0-9\-_]*)', path)
    company_match = re.search(r'/company/([a-zA-Z0-9][a-zA-Z0-9\-_]*)', path)

    if in_match:
        username = in_match.group(1)
        return f"linkedin.com/in/{username}"
    elif company_match:
        company_slug = company_match.group(1)
        return f"linkedin.com/company/{company_slug}"

    return None


def is_valid_linkedin_in_url(url: str | None) -> bool:
    """
    Check if URL is a valid LinkedIn personal profile URL.

    Args:
        url: URL to check

    Returns:
        True if valid /in/ URL, False otherwise
    """
    if not url:
        return False

    normalized = normalize_linkedin_url(url)
    if not normalized:
        return False

    return "/in/" in normalized


def is_valid_linkedin_company_url(url: str | None) -> bool:
    """
    Check if URL is a valid LinkedIn company profile URL.

    Args:
        url: URL to check

    Returns:
        True if valid /company/ URL, False otherwise
    """
    if not url:
        return False

    normalized = normalize_linkedin_url(url)
    if not normalized:
        return False

    return "/company/" in normalized


def extract_linkedin_username(url: str | None) -> str | None:
    """
    Extract username from a LinkedIn /in/ URL.

    Args:
        url: LinkedIn profile URL

    Returns:
        Username or None
    """
    normalized = normalize_linkedin_url(url)
    if not normalized or "/in/" not in normalized:
        return None

    match = re.search(r'/in/([a-zA-Z0-9\-_]+)', normalized)
    return match.group(1) if match else None


def extract_linkedin_company_slug(url: str | None) -> str | None:
    """
    Extract company slug from a LinkedIn /company/ URL.

    Args:
        url: LinkedIn company URL

    Returns:
        Company slug or None
    """
    normalized = normalize_linkedin_url(url)
    if not normalized or "/company/" not in normalized:
        return None

    match = re.search(r'/company/([a-zA-Z0-9\-_]+)', normalized)
    return match.group(1) if match else None


def to_full_linkedin_url(normalized_url: str | None) -> str | None:
    """
    Convert normalized LinkedIn URL to full URL with protocol.

    Args:
        normalized_url: URL like linkedin.com/in/username

    Returns:
        Full URL like https://www.linkedin.com/in/username
    """
    if not normalized_url:
        return None

    if normalized_url.startswith('http'):
        return normalized_url

    return f"https://www.{normalized_url}"


# Test cases
if __name__ == "__main__":
    test_urls = [
        "https://www.linkedin.com/in/john-smith-12345/",
        "https://linkedin.com/in/john-smith?mini=true",
        "http://www.linkedin.com/in/john-smith#about",
        "linkedin.com/in/john-smith",
        "/in/john-smith",
        "https://www.linkedin.com/company/acme-corp/",
        "https://de.linkedin.com/in/hans-mueller",
        "https://www.linkedin.com/in/jane-doe/overlay/contact-info/",
        "invalid-url",
        None,
    ]

    for url in test_urls:
        normalized = normalize_linkedin_url(url)
        is_person = is_valid_linkedin_in_url(url)
        is_company = is_valid_linkedin_company_url(url)
        print(f"{url!r:60} -> {normalized!r:40} (person: {is_person}, company: {is_company})")
