"""
Website Contact Scraper
Extract contacts, emails, and people from company websites
"""

import aiohttp
import re
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urljoin, urlparse
import trafilatura


@dataclass
class ExtractedContact:
    """A contact extracted from a website"""
    name: str | None
    title: str | None
    email: str | None
    phone: str | None
    source_url: str
    context: str | None  # Text around where contact was found


@dataclass
class SiteContactResult:
    """Results from scraping a website for contacts"""
    contacts: list[ExtractedContact] = field(default_factory=list)
    emails: list[str] = field(default_factory=list)
    phones: list[str] = field(default_factory=list)
    scrape_method: str = "requests"  # requests, zenrows
    pages_scraped: int = 0
    errors: list[str] = field(default_factory=list)


# Regex patterns
EMAIL_PATTERN = re.compile(
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
)

# Obfuscated email patterns
OBFUSCATED_EMAIL_PATTERNS = [
    re.compile(r'\b([A-Za-z0-9._%+-]+)\s*\[\s*at\s*\]\s*([A-Za-z0-9.-]+)\s*\[\s*dot\s*\]\s*([A-Z|a-z]{2,})\b', re.I),
    re.compile(r'\b([A-Za-z0-9._%+-]+)\s*\(at\)\s*([A-Za-z0-9.-]+)\s*\(dot\)\s*([A-Z|a-z]{2,})\b', re.I),
    re.compile(r'\b([A-Za-z0-9._%+-]+)\s*@\s*([A-Za-z0-9.-]+)\s*\.\s*([A-Z|a-z]{2,})\b'),
]

