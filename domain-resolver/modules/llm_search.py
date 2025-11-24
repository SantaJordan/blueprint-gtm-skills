"""
LLM-Powered Search Strategy

Uses local LLM (Ollama) to generate intelligent search queries for finding
company websites when minimal data is available.

This is particularly useful for Tier 3/4 cases where we only have:
- Company name + context (no location)
- Company name only

The LLM generates multiple search query variations and helps analyze results.
"""

import httpx
import json
import logging
from typing import Dict, List, Any, Optional
import asyncio
import re

logger = logging.getLogger(__name__)


class LLMSearchStrategy:
    """Uses LLM to generate intelligent search strategies"""

    def __init__(self, endpoint: str = "http://localhost:11434/api/generate",
                 model: str = "llama3.2:3b", timeout: int = 20):
        """
        Initialize LLM search strategist

        Args:
            endpoint: Ollama API endpoint
            model: Model name (prefer fast models like llama3.2:3b)
            timeout: Request timeout
        """
        self.endpoint = endpoint
        self.model = model
        self.timeout = timeout

    async def generate_search_queries(self, company_data: Dict[str, Any],
                                     num_queries: int = 5) -> List[str]:
        """
        Generate multiple search query variations for a company

        Args:
            company_data: Dict with name, context, etc.
            num_queries: Number of query variations to generate (default: 5)

        Returns:
            List of search query strings
        """
        company_name = company_data.get('name', '')
        context = company_data.get('context', '')
        city = company_data.get('city', '')

        prompt = f"""Generate {num_queries} Google search queries to find the official website for this company:

Company Name: {company_name}
Industry/Context: {context if context else 'Unknown'}
Location: {city if city else 'Unknown'}

**Requirements:**
1. Each query should be different (vary the approach)
2. Include variations like:
   - "{company_name} official website"
   - "{company_name} {context} company"
   - "{company_name} headquarters"
   - Industry-specific terms
3. Avoid overly long queries (5-8 words max)
4. Return ONLY valid JSON array of strings

**Example Output:**
["OpenAI official website", "OpenAI artificial intelligence company", "OpenAI San Francisco headquarters", "OpenAI GPT company", "OpenAI research lab"]

Return JSON array only:"""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.endpoint,
                    json={
                        'model': self.model,
                        'prompt': prompt,
                        'stream': False,
                        'format': 'json',
                        'options': {
                            'temperature': 0.7,  # Higher temperature for diversity
                            'num_predict': 256
                        }
                    },
                    timeout=self.timeout
                )

                if response.status_code != 200:
                    logger.error(f"LLM error: {response.status_code}")
                    return self._fallback_queries(company_data)

                result = response.json()
                llm_response = result.get('response', '')

                # Parse JSON array
                queries = self._parse_query_list(llm_response)

                if not queries:
                    logger.warning("LLM returned no valid queries, using fallback")
                    return self._fallback_queries(company_data)

                logger.info(f"Generated {len(queries)} search queries via LLM")
                return queries[:num_queries]

        except Exception as e:
            logger.error(f"Error generating queries: {e}")
            return self._fallback_queries(company_data)

    def _parse_query_list(self, llm_response: str) -> List[str]:
        """Parse LLM response as JSON array of queries"""

        try:
            # Try direct JSON parse
            parsed = json.loads(llm_response)
            if isinstance(parsed, list):
                # Filter out empty strings
                return [str(q).strip() for q in parsed if q]

        except json.JSONDecodeError:
            logger.debug("JSON parse failed, trying regex extraction")

        # Fallback: Extract quoted strings
        pattern = r'["\']([^"\']+)["\']'
        matches = re.findall(pattern, llm_response)

        if matches:
            return matches

        return []

    def _fallback_queries(self, company_data: Dict[str, Any]) -> List[str]:
        """Generate fallback queries without LLM"""

        name = company_data.get('name', '')
        context = company_data.get('context', '')
        city = company_data.get('city', '')

        queries = [
            f"{name} official website",
            f"{name} company",
        ]

        if context:
            queries.extend([
                f"{name} {context}",
                f"{name} {context} company"
            ])

        if city:
            queries.append(f"{name} {city}")

        queries.append(f"{name} headquarters")

        return queries[:5]

    async def analyze_search_results(self, company_data: Dict[str, Any],
                                    search_results: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Use LLM to analyze search results and pick best domain candidate

        Args:
            company_data: Expected company data
            search_results: List of search results [{title, link, snippet}, ...]

        Returns:
            Best result dict or None
        """
        if not search_results:
            return None

        company_name = company_data.get('name', '')
        context = company_data.get('context', '')

        # Build prompt with search results
        results_text = "\n".join([
            f"{i+1}. Title: {r.get('title', '')}\n   URL: {r.get('link', '')}\n   Snippet: {r.get('snippet', '')}"
            for i, r in enumerate(search_results[:10])  # Top 10 results
        ])

        prompt = f"""Analyze these Google search results and identify which URL is most likely the official website for this company:

**Target Company:**
- Name: {company_name}
- Industry: {context if context else 'Unknown'}

**Search Results:**
{results_text}

**Task:**
Pick the result number (1-{min(10, len(search_results))}) that is most likely the company's official website.
Avoid: Wikipedia, LinkedIn, Facebook, news articles, review sites.
Prefer: Official company domains, .com sites.

Return ONLY valid JSON:
{{
  "result_number": 1-{min(10, len(search_results))},
  "confidence": 0-100,
  "reasoning": "brief explanation"
}}

JSON only:"""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.endpoint,
                    json={
                        'model': self.model,
                        'prompt': prompt,
                        'stream': False,
                        'format': 'json',
                        'options': {
                            'temperature': 0.1,  # Low temp for consistent choice
                            'num_predict': 128
                        }
                    },
                    timeout=self.timeout
                )

                if response.status_code != 200:
                    logger.error(f"LLM analysis error: {response.status_code}")
                    return None

                result = response.json()
                llm_response = result.get('response', '')

                # Parse response
                analysis = self._parse_analysis(llm_response)

                if not analysis or analysis.get('result_number') is None:
                    return None

                result_num = analysis['result_number']
                if 1 <= result_num <= len(search_results):
                    selected_result = search_results[result_num - 1]
                    selected_result['llm_confidence'] = analysis.get('confidence', 50)
                    selected_result['llm_reasoning'] = analysis.get('reasoning', '')

                    logger.info(f"LLM selected result #{result_num}: {selected_result.get('link')}")
                    return selected_result

                return None

        except Exception as e:
            logger.error(f"Error analyzing results: {e}")
            return None

    def _parse_analysis(self, llm_response: str) -> Dict[str, Any]:
        """Parse LLM analysis response"""

        try:
            parsed = json.loads(llm_response)
            if isinstance(parsed, dict):
                return {
                    'result_number': int(parsed.get('result_number', 0)),
                    'confidence': int(parsed.get('confidence', 50)),
                    'reasoning': str(parsed.get('reasoning', ''))
                }

        except:
            pass

        # Fallback: regex extraction
        result_match = re.search(r'result_number["\']?\s*:\s*(\d+)', llm_response)
        conf_match = re.search(r'confidence["\']?\s*:\s*(\d+)', llm_response)

        if result_match:
            return {
                'result_number': int(result_match.group(1)),
                'confidence': int(conf_match.group(1)) if conf_match else 50,
                'reasoning': ''
            }

        return {}


async def llm_powered_search(company_data: Dict[str, Any],
                            serper_api_key: str,
                            llm_endpoint: str = "http://localhost:11434/api/generate",
                            llm_model: str = "llama3.2:3b") -> Optional[Dict[str, Any]]:
    """
    Convenience function for LLM-powered search

    Args:
        company_data: Company information
        serper_api_key: Serper API key for Google search
        llm_endpoint: Ollama endpoint
        llm_model: LLM model name

    Returns:
        {
            'domain': str,
            'source': 'llm_search',
            'confidence': int,
            'method': 'llm_query_generation'
        } or None
    """
    import aiohttp

    strategy = LLMSearchStrategy(llm_endpoint, llm_model)

    # Generate search queries
    queries = await strategy.generate_search_queries(company_data, num_queries=3)

    logger.info(f"LLM generated queries: {queries}")

    # Execute searches
    all_results = []
    for query in queries:
        # Search via Serper
        url = "https://google.serper.dev/search"
        headers = {
            'X-API-KEY': serper_api_key,
            'Content-Type': 'application/json'
        }
        payload = {'q': query, 'num': 10}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers,
                                       timeout=aiohttp.ClientTimeout(total=10)) as response:

                    if response.status == 200:
                        data = await response.json()
                        organic = data.get('organic', [])
                        all_results.extend(organic)

        except Exception as e:
            logger.error(f"Search error for query '{query}': {e}")

    if not all_results:
        logger.warning("No search results from LLM queries")
        return None

    # Deduplicate results by link
    unique_results = {}
    for result in all_results:
        link = result.get('link')
        if link and link not in unique_results:
            unique_results[link] = result

    results_list = list(unique_results.values())

    # Use LLM to analyze and pick best result
    best_result = await strategy.analyze_search_results(company_data, results_list)

    if not best_result:
        logger.warning("LLM could not identify best result")
        return None

    # Extract domain
    link = best_result.get('link', '')
    domain_match = re.search(r'https?://(?:www\.)?([^/"\']+)', link)

    if not domain_match:
        return None

    domain = domain_match.group(1)

    return {
        'domain': domain,
        'source': 'llm_search',
        'confidence': int(best_result.get('llm_confidence', 60)),
        'method': 'llm_query_generation',
        'reasoning': best_result.get('llm_reasoning', '')
    }
