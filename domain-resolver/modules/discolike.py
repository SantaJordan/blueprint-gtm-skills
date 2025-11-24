"""
Discolike API integration module
Company enrichment and domain verification
"""
import aiohttp
import logging
from typing import Optional, Dict, Any

from .utils import clean_domain

logger = logging.getLogger(__name__)


class DiscolikeClient:
    """Async client for Discolike API"""

    def __init__(self, api_key: str, timeout: int = 30):
        self.api_key = api_key
        self.timeout = timeout
        self.base_url = "https://api.discolike.com/v1"

    async def enrich_company(self, company_name: str,
                            city: Optional[str] = None,
                            country: str = "US") -> Dict[str, Any]:
        """
        Enrich company data via Discolike API

        Args:
            company_name: Company name
            city: Optional city/location
            country: Country code (default: US)

        Returns:
            API response dict with company data
        """
        url = f"{self.base_url}/company/enrich"

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        payload = {
            'name': company_name
        }

        if city:
            payload['location'] = city

        if country:
            payload['country'] = country

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers,
                                   timeout=aiohttp.ClientTimeout(total=self.timeout)) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    logger.debug(f"Company not found in Discolike: {company_name}")
                    return {}
                else:
                    logger.error(f"Discolike API error {response.status} for {company_name}")
                    return {}


async def resolve_via_discolike(client: DiscolikeClient, company_data: Dict[str, Any],
                                config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Stage 3: Resolve domain via Discolike enrichment

    Args:
        client: DiscolikeClient instance
        company_data: Dict with name, city, etc.
        config: Configuration dict

    Returns:
        Result dict or None if no match
    """
    name = company_data.get('name')
    city = company_data.get('city')

    if not name:
        return None

    logger.info(f"Discolike enrichment: {name}")

    try:
        response = await client.enrich_company(name, city=city)

        if not response or 'domain' not in response:
            logger.debug(f"No domain from Discolike for: {name}")
            return None

        domain = clean_domain(response['domain'])

        if not domain:
            return None

        # Discolike filters parked domains automatically
        # So we can trust the result with high confidence

        confidence = 90  # High confidence from specialized B2B data provider

        # Boost confidence if additional signals match
        if 'phone' in response and company_data.get('phone'):
            # Phone verification would require fuzzy matching
            # For now, just boost confidence if phone exists
            confidence = min(confidence + 5, 95)

        logger.info(f"✓ Discolike match: {domain} (confidence: {confidence})")

        return {
            'domain': domain,
            'confidence': confidence,
            'source': 'discolike',
            'method': 'b2b_enrichment',
            'details': {
                'company_size': response.get('employee_count'),
                'industry': response.get('industry'),
                'revenue': response.get('revenue_range')
            }
        }

    except Exception as e:
        logger.error(f"Discolike error for {name}: {e}")
        return None
