"""
Serper.dev API integration module
Handles Places API and Search API with Knowledge Graph detection
"""
import aiohttp
import logging
from typing import Optional, Dict, Any, List

from .utils import clean_domain, phone_fuzzy_match, is_blacklisted, create_search_query
from .fuzzy_matcher import calculate_advanced_score
from .parking_detector import is_parked_domain

logger = logging.getLogger(__name__)


class SerperClient:
    """Async client for Serper.dev API"""

    def __init__(self, api_key: str, timeout: int = 30):
        self.api_key = api_key
        self.timeout = timeout
        self.base_url = "https://google.serper.dev"

    async def places_search(self, query: str) -> Dict[str, Any]:
        """
        Query Serper Places API (Google Maps business listings)

        Args:
            query: Search query

        Returns:
            API response dict
        """
        url = f"{self.base_url}/places"

        headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }

        payload = {
            'q': query
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers,
                                   timeout=aiohttp.ClientTimeout(total=self.timeout)) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Serper Places API error: {response.status}")
                    return {}

    async def search(self, query: str, num_results: int = 10) -> Dict[str, Any]:
        """
        Query Serper Search API (Google Search with Knowledge Graph)

        Args:
            query: Search query
            num_results: Number of results to return

        Returns:
            API response dict with organic results and knowledgeGraph if available
        """
        url = f"{self.base_url}/search"

        headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }

        payload = {
            'q': query,
            'num': num_results
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers,
                                   timeout=aiohttp.ClientTimeout(total=self.timeout)) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Serper Search API error: {response.status}")
                    return {}


