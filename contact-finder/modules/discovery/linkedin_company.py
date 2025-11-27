"""
LinkedIn Company Discovery
Find company LinkedIn URLs using multiple sources in parallel
"""

import asyncio
import aiohttp
import re
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import quote_plus

from ..validation.linkedin_normalizer import (
    normalize_linkedin_url,
    is_valid_linkedin_company_url,
    extract_linkedin_company_slug
)


@dataclass
class CompanyLinkedInResult:
    """Result of LinkedIn company discovery"""
    company_name: str
    domain: str | None
    linkedin_url: str | None  # Normalized: linkedin.com/company/xxx
    linkedin_slug: str | None
    confidence: float  # 0-100
    source: str  # serper, scrapin, exa, site_scrape
    evidence: list[str] = field(default_factory=list)
    all_candidates: list[dict] = field(default_factory=list)


class LinkedInCompanyDiscovery:
    """
    Find company LinkedIn URLs using multiple sources.

    Priority (cost-optimized):
    1. Scrapin (FREE) - company search by domain
    2. Exa (FREE) - semantic search
    3. Serper (cheap) - Google search
    4. Site scrape (free) - look on company website
    """

    def __init__(
        self,
        serper_api_key: str | None = None,
        scrapin_client: Any = None,
        exa_client: Any = None,
        timeout: int = 30
    ):
        self.serper_api_key = serper_api_key
        self.scrapin = scrapin_client
        self.exa = exa_client
        self.timeout = timeout
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def _search_serper(
        self,
        company_name: str,
        domain: str | None = None,
        location: str | None = None
    ) -> list[dict]:
        """
        Search for company LinkedIn using Serper (Google).

        Returns list of candidates with url, title, confidence.
        """
        if not self.serper_api_key:
            return []

        candidates = []

        try:
            session = await self._get_session()

            # Build search query
            query_parts = [f'"{company_name}"', 'site:linkedin.com/company']
            if location:
                query_parts.append(f'"{location}"')

            query = " ".join(query_parts)

            async with session.post(
                "https://google.serper.dev/search",
                headers={
                    "X-API-KEY": self.serper_api_key,
                    "Content-Type": "application/json"
                },
                json={"q": query, "num": 5}
            ) as response:
                if response.status == 200:
                    data = await response.json()

                    for result in data.get("organic", [])[:5]:
                        url = result.get("link", "")
                        if "linkedin.com/company" in url:
                            normalized = normalize_linkedin_url(url)
                            if normalized:
                                candidates.append({
                                    "url": normalized,
                                    "title": result.get("title", ""),
                                    "snippet": result.get("snippet", ""),
                                    "source": "serper",
                                    "position": result.get("position", 0)
                                })
        except Exception as e:
            pass  # Silently fail, other sources will try

        return candidates

    async def _search_scrapin(
        self,
        company_name: str,
        domain: str | None = None
    ) -> list[dict]:
        """
        Search using Scrapin (FREE).

        Returns list of candidates.
        """
        if not self.scrapin:
            return []

        candidates = []

        try:
            # Search by domain if available
            if domain:
                result = await self.scrapin.search_company(domain=domain)
                if result.linkedin_url:
                    normalized = normalize_linkedin_url(result.linkedin_url)
                    if normalized:
                        candidates.append({
                            "url": normalized,
                            "title": result.name or company_name,
                            "snippet": result.description or "",
                            "source": "scrapin",
                            "confidence_boost": 20  # Domain match = high confidence
                        })

            # Also search by name
            result = await self.scrapin.search_company(company_name=company_name)
            if result.linkedin_url:
                normalized = normalize_linkedin_url(result.linkedin_url)
                if normalized and not any(c["url"] == normalized for c in candidates):
                    candidates.append({
                        "url": normalized,
                        "title": result.name or company_name,
                        "snippet": result.description or "",
                        "source": "scrapin",
                        "confidence_boost": 0
                    })
        except Exception:
            pass

        return candidates

    async def _search_exa(
        self,
        company_name: str,
        location: str | None = None
    ) -> list[dict]:
        """
        Search using Exa semantic search (FREE).

        Returns list of candidates.
        """
        if not self.exa:
            return []

        candidates = []

        try:
            linkedin_url = await self.exa.find_linkedin_company(
                company_name=company_name,
                location=location
            )

            if linkedin_url:
                normalized = normalize_linkedin_url(linkedin_url)
                if normalized:
                    candidates.append({
                        "url": normalized,
                        "title": company_name,
                        "snippet": "",
                        "source": "exa",
                        "confidence_boost": 10  # Semantic search confidence
                    })
        except Exception:
            pass

        return candidates

    async def _scrape_website_for_linkedin(
        self,
        domain: str
    ) -> list[dict]:
        """
        Scrape company website looking for LinkedIn link.

        Returns list of candidates.
        """
        if not domain:
            return []

        candidates = []

        try:
            session = await self._get_session()

            # Try homepage and about page
            urls_to_try = [
                f"https://{domain}",
                f"https://{domain}/about",
                f"https://{domain}/contact"
            ]

            linkedin_pattern = re.compile(
                r'https?://(?:www\.)?linkedin\.com/company/([a-zA-Z0-9\-_]+)',
                re.I
            )

            for url in urls_to_try:
                try:
                    async with session.get(
                        url,
                        headers={"User-Agent": "Mozilla/5.0"},
                        allow_redirects=True,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        if response.status == 200:
                            html = await response.text()

                            matches = linkedin_pattern.findall(html)
                            for slug in matches[:3]:  # Take first 3 unique
                                normalized = f"linkedin.com/company/{slug}"
                                if not any(c["url"] == normalized for c in candidates):
                                    candidates.append({
                                        "url": normalized,
                                        "title": "",
                                        "snippet": f"Found on {url}",
                                        "source": "site_scrape",
                                        "confidence_boost": 30  # Found on company site = very high confidence
                                    })
                except Exception:
                    continue
        except Exception:
            pass

        return candidates

    def _calculate_confidence(
        self,
        candidate: dict,
        company_name: str,
        domain: str | None
    ) -> float:
        """Calculate confidence score for a candidate"""
        score = 50.0  # Base score

        # Source confidence
        source_scores = {
            "site_scrape": 30,
            "scrapin": 20,
            "exa": 15,
            "serper": 10
        }
        score += source_scores.get(candidate.get("source", ""), 0)

        # Confidence boost from source
        score += candidate.get("confidence_boost", 0)

        # Name matching
        title = candidate.get("title", "").lower()
        company_lower = company_name.lower()

        # Exact name in title
        if company_lower in title:
            score += 15

        # URL slug contains company name parts
        url = candidate.get("url", "")
        slug = extract_linkedin_company_slug(url) or ""
        slug_lower = slug.lower().replace("-", " ").replace("_", " ")

        name_parts = company_lower.split()
        matching_parts = sum(1 for part in name_parts if part in slug_lower and len(part) > 2)
        if matching_parts > 0:
            score += min(matching_parts * 5, 15)

        # Position penalty (for search results)
        position = candidate.get("position", 0)
        if position > 1:
            score -= (position - 1) * 3

        return max(0, min(100, score))

    async def discover(
        self,
        company_name: str,
        domain: str | None = None,
        location: str | None = None
    ) -> CompanyLinkedInResult:
        """
        Discover company LinkedIn URL using all available sources in parallel.

        Args:
            company_name: Company name
            domain: Company domain (optional but recommended)
            location: Location for disambiguation (optional)

        Returns:
            CompanyLinkedInResult with best match and all candidates
        """
        # Run all sources in parallel
        tasks = [
            self._search_scrapin(company_name, domain),
            self._search_exa(company_name, location),
            self._search_serper(company_name, domain, location),
            self._scrape_website_for_linkedin(domain) if domain else asyncio.coroutine(lambda: [])()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect all candidates
        all_candidates = []
        for result in results:
            if isinstance(result, list):
                all_candidates.extend(result)

        # Calculate confidence for each
        for candidate in all_candidates:
            candidate["confidence"] = self._calculate_confidence(
                candidate, company_name, domain
            )

        # Sort by confidence
        all_candidates.sort(key=lambda x: x.get("confidence", 0), reverse=True)

        # Deduplicate by URL, keeping highest confidence
        seen_urls = set()
        unique_candidates = []
        for c in all_candidates:
            url = c.get("url")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_candidates.append(c)

        # Build evidence
        evidence = []
        for c in unique_candidates[:3]:
            ev = f"{c.get('source')}: {c.get('url')} (confidence: {c.get('confidence', 0):.0f})"
            if c.get("snippet"):
                ev += f" - {c.get('snippet', '')[:100]}"
            evidence.append(ev)

        # Get best result
        best = unique_candidates[0] if unique_candidates else None

        return CompanyLinkedInResult(
            company_name=company_name,
            domain=domain,
            linkedin_url=best.get("url") if best else None,
            linkedin_slug=extract_linkedin_company_slug(best.get("url")) if best else None,
            confidence=best.get("confidence", 0) if best else 0,
            source=best.get("source", "none") if best else "none",
            evidence=evidence,
            all_candidates=unique_candidates
        )


# Convenience function
async def test_linkedin_discovery(
    company_name: str,
    domain: str | None = None,
    serper_key: str | None = None
):
    """Test LinkedIn discovery"""
    discovery = LinkedInCompanyDiscovery(serper_api_key=serper_key)
    try:
        result = await discovery.discover(company_name, domain)
        print(f"Company: {company_name}")
        print(f"LinkedIn: {result.linkedin_url}")
        print(f"Confidence: {result.confidence}")
        print(f"Source: {result.source}")
        print(f"Evidence: {result.evidence}")
        return result
    finally:
        await discovery.close()