PHONE_PATTERNS = [
    re.compile(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'),
    re.compile(r'\+1[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}'),
    re.compile(r'1[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}'),
]

# Common pages to scrape for contacts
CONTACT_PAGES = [
    '',  # Homepage
    'contact',
    'contact-us',
    'about',
    'about-us',
    'team',
    'our-team',
    'staff',
    'leadership',
    'meet-the-team',
    'people',
]

# Blacklist emails (generic/spam traps)
EMAIL_BLACKLIST = {
    'noreply', 'no-reply', 'donotreply', 'do-not-reply',
    'test', 'example', 'spam', 'abuse', 'postmaster',
    'webmaster', 'hostmaster', 'admin', 'administrator',
    'support', 'help', 'contact', 'info', 'sales', 'marketing',
}


class SiteScraper:
    """Scrape websites for contact information"""

    def __init__(
        self,
        zenrows_api_key: str | None = None,
        timeout: int = 20,
        max_pages: int = 5
    ):
        self.zenrows_api_key = zenrows_api_key
        self.timeout = timeout
        self.max_pages = max_pages
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                },
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def _fetch_url(self, url: str) -> tuple[str | None, str]:
        """Fetch URL content, trying direct request then ZenRows fallback"""
        session = await self._get_session()

        # Try direct request first
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    if html and len(html) > 500:
                        return html, "requests"
        except Exception:
            pass

        # Try ZenRows if available
        if self.zenrows_api_key:
            try:
                zenrows_url = "https://api.zenrows.com/v1/"
                params = {
                    "url": url,
                    "apikey": self.zenrows_api_key,
                    "js_render": "false"
                }
                async with session.get(zenrows_url, params=params) as response:
                    if response.status == 200:
                        html = await response.text()
                        return html, "zenrows"
            except Exception:
                pass

        return None, "failed"

    def _extract_text(self, html: str) -> str:
        """Extract clean text from HTML using Trafilatura"""
        try:
            text = trafilatura.extract(
                html,
                include_comments=False,
                include_tables=True,
                no_fallback=False
            )
            return text or ""
        except Exception:
            return ""

    def _extract_emails(self, text: str, html: str) -> list[str]:
        """Extract email addresses from text and HTML"""
        emails = set()

        # Standard emails
        for match in EMAIL_PATTERN.findall(text):
            emails.add(match.lower())

        for match in EMAIL_PATTERN.findall(html):
            emails.add(match.lower())

        # Obfuscated emails
        for pattern in OBFUSCATED_EMAIL_PATTERNS:
            for match in pattern.findall(text):
                if len(match) == 3:
                    email = f"{match[0]}@{match[1]}.{match[2]}".lower()
                    emails.add(email)

        # Filter out blacklisted and invalid emails
        valid_emails = []
        for email in emails:
            local_part = email.split('@')[0].lower()

            # Skip blacklisted
            if any(bl in local_part for bl in EMAIL_BLACKLIST):
                continue

            # Skip image/file extensions
            if any(email.endswith(ext) for ext in ['.png', '.jpg', '.gif', '.svg', '.css', '.js']):
                continue

            valid_emails.append(email)

        return valid_emails

    def _extract_phones(self, text: str) -> list[str]:
        """Extract phone numbers from text"""
        phones = set()

        for pattern in PHONE_PATTERNS:
            for match in pattern.findall(text):
                # Normalize phone
                phone = re.sub(r'[^\d]', '', match)
                if len(phone) >= 10:
                    phones.add(phone[-10:])  # Last 10 digits

        return list(phones)

    def _extract_contacts_from_text(self, text: str, source_url: str) -> list[ExtractedContact]:
        """Extract named contacts from text content"""
        contacts = []

        # Look for patterns like "Owner: John Smith" or "John Smith, Owner"
        # This is simplified - a real implementation would use NER
        lines = text.split('\n')

        title_keywords = [
            'owner', 'president', 'ceo', 'director', 'manager',
            'founder', 'partner', 'principal', 'chief'
        ]

        for i, line in enumerate(lines):
            line_lower = line.lower()

            # Check if line contains a title keyword
            for keyword in title_keywords:
                if keyword in line_lower:
                    # Look for a name pattern near the keyword
                    # This is very simplified
                    context_start = max(0, i - 1)
                    context_end = min(len(lines), i + 2)
                    context = '\n'.join(lines[context_start:context_end])

                    # Extract any emails in context
                    emails = self._extract_emails(context, context)

                    contacts.append(ExtractedContact(
                        name=None,  # Would need NER for this
                        title=keyword.title(),
                        email=emails[0] if emails else None,
                        phone=None,
                        source_url=source_url,
                        context=context[:200]
                    ))
                    break

        return contacts

    async def scrape_domain(self, domain: str) -> SiteContactResult:
        """
        Scrape a domain for contact information

        Args:
            domain: Domain to scrape (without protocol)

        Returns:
            SiteContactResult with all found contacts and emails
        """
        result = SiteContactResult()

        # Ensure domain has protocol
        if not domain.startswith('http'):
            base_url = f"https://{domain}"
        else:
            base_url = domain
            domain = urlparse(domain).netloc

        all_emails = set()
        all_phones = set()
        all_contacts = []

        # Scrape contact pages
        pages_to_try = [urljoin(base_url, f"/{page}") for page in CONTACT_PAGES[:self.max_pages]]

        for url in pages_to_try:
            html, method = await self._fetch_url(url)

            if not html:
                result.errors.append(f"Failed to fetch: {url}")
                continue

            result.pages_scraped += 1
            if method != "requests":
                result.scrape_method = method

            # Extract text
            text = self._extract_text(html)

            # Extract emails
            emails = self._extract_emails(text, html)
            all_emails.update(emails)

            # Extract phones
            phones = self._extract_phones(text)
            all_phones.update(phones)

            # Extract named contacts
            contacts = self._extract_contacts_from_text(text, url)
            all_contacts.extend(contacts)

        # Filter to domain emails only
        result.emails = [e for e in all_emails if domain in e]

        # Include some non-domain emails if they look personal
        personal_emails = [e for e in all_emails if
                          any(e.endswith(d) for d in ['@gmail.com', '@yahoo.com', '@outlook.com', '@hotmail.com'])
                          and domain.split('.')[0].lower() in e.lower()]
        result.emails.extend(personal_emails)

        result.phones = list(all_phones)
        result.contacts = all_contacts

        return result

    async def extract_email_for_person(
        self,
        domain: str,
        name: str
    ) -> str | None:
        """
        Look for a specific person's email on a website

        Args:
            domain: Company domain
            name: Person's name to look for

        Returns:
            Email if found, None otherwise
        """
        result = await self.scrape_domain(domain)

        # Look for emails matching the person's name
        name_parts = name.lower().split()

        for email in result.emails:
            local_part = email.split('@')[0].lower()

            # Check if name parts appear in email
            if any(part in local_part for part in name_parts if len(part) > 2):
                return email

        return None


# Convenience function
async def test_site_scraper(domain: str):
    """Test site scraper"""
    scraper = SiteScraper()
    try:
        result = await scraper.scrape_domain(domain)
        print(f"Scraped {result.pages_scraped} pages from {domain}")
        print(f"Found {len(result.emails)} emails, {len(result.phones)} phones")
        return result
    finally:
        await scraper.close()