async def resolve_via_places(client: SerperClient, company_data: Dict[str, Any],
                             config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Stage 1: Resolve domain via Serper Places API
    This is the "Gold Layer" with highest confidence

    Args:
        client: SerperClient instance
        company_data: Dict with name, city, phone, etc.
        config: Configuration dict

    Returns:
        Result dict or None if no match
    """
    name = company_data.get('name')
    city = company_data.get('city')
    phone = company_data.get('phone')

    if not name:
        return None

    # Create query
    query = create_search_query(name, city, query_type="places")

    logger.info(f"Places search: {query}")

    try:
        response = await client.places_search(query)

        if not response or 'places' not in response:
            logger.debug(f"No places found for: {name}")
            return None

        places = response.get('places', [])

        for place in places[:3]:  # Check top 3 results
            place_website = place.get('website')
            place_phone = place.get('phoneNumber') or place.get('phone')

            if not place_website:
                continue

            # Clean domain
            domain = clean_domain(place_website)

            if not domain:
                continue

            # Phone number verification (if available)
            phone_match = False
            if phone and place_phone:
                phone_match = phone_fuzzy_match(phone, place_phone, min_digits=4)

            # Medium-high confidence if phone matches (lowered from 99 to ensure LLM verification)
            # Parent companies often share phone numbers across facilities
            if phone_match:
                logger.info(f"✓ Places match with phone verification: {domain}")
                return {
                    'domain': domain,
                    'confidence': 75,  # Lowered from 99 to force LLM verification
                    'source': 'google_places',
                    'method': 'phone_verified',
                    'details': {
                        'place_name': place.get('title'),
                        'place_phone': place_phone,
                        'address': place.get('address')
                    }
                }

            # Medium-high confidence if place name matches well
            place_name = place.get('title', '')
            if place_name:
                # Use fuzzy matching
                score_result = calculate_advanced_score(
                    company_name=name,
                    url=domain,
                    context=company_data.get('context'),
                    config=config.get('fuzzy_matching', {})
                )

                if score_result['score'] >= 85:
                    logger.info(f"✓ Places match with name similarity: {domain} (score: {score_result['score']})")
                    return {
                        'domain': domain,
                        'confidence': score_result['score'],
                        'source': 'google_places',
                        'method': 'name_matched',
                        'details': {
                            'place_name': place_name,
                            'fuzzy_score': score_result['score'],
                            'place_phone': place_phone
                        }
                    }

    except Exception as e:
        logger.error(f"Places API error for {name}: {e}")

    return None


async def resolve_via_search(client: SerperClient, company_data: Dict[str, Any],
                             config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Stage 2: Resolve domain via Serper Search API
    Checks Knowledge Graph first, then fuzzy matches organic results

    Args:
        client: SerperClient instance
        company_data: Dict with name, city, context, etc.
        config: Configuration dict

    Returns:
        Result dict or None if no match
    """
    name = company_data.get('name')
    city = company_data.get('city')
    context = company_data.get('context')
    phone = company_data.get('phone')

    if not name:
        return None

    # Create optimized query
    query = create_search_query(name, city, context, query_type="official")

    logger.info(f"Search query: {query}")

    try:
        response = await client.search(query, num_results=10)

        if not response:
            return None

        # === Check 1: Knowledge Graph (Highest Trust) ===
        kg = response.get('knowledgeGraph')
        if kg and 'website' in kg:
            kg_website = kg['website']
            domain = clean_domain(kg_website)

            if domain:
                logger.info(f"✓ Knowledge Graph match: {domain}")
                return {
                    'domain': domain,
                    'confidence': 98,
                    'source': 'google_kg',
                    'method': 'knowledge_graph',
                    'details': {
                        'kg_title': kg.get('title'),
                        'kg_type': kg.get('type')
                    }
                }

        # === Check 2: Organic Results with Fuzzy Matching ===
        organic_results = response.get('organic', [])

        if not organic_results:
            logger.debug(f"No organic results for: {name}")
            return None

        blacklist = config.get('blacklist_domains', [])

        # Filter and score candidates
        candidates = []

        for result in organic_results[:5]:  # Top 5 results
            url = result.get('link')
            snippet = result.get('snippet', '')

            if not url:
                continue

            # Blacklist check
            if is_blacklisted(url, blacklist):
                logger.debug(f"Blacklisted: {url}")
                continue

            # Parking detection (quick check on snippet)
            is_parked, parking_reason = is_parked_domain(snippet, url)
            if is_parked:
                logger.debug(f"Parked domain detected: {url} ({parking_reason})")
                continue

            # Calculate fuzzy score
            score_result = calculate_advanced_score(
                company_name=name,
                url=url,
                context=context,
                snippet=snippet,
                phone=phone,
                config=config.get('fuzzy_matching', {})
            )

            candidates.append({
                'url': url,
                'domain': clean_domain(url),
                'score': score_result['score'],
                'method': score_result['method'],
                'details': score_result['details'],
                'snippet': snippet,
                'position': result.get('position', 0)
            })

        # Sort by score (descending)
        candidates.sort(key=lambda x: x['score'], reverse=True)

        if not candidates:
            logger.debug(f"No valid candidates after filtering for: {name}")
            return None

        # Return best candidate
        best = candidates[0]

        logger.info(f"Best match: {best['domain']} (score: {best['score']}, method: {best['method']})")

        return {
            'domain': best['domain'],
            'confidence': best['score'],
            'source': 'serper_search',
            'method': best['method'],
            'details': {
                'position': best['position'],
                'fuzzy_details': best['details'],
                'snippet': best['snippet'][:200]  # Truncate
            }
        }

    except Exception as e:
        logger.error(f"Search API error for {name}: {e}")

    return None


async def resolve_company(client: SerperClient, company_data: Dict[str, Any],
                         config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Combined resolver: Try Places first, fallback to Search

    Args:
        client: SerperClient instance
        company_data: Company information dict
        config: Configuration dict

    Returns:
        Best resolution result or None
    """
    result = None

    # Stage 1: Places API (if enabled)
    if config.get('stages', {}).get('use_places', True):
        result = await resolve_via_places(client, company_data, config)

        if result and result.get('confidence', 0) >= config.get('thresholds', {}).get('auto_accept', 85):
            logger.info(f"✓✓ High confidence from Places: {result['domain']}")
            return result

    # Stage 2: Search API (if enabled)
    if config.get('stages', {}).get('use_search', True):
        search_result = await resolve_via_search(client, company_data, config)

        # Use search result if better than places result or if no places result
        if search_result:
            if not result or search_result.get('confidence', 0) > result.get('confidence', 0):
                result = search_result

    return result
