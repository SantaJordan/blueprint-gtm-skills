"""
Exa.ai API Client
https://docs.exa.ai

Features:
- Neural/semantic search optimized for AI
- Company research tool
- Domain expert finder
- Content extraction with highlights
"""

import aiohttp
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExaSearchResult:
    """Individual search result"""
    title: str | None
    url: str | None
    snippet: str | None
    text: str | None
    highlights: list[str] = field(default_factory=list)
    score: float = 0.0
    published_date: str | None = None
    author: str | None = None
    raw_response: dict = field(default_factory=dict)


@dataclass
class ExaSearchResponse:
    """Search response with multiple results"""
    results: list[ExaSearchResult] = field(default_factory=list)
    total_results: int = 0
    raw_response: dict = field(default_factory=dict)


class ExaClient:
    """Exa.ai API client for semantic search"""

    BASE_URL = "https://api.exa.ai"

    def __init__(self, api_key: str, timeout: int = 60):
        self.api_key = api_key
        self.timeout = timeout
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def _post(self, endpoint: str, data: dict) -> dict:
        """Make a POST request to Exa API"""
        session = await self._get_session()
        url = f"{self.BASE_URL}{endpoint}"

        async with session.post(url, json=data) as response:
            if response.status == 401:
                raise ValueError("Invalid Exa API key")
            if response.status == 429:
                raise ValueError("Exa rate limit exceeded")
            result = await response.json()
            return result

    async def search(
        self,
        query: str,
        num_results: int = 10,
        search_type: str = "neural",  # neural, keyword, auto
        include_domains: list[str] | None = None,
        exclude_domains: list[str] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        contents: bool = True,
        highlights: bool = True,
        summary: bool = False
    ) -> ExaSearchResponse:
        """
        Semantic search using Exa

        Args:
            query: Search query (semantic or keyword)
            num_results: Number of results to return (1-100)
            search_type: "neural" (semantic), "keyword", or "auto"
            include_domains: Only search these domains
            exclude_domains: Exclude these domains
            start_date: Filter by date (YYYY-MM-DD)
            end_date: Filter by date (YYYY-MM-DD)
            contents: Include page text content
            highlights: Include relevant highlights
            summary: Include AI summary
        """
        data = {
            "query": query,
            "numResults": min(num_results, 100),
            "type": search_type,
            "useAutoprompt": search_type == "auto",
        }

        if include_domains:
            data["includeDomains"] = include_domains
        if exclude_domains:
            data["excludeDomains"] = exclude_domains
        if start_date:
            data["startPublishedDate"] = start_date
        if end_date:
            data["endPublishedDate"] = end_date

        # Content options
        content_options = {}
        if contents:
            content_options["text"] = True
        if highlights:
            content_options["highlights"] = True
        if summary:
            content_options["summary"] = True

        if content_options:
            data["contents"] = content_options

        try:
            result = await self._post("/search", data)

            results = []
            for item in result.get("results", []):
                results.append(ExaSearchResult(
                    title=item.get("title"),
                    url=item.get("url"),
                    snippet=item.get("snippet"),
                    text=item.get("text"),
                    highlights=item.get("highlights", []),
                    score=item.get("score", 0),
                    published_date=item.get("publishedDate"),
                    author=item.get("author"),
                    raw_response=item
                ))

            return ExaSearchResponse(
                results=results,
                total_results=len(results),
                raw_response=result
            )

        except Exception as e:
            return ExaSearchResponse(
                results=[],
                total_results=0,
                raw_response={"error": str(e)}
            )

    async def find_company_contacts(
        self,
        company_name: str,
        domain: str | None = None,
        titles: list[str] | None = None,
        location: str | None = None,
        num_results: int = 10
    ) -> ExaSearchResponse:
        """
        Find contacts/decision makers at a company using semantic search

        Args:
            company_name: Company name
            domain: Company domain (for site: filtering)
            titles: Target job titles
            location: Location filter
            num_results: Max results
        """
        # Build semantic query
        query_parts = [f'"{company_name}"']

        if titles:
            title_str = " OR ".join([f'"{t}"' for t in titles[:3]])  # Top 3 titles
            query_parts.append(f"({title_str})")

        if location:
            query_parts.append(f'"{location}"')

        query_parts.append("contact OR owner OR manager OR director")

        query = " ".join(query_parts)

        # Domain filtering
        include_domains = None
        if domain:
            include_domains = [domain, "linkedin.com"]
        else:
            include_domains = ["linkedin.com"]

        return await self.search(
            query=query,
            num_results=num_results,
            search_type="neural",
            include_domains=include_domains,
            contents=True,
            highlights=True
        )

    async def company_research(
        self,
        company_name: str,
        domain: str | None = None,
        num_results: int = 5
    ) -> ExaSearchResponse:
        """
        Research a company - get information from their website and news

        Args:
            company_name: Company name
            domain: Company domain
            num_results: Max results
        """
        query = f'"{company_name}" company about team leadership contact'

        include_domains = [domain] if domain else None

        return await self.search(
            query=query,
            num_results=num_results,
            search_type="neural",
            include_domains=include_domains,
            contents=True,
            highlights=True,
            summary=True
        )

    async def find_linkedin_company(
        self,
        company_name: str,
        location: str | None = None
    ) -> str | None:
        """
        Find a company's LinkedIn URL using semantic search

        Args:
            company_name: Company name
            location: Optional location for disambiguation

        Returns:
            LinkedIn company URL or None
        """
        query = f'"{company_name}" company'
        if location:
            query += f' "{location}"'

        result = await self.search(
            query=query,
            num_results=5,
            search_type="neural",
            include_domains=["linkedin.com"],
            contents=False,
            highlights=False
        )

        # Find first linkedin.com/company URL
        for r in result.results:
            if r.url and "linkedin.com/company" in r.url:
                return r.url

        return None

    async def find_linkedin_person(
        self,
        name: str,
        company: str | None = None,
        title: str | None = None
    ) -> str | None:
        """
        Find a person's LinkedIn URL using semantic search

        Args:
            name: Person's name
            company: Company name (optional)
            title: Job title (optional)

        Returns:
            LinkedIn profile URL or None
        """
        query = f'"{name}"'
        if company:
            query += f' "{company}"'
        if title:
            query += f' "{title}"'

        result = await self.search(
            query=query,
            num_results=5,
            search_type="neural",
            include_domains=["linkedin.com"],
            contents=False,
            highlights=False
        )

        # Find first linkedin.com/in URL
        for r in result.results:
            if r.url and "linkedin.com/in" in r.url:
                return r.url

        return None


# Convenience function
async def test_exa_api(api_key: str):
    """Test Exa API connection"""
    client = ExaClient(api_key)
    try:
        result = await client.search("OpenAI company", num_results=1)
        if result.results:
            print(f"Exa API connected. Found: {result.results[0].title}")
            return True
        else:
            print("Exa API connected but no results")
            return True
    except Exception as e:
        print(f"Exa API error: {e}")
        return False
    finally:
        await client.close()
