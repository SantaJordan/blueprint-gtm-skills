"""
Directory Scraper - Extract domains from B2B directory sites

Searches business directories (ZoomInfo, Crunchbase, Apollo, LinkedIn) using
Google's site: operator, then extracts company domain from directory listings.

This is a "hack" approach that leverages public directory data without needing
API keys for each directory service.
"""

import aiohttp
import logging
from typing import Dict, List, Optional, Any, Tuple
import re
from bs4 import BeautifulSoup
import asyncio

logger = logging.getLogger(__name__)


class DirectoryScraper:
    """Scrapes company domains from business directory sites"""

    # Directory configurations
    DIRECTORIES = {
        'zoominfo': {
            'search_template': 'site:zoominfo.com/c {company_name}',
            'domain_patterns': [
                r'href="https?://(?:www\.)?([^/"\']+\.[a-z]{2,})"',  # Generic link
                r'website["\']?\s*:\s*["\']https?://(?:www\.)?([^/"\']+)',  # JSON data
                r'data-website["\']?=["\'](https?://(?:www\.)?[^"\']+)',  # Data attribute
            ],
            'domain_selectors': [
                'a[href*="http"]',  # All external links
                '.website-link',
                '[data-website]'
            ]
        },
        'crunchbase': {
            'search_template': 'site:crunchbase.com/organization {company_name}',
            'domain_patterns': [
                r'identifier["\']?\s*:\s*["\']https?://(?:www\.)?([^/"\']+)',
                r'Website["\']?[:\s]+["\']?https?://(?:www\.)?([^/"\']+)',
                r'href="https?://(?:www\.)?([^/"\']+\.[a-z]{2,})"',
            ],
            'domain_selectors': [
                'a.cb-link',
                'a[aria-label*="website"]',
                'a[href*="http"]'
            ]
        },
        'apollo': {
            'search_template': 'site:apollo.io/companies {company_name}',
            'domain_patterns': [
                r'domain["\']?\s*:\s*["\']([^"\']+)',
                r'website["\']?\s*:\s*["\']https?://(?:www\.)?([^/"\']+)',
                r'href="https?://(?:www\.)?([^/"\']+\.[a-z]{2,})"',
            ],
            'domain_selectors': [
                'a.website-link',
                'a[href*="http"]'
            ]
        },
        'linkedin': {
            'search_template': 'site:linkedin.com/company {company_name}',
            'domain_patterns': [
                r'externalUrl["\']?\s*:\s*["\']https?://(?:www\.)?([^/"\']+)',
                r'website["\']?\s*:\s*["\']https?://(?:www\.)?([^/"\']+)',
                r'See all.*?employees on LinkedIn.*?href="https?://(?:www\.)?([^/"\']+)',
            ],
            'domain_selectors': [
                'a.link-without-visited-state',
                'a[href*="http"]'
            ]
        }
    }

    def __init__(self, serper_api_key: str, zenrows_api_key: Optional[str] = None):
        """
        Initialize directory scraper

        Args:
            serper_api_key: Serper API key for Google search
            zenrows_api_key: Optional ZenRows API key for anti-bot scraping
        """
        self.serper_api_key = serper_api_key
        self.zenrows_api_key = zenrows_api_key

    async def search_directories(self, company_name: str,
                                 context: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search all configured directories for company domain

        Args:
            company_name: Company name to search
            context: Optional industry/context for disambiguation

        Returns:
            List of results: [{
                'domain': str,
                'source': str,  # 'zoominfo', 'crunchbase', etc.
                'confidence': int,  # 75 (directory-sourced)
                'directory_url': str
            }]
        """
        logger.info(f"Searching directories for: {company_name}")

        tasks = []
        for directory_name in self.DIRECTORIES.keys():
            tasks.append(self._search_single_directory(
                directory_name, company_name, context
            ))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and None results
        valid_results = []
        for i, result in enumerate(results):
            directory_name = list(self.DIRECTORIES.keys())[i]
            if isinstance(result, Exception):
                logger.error(f"Error searching {directory_name}: {result}")
            elif result:
                valid_results.append(result)

        logger.info(f"Found {len(valid_results)} domains from directories")
        return valid_results

    async def _search_single_directory(self, directory_name: str,
                                      company_name: str,
                                      context: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Search a single directory for company domain

        Args:
            directory_name: Name of directory ('zoominfo', 'crunchbase', etc.)
            company_name: Company name
            context: Optional context

        Returns:
            Result dict or None if not found
        """
        config = self.DIRECTORIES[directory_name]

        # Build search query
        query = config['search_template'].format(company_name=company_name)
        if context:
            query += f" {context}"

        logger.debug(f"Searching {directory_name}: {query}")

        # Search Google for directory page
        directory_url = await self._google_search_directory(query, directory_name)

        if not directory_url:
            logger.debug(f"No {directory_name} page found for {company_name}")
            return None

        logger.info(f"Found {directory_name} page: {directory_url}")

        # Scrape directory page
        domain = await self._extract_domain_from_directory(
            directory_url, config, company_name
        )

        if not domain:
            logger.debug(f"Could not extract domain from {directory_name} page")
            return None

        return {
            'domain': domain,
            'source': f'directory_{directory_name}',
            'confidence': 75,  # Medium confidence for directory-sourced domains
            'directory_url': directory_url
        }

    async def _google_search_directory(self, query: str, directory_name: str) -> Optional[str]:
        """
        Use Google search (via Serper) to find directory page

        Args:
            query: Search query with site: operator
            directory_name: Name of directory

        Returns:
            URL of directory page or None
        """
        url = "https://google.serper.dev/search"

        headers = {
            'X-API-KEY': self.serper_api_key,
            'Content-Type': 'application/json'
        }

        payload = {
            'q': query,
            'num': 3  # Only need top 3 results
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers,
                                       timeout=aiohttp.ClientTimeout(total=10)) as response:

                    if response.status != 200:
                        logger.error(f"Serper error for {directory_name}: {response.status}")
                        return None

                    data = await response.json()

                    # Get first organic result
                    organic = data.get('organic', [])
                    if organic and len(organic) > 0:
                        return organic[0].get('link')

                    return None

        except Exception as e:
            logger.error(f"Error searching {directory_name}: {e}")
            return None

    async def _extract_domain_from_directory(self, directory_url: str,
                                            config: Dict[str, Any],
                                            company_name: str) -> Optional[str]:
        """
        Extract company domain from directory page

        Args:
            directory_url: URL of directory listing
            config: Directory configuration (patterns, selectors)
            company_name: Company name for validation

        Returns:
            Domain or None
        """
        # Scrape directory page
        html = await self._fetch_page(directory_url)

        if not html:
            return None

        # Try regex patterns first (fast)
        for pattern in config['domain_patterns']:
            matches = re.findall(pattern, html, re.IGNORECASE)
            if matches:
                domain = self._clean_domain(matches[0])
                if domain and self._is_valid_domain(domain, company_name):
                    logger.info(f"Extracted domain via regex: {domain}")
                    return domain

        # Try CSS selectors (more reliable but slower)
        try:
            soup = BeautifulSoup(html, 'html.parser')

            for selector in config['domain_selectors']:
                elements = soup.select(selector)
                for elem in elements:
                    href = elem.get('href', '')
                    if href and 'http' in href:
                        # Extract domain from href
                        domain_match = re.search(r'https?://(?:www\.)?([^/"\']+)', href)
                        if domain_match:
                            domain = self._clean_domain(domain_match.group(1))
                            if domain and self._is_valid_domain(domain, company_name):
                                logger.info(f"Extracted domain via selector: {domain}")
                                return domain

        except Exception as e:
            logger.debug(f"Error parsing HTML: {e}")

        return None

    async def _fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch directory page HTML

        Args:
            url: URL to fetch

        Returns:
            HTML content or None
        """
        # Try standard request first
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers,
                                      timeout=aiohttp.ClientTimeout(total=15)) as response:

                    if response.status == 200:
                        return await response.text()

        except Exception as e:
            logger.debug(f"Standard fetch failed: {e}")

        # Fallback to ZenRows if available
        if self.zenrows_api_key:
            return await self._fetch_with_zenrows(url)

        return None

    async def _fetch_with_zenrows(self, url: str) -> Optional[str]:
        """Fetch using ZenRows (anti-bot protection)"""
        zenrows_url = "https://api.zenrows.com/v1/"

        params = {
            'url': url,
            'apikey': self.zenrows_api_key,
            'js_render': 'false',
            'premium_proxy': 'false'
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(zenrows_url, params=params,
                                      timeout=aiohttp.ClientTimeout(total=20)) as response:

                    if response.status == 200:
                        logger.info(f"Fetched {url} via ZenRows")
                        return await response.text()

        except Exception as e:
            logger.error(f"ZenRows fetch failed: {e}")

        return None

    def _clean_domain(self, domain: str) -> Optional[str]:
        """
        Clean and normalize domain

        Args:
            domain: Raw domain string

        Returns:
            Cleaned domain or None
        """
        if not domain:
            return None

        # Remove protocol
        domain = re.sub(r'https?://', '', domain)
        # Remove www
        domain = re.sub(r'^www\.', '', domain)
        # Remove path
        domain = domain.split('/')[0]
        # Remove port
        domain = domain.split(':')[0]
        # Remove quotes
        domain = domain.strip('\'"')

        # Validate basic format
        if '.' not in domain or len(domain) < 4:
            return None

        return domain.lower()

    def _is_valid_domain(self, domain: str, company_name: str) -> bool:
        """
        Validate that domain is not a directory site or noise

        Args:
            domain: Candidate domain
            company_name: Expected company name

        Returns:
            True if valid, False if noise
        """
        # Filter out directory sites themselves
        directory_domains = [
            'zoominfo.com', 'crunchbase.com', 'apollo.io', 'linkedin.com',
            'facebook.com', 'twitter.com', 'instagram.com', 'youtube.com',
            'google.com', 'bing.com', 'yahoo.com'
        ]

        for dir_domain in directory_domains:
            if dir_domain in domain:
                return False

        # Filter out common noise domains
        noise_domains = [
            'example.com', 'test.com', 'localhost', 'domain.com',
            'website.com', 'email.com'
        ]

        if any(noise in domain for noise in noise_domains):
            return False

        return True


async def search_directories(company_name: str, serper_api_key: str,
                             zenrows_api_key: Optional[str] = None,
                             context: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Convenience function to search all directories

    Args:
        company_name: Company name to search
        serper_api_key: Serper API key
        zenrows_api_key: Optional ZenRows API key
        context: Optional industry/context

    Returns:
        List of domain results from directories
    """
    scraper = DirectoryScraper(serper_api_key, zenrows_api_key)
    results = await scraper.search_directories(company_name, context)
    return results
