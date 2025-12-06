"""
WebSearch - Search tool using Serper API to replace Claude Code's WebSearch.
Performs Google searches and returns structured results.
"""
import httpx
import asyncio
from typing import Dict, List, Optional


class WebSearch:
    """Async search client using Serper API."""

    BASE_URL = "https://google.serper.dev/search"

    def __init__(self, api_key: str, timeout: int = 30):
        self.api_key = api_key
        self.timeout = timeout

    async def search(
        self,
        query: str,
        num_results: int = 10,
        search_type: str = "search"
    ) -> Dict:
        """
        Perform a Google search.

        Args:
            query: Search query string
            num_results: Number of results to return (max 100)
            search_type: Type of search (search, news, images)

        Returns:
            {
                "query": str,
                "organic": [
                    {
                        "title": str,
                        "link": str,
                        "snippet": str,
                        "position": int
                    }
                ],
                "knowledgeGraph": {...} | None,
                "answerBox": {...} | None,
                "success": bool,
                "error": str | None
            }
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.BASE_URL,
                    headers={
                        "X-API-KEY": self.api_key,
                        "Content-Type": "application/json"
                    },
                    json={
                        "q": query,
                        "num": num_results,
                        "gl": "us",
                        "hl": "en"
                    }
                )

                if response.status_code != 200:
                    return {
                        "query": query,
                        "organic": [],
                        "success": False,
                        "error": f"API error: {response.status_code}"
                    }

                data = response.json()

                # Extract and normalize results
                organic = []
                for i, result in enumerate(data.get("organic", [])):
                    organic.append({
                        "title": result.get("title", ""),
                        "link": result.get("link", ""),
                        "snippet": result.get("snippet", ""),
                        "position": i + 1
                    })

                return {
                    "query": query,
                    "organic": organic,
                    "knowledgeGraph": data.get("knowledgeGraph"),
                    "answerBox": data.get("answerBox"),
                    "peopleAlsoAsk": data.get("peopleAlsoAsk", []),
                    "relatedSearches": data.get("relatedSearches", []),
                    "success": True,
                    "error": None
                }

        except httpx.TimeoutException:
            return {
                "query": query,
                "organic": [],
                "success": False,
                "error": "Search timeout"
            }
        except Exception as e:
            return {
                "query": query,
                "organic": [],
                "success": False,
                "error": str(e)
            }

    async def search_parallel(self, queries: List[str], num_results: int = 10) -> List[Dict]:
        """
        Perform multiple searches in parallel.

        Args:
            queries: List of search queries
            num_results: Number of results per query

        Returns:
            List of search results in same order as queries
        """
        tasks = [self.search(query, num_results) for query in queries]
        return await asyncio.gather(*tasks)

    def format_results(self, results: Dict) -> str:
        """Format search results as readable text."""
        if not results.get("success"):
            return f"Search failed: {results.get('error', 'Unknown error')}"

        lines = [f"Search: {results['query']}\n"]

        # Add answer box if present
        if results.get("answerBox"):
            ab = results["answerBox"]
            lines.append(f"Answer: {ab.get('answer', ab.get('snippet', ''))}\n")

        # Add organic results
        for r in results.get("organic", []):
            lines.append(f"{r['position']}. {r['title']}")
            lines.append(f"   {r['link']}")
            lines.append(f"   {r['snippet']}\n")

        return "\n".join(lines)


# Convenience functions
async def search_google(query: str, api_key: str, num_results: int = 10) -> Dict:
    """Quick search with Serper API."""
    searcher = WebSearch(api_key)
    return await searcher.search(query, num_results)


async def search_multiple(queries: List[str], api_key: str, num_results: int = 10) -> List[Dict]:
    """Quick parallel search."""
    searcher = WebSearch(api_key)
    return await searcher.search_parallel(queries, num_results)
