"""
WebFetch - HTTP fetching tool to replace Claude Code's WebFetch.
Fetches web pages and returns content as text.
"""
import httpx
import asyncio
from typing import Dict, List, Optional
from html import unescape
import re


class WebFetch:
    """Async HTTP client for fetching web pages."""

    def __init__(self, timeout: int = 30, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

    async def fetch(self, url: str) -> Dict:
        """
        Fetch a single URL and return its content.

        Returns:
            {
                "url": str,          # Final URL after redirects
                "content": str,      # Raw HTML content
                "text": str,         # Extracted text content
                "title": str,        # Page title if found
                "status": int,       # HTTP status code
                "success": bool,     # Whether fetch succeeded
                "error": str | None  # Error message if failed
            }
        """
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(
                    timeout=self.timeout,
                    follow_redirects=True,
                    headers=self.headers
                ) as client:
                    response = await client.get(url)

                    content = response.text
                    text = self._extract_text(content)
                    title = self._extract_title(content)

                    return {
                        "url": str(response.url),
                        "content": content[:100000],  # Limit content size
                        "text": text[:50000],  # Limit text size
                        "title": title,
                        "status": response.status_code,
                        "success": response.status_code == 200,
                        "error": None
                    }
            except httpx.TimeoutException:
                if attempt == self.max_retries - 1:
                    return self._error_response(url, "Timeout")
                await asyncio.sleep(1 * (attempt + 1))
            except httpx.HTTPError as e:
                if attempt == self.max_retries - 1:
                    return self._error_response(url, str(e))
                await asyncio.sleep(1 * (attempt + 1))
            except Exception as e:
                return self._error_response(url, str(e))

        return self._error_response(url, "Max retries exceeded")

    async def fetch_parallel(self, urls: List[str]) -> List[Dict]:
        """Fetch multiple URLs in parallel."""
        tasks = [self.fetch(url) for url in urls]
        return await asyncio.gather(*tasks)

    def _error_response(self, url: str, error: str) -> Dict:
        """Create error response."""
        return {
            "url": url,
            "content": "",
            "text": "",
            "title": "",
            "status": 0,
            "success": False,
            "error": error
        }

    def _extract_title(self, html: str) -> str:
        """Extract page title from HTML."""
        match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
        if match:
            return unescape(match.group(1).strip())
        return ""

    def _extract_text(self, html: str) -> str:
        """Extract readable text from HTML, removing scripts, styles, etc."""
        # Remove script and style elements
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<noscript[^>]*>.*?</noscript>', '', text, flags=re.DOTALL | re.IGNORECASE)

        # Remove HTML comments
        text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)

        # Remove all HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)

        # Decode HTML entities
        text = unescape(text)

        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)

        return text.strip()


# Convenience function for quick fetches
async def fetch_url(url: str) -> Dict:
    """Quick fetch a single URL."""
    fetcher = WebFetch()
    return await fetcher.fetch(url)


async def fetch_urls(urls: List[str]) -> List[Dict]:
    """Quick fetch multiple URLs in parallel."""
    fetcher = WebFetch()
    return await fetcher.fetch_parallel(urls)
