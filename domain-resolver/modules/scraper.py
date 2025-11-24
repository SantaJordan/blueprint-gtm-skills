"""
Web scraping module with requests → ZenRows fallback → Trafilatura extraction

Enhanced V2: Includes validation capabilities for domain verification
- Contact information extraction (phone, email)
- Company name extraction
- Domain verification from page metadata
"""
import aiohttp
import trafilatura
import logging
from typing import Optional, Dict, Any, List
import asyncio
import re
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


async def fetch_with_requests(url: str, timeout: int = 10) -> Optional[str]:
    """
    Fetch HTML using standard aiohttp request

    Args:
        url: URL to fetch
        timeout: Request timeout in seconds

    Returns:
        HTML content or None if failed
    """
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers,
                                  timeout=aiohttp.ClientTimeout(total=timeout),
                                  allow_redirects=True) as response:

                if response.status == 200:
                    html = await response.text()
                    logger.debug(f"Successfully fetched {url} with requests")
                    return html
                else:
                    logger.warning(f"HTTP {response.status} for {url}")
                    return None

    except asyncio.TimeoutError:
        logger.warning(f"Timeout fetching {url}")
        return None
    except Exception as e:
        logger.warning(f"Error fetching {url}: {e}")
        return None


async def fetch_with_zenrows(url: str, api_key: str, timeout: int = 20) -> Optional[str]:
    """
    Fetch HTML using ZenRows (for anti-bot sites)

    Args:
        url: URL to fetch
        api_key: ZenRows API key
        timeout: Request timeout in seconds

    Returns:
        HTML content or None if failed
    """
    if not api_key:
        logger.error("ZenRows API key not configured")
        return None

    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    zenrows_url = "https://api.zenrows.com/v1/"

    params = {
        'url': url,
        'apikey': api_key,
        'js_render': 'false',  # Don't need JS rendering for most business sites
        'premium_proxy': 'false'  # Start with residential, upgrade if needed
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(zenrows_url, params=params,
                                  timeout=aiohttp.ClientTimeout(total=timeout)) as response:

                if response.status == 200:
                    html = await response.text()
                    logger.info(f"Successfully fetched {url} with ZenRows")
                    return html
                else:
                    logger.error(f"ZenRows returned {response.status} for {url}")
                    return None

    except asyncio.TimeoutError:
        logger.error(f"ZenRows timeout for {url}")
        return None
    except Exception as e:
        logger.error(f"ZenRows error for {url}: {e}")
        return None


def extract_text(html: str) -> Optional[str]:
    """
    Extract clean text from HTML using Trafilatura

    Args:
        html: Raw HTML content

    Returns:
        Extracted text or None if failed
    """
    if not html:
        return None

    try:
        # Trafilatura extracts main content and removes boilerplate
        text = trafilatura.extract(html,
                                   include_comments=False,
                                   include_tables=False,
                                   include_formatting=False,
                                   no_fallback=False)

        if text and len(text) > 50:  # Minimum meaningful content
            logger.debug(f"Extracted {len(text)} characters of text")
            return text
        else:
            logger.warning("Trafilatura returned insufficient text")
            return None

    except Exception as e:
        logger.error(f"Trafilatura extraction error: {e}")
        return None


async def scrape_url(url: str, zenrows_api_key: Optional[str] = None,
                    timeout: int = 15) -> Optional[Dict[str, Any]]:
    """
    Scrape URL with automatic fallback: requests → ZenRows → Trafilatura

    Args:
        url: URL to scrape
        zenrows_api_key: Optional ZenRows API key for fallback
        timeout: Timeout in seconds

    Returns:
        {
            'url': str,
            'html': str,
            'text': str,
            'method': str,  # 'requests' or 'zenrows'
            'char_count': int
        } or None
    """
    html = None
    method = None

    # Try 1: Standard requests (free, fast)
    html = await fetch_with_requests(url, timeout=timeout)
    if html:
        method = 'requests'
    else:
        # Try 2: ZenRows fallback (for anti-bot sites)
        if zenrows_api_key:
            logger.info(f"Falling back to ZenRows for {url}")
            html = await fetch_with_zenrows(url, zenrows_api_key, timeout=timeout)
            if html:
                method = 'zenrows'

    if not html:
        logger.error(f"Failed to fetch {url} with all methods")
        return None

    # Extract clean text
    text = extract_text(html)

    if not text:
        logger.warning(f"No text extracted from {url}")
        return None

    return {
        'url': url,
        'html': html,
        'text': text,
        'method': method,
        'char_count': len(text)
    }


async def batch_scrape(urls: list, zenrows_api_key: Optional[str] = None,
                      max_concurrent: int = 5, timeout: int = 15) -> Dict[str, Any]:
    """
    Scrape multiple URLs concurrently

    Args:
        urls: List of URLs to scrape
        zenrows_api_key: Optional ZenRows API key
        max_concurrent: Maximum concurrent requests
        timeout: Per-request timeout

    Returns:
        Dict mapping URL to scrape result
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def scrape_with_semaphore(url):
        async with semaphore:
            return await scrape_url(url, zenrows_api_key, timeout)

    tasks = [scrape_with_semaphore(url) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Map results
    result_map = {}
    for url, result in zip(urls, results):
        if isinstance(result, Exception):
            logger.error(f"Exception scraping {url}: {result}")
            result_map[url] = None
        else:
            result_map[url] = result

    return result_map


# =============================================================================
# V2 VALIDATION ENHANCEMENTS
# =============================================================================

def extract_phone_numbers(html: str) -> List[str]:
    """
    Extract phone numbers from HTML

    Args:
        html: Raw HTML content

    Returns:
        List of phone numbers found
    """
    if not html:
        return []

    # Common phone number patterns
    patterns = [
        r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',  # 555-123-4567, 555.123.4567, 555 123 4567
        r'\(\d{3}\)\s*\d{3}[-.\s]?\d{4}',       # (555) 123-4567
        r'\+\d{1,3}[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',  # +1-555-123-4567
        r'\b\d{10}\b',                           # 5551234567
    ]

    phones = []
    for pattern in patterns:
        matches = re.findall(pattern, html)
        phones.extend(matches)

    # Deduplicate and normalize
    normalized_phones = []
    for phone in phones:
        # Extract digits only
        digits = re.sub(r'\D', '', phone)
        if 10 <= len(digits) <= 15:  # Valid phone number length
            normalized_phones.append(phone)

    return list(set(normalized_phones))[:5]  # Return up to 5 unique phones


def extract_emails(html: str) -> List[str]:
    """
    Extract email addresses from HTML

    Args:
        html: Raw HTML content

    Returns:
        List of email addresses found
    """
    if not html:
        return []

    # Email pattern
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

    emails = re.findall(pattern, html)

    # Filter out common noise emails
    noise_patterns = [
        r'.*@example\.(com|org)',
        r'.*@email\.(com|org)',
        r'.*@domain\.(com|org)',
        r'.*@placeholder\.',
        r'noreply@',
        r'no-reply@'
    ]

    filtered_emails = []
    for email in emails:
        is_noise = any(re.match(pattern, email, re.I) for pattern in noise_patterns)
        if not is_noise:
            filtered_emails.append(email.lower())

    return list(set(filtered_emails))[:5]  # Return up to 5 unique emails


def extract_company_name(html: str) -> Optional[str]:
    """
    Extract company name from HTML metadata and content

    Checks:
    1. <title> tag
    2. <meta property="og:site_name"> tag
    3. <meta name="author"> tag
    4. <meta name="publisher"> tag
    5. Schema.org Organization name

    Args:
        html: Raw HTML content

    Returns:
        Company name or None
    """
    if not html:
        return None

    try:
        soup = BeautifulSoup(html, 'html.parser')

        # Check og:site_name
        og_site = soup.find('meta', property='og:site_name')
        if og_site and og_site.get('content'):
            return og_site['content'].strip()

        # Check meta author
        author = soup.find('meta', attrs={'name': 'author'})
        if author and author.get('content'):
            return author['content'].strip()

        # Check meta publisher
        publisher = soup.find('meta', attrs={'name': 'publisher'})
        if publisher and publisher.get('content'):
            return publisher['content'].strip()

        # Check schema.org Organization
        org_schema = soup.find('script', type='application/ld+json')
        if org_schema:
            try:
                import json
                data = json.loads(org_schema.string)
                if isinstance(data, dict):
                    if data.get('@type') == 'Organization' and data.get('name'):
                        return data['name']
                    if 'publisher' in data and isinstance(data['publisher'], dict):
                        if data['publisher'].get('name'):
                            return data['publisher']['name']
            except:
                pass

        # Fallback: Extract from title (remove common suffixes)
        title = soup.find('title')
        if title and title.string:
            title_text = title.string.strip()
            # Remove common suffixes
            for suffix in [' - Home', ' | Home', ' - Official Site', ' | Official Site',
                          ' - Welcome', ' | Welcome', ' | Official Website']:
                title_text = title_text.replace(suffix, '')
            return title_text

        return None

    except Exception as e:
        logger.debug(f"Error extracting company name: {e}")
        return None


def extract_domain_from_meta(html: str) -> Optional[str]:
    """
    Extract domain from HTML metadata

    Checks:
    1. <meta property="og:url">
    2. <link rel="canonical">
    3. <meta name="url">

    Args:
        html: Raw HTML content

    Returns:
        Domain or None
    """
    if not html:
        return None

    try:
        soup = BeautifulSoup(html, 'html.parser')

        # Check og:url
        og_url = soup.find('meta', property='og:url')
        if og_url and og_url.get('content'):
            url = og_url['content']
            domain = re.sub(r'https?://(www\.)?', '', url)
            domain = domain.split('/')[0]
            return domain

        # Check canonical
        canonical = soup.find('link', rel='canonical')
        if canonical and canonical.get('href'):
            url = canonical['href']
            domain = re.sub(r'https?://(www\.)?', '', url)
            domain = domain.split('/')[0]
            return domain

        # Check meta url
        meta_url = soup.find('meta', attrs={'name': 'url'})
        if meta_url and meta_url.get('content'):
            url = meta_url['content']
            domain = re.sub(r'https?://(www\.)?', '', url)
            domain = domain.split('/')[0]
            return domain

        return None

    except Exception as e:
        logger.debug(f"Error extracting domain from metadata: {e}")
        return None


async def scrape_and_validate(url: str, company_data: Dict[str, Any],
                               zenrows_api_key: Optional[str] = None,
                               timeout: int = 15) -> Optional[Dict[str, Any]]:
    """
    Scrape URL and extract validation data

    This is the V2 enhanced scraper that always extracts validation signals
    for use by the LLM judge.

    Args:
        url: URL to scrape
        company_data: Expected company data (name, phone, city, etc.)
        zenrows_api_key: Optional ZenRows API key
        timeout: Timeout in seconds

    Returns:
        {
            'url': str,
            'html': str,
            'text': str,
            'method': str,
            'char_count': int,
            'validation': {
                'company_name': str,           # Extracted from page
                'domain': str,                 # From page metadata
                'phone_numbers': List[str],    # All phones found
                'emails': List[str],           # All emails found
                'phone_match': bool,           # Does any phone match input?
                'name_similarity': float       # 0-100 similarity score
            }
        } or None
    """
    # First scrape the page
    result = await scrape_url(url, zenrows_api_key, timeout)

    if not result:
        return None

    # Extract validation signals
    html = result['html']
    text = result['text']

    extracted_name = extract_company_name(html)
    extracted_domain = extract_domain_from_meta(html)
    extracted_phones = extract_phone_numbers(html)
    extracted_emails = extract_emails(html)

    # Check phone match
    phone_match = False
    if company_data.get('phone') and extracted_phones:
        input_phone_digits = re.sub(r'\D', '', company_data['phone'])
        for extracted_phone in extracted_phones:
            extracted_digits = re.sub(r'\D', '', extracted_phone)
            # Check if last 4+ digits match
            if len(input_phone_digits) >= 4 and len(extracted_digits) >= 4:
                if input_phone_digits[-4:] == extracted_digits[-4:]:
                    phone_match = True
                    break

    # Calculate name similarity
    name_similarity = 0.0
    if company_data.get('name') and extracted_name:
        from rapidfuzz import fuzz
        name_similarity = fuzz.ratio(
            company_data['name'].lower(),
            extracted_name.lower()
        )

    # Add validation data to result
    result['validation'] = {
        'company_name': extracted_name,
        'domain': extracted_domain,
        'phone_numbers': extracted_phones,
        'emails': extracted_emails,
        'phone_match': phone_match,
        'name_similarity': name_similarity
    }

    logger.info(f"Validation signals for {url}:")
    logger.info(f"  Company name: {extracted_name}")
    logger.info(f"  Phone match: {phone_match}")
    logger.info(f"  Name similarity: {name_similarity:.1f}")

    return result
