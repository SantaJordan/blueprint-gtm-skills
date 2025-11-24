"""
Ocean.io API integration module
Company enrichment and domain verification
"""
import aiohttp
import logging
from typing import Optional, Dict, Any

from .utils import clean_domain

logger = logging.getLogger(__name__)


class OceanClient:
    """Async client for Ocean.io API"""

    def __init__(self, api_key: str, timeout: int = 30):
        self.api_key = api_key
        self.timeout = timeout
        self.base_url = "https://api.ocean.io/v2"

    async def enrich_company(self, company_name: str,
                            city: Optional[str] = None,
                            state: Optional[str] = None,
                            country_code: str = "us") -> Dict[str, Any]:
        """
        Enrich company data via Ocean.io API

        Args:
            company_name: Company name
            city: Optional city/location
            state: Optional state (US addresses)
            country_code: Country code (default: us)

        Returns:
            API response dict with company data
        """
        url = f"{self.base_url}/enrich/company"

        headers = {
            'x-api-token': self.api_key,
            'Content-Type': 'application/json'
        }

        # Build company object
        company_obj = {
            'name': company_name,
            'countryCode': country_code.lower()
        }

        if city:
            company_obj['city'] = city

        if state:
            company_obj['state'] = state

        payload = {
            'company': company_obj
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers,
                                       timeout=aiohttp.ClientTimeout(total=self.timeout)) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    elif response.status == 404:
                        logger.debug(f"Company not found in Ocean: {company_name}")
                        return {}
                    elif response.status == 401:
                        logger.error(f"Ocean API authentication failed - check API key")
                        return {}
                    else:
                        error_text = await response.text()
                        logger.error(f"Ocean API error {response.status} for {company_name}: {error_text}")
                        return {}

        except aiohttp.ClientError as e:
            logger.error(f"Ocean API connection error for {company_name}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Ocean API unexpected error for {company_name}: {e}")
            return {}


async def resolve_via_ocean(client: OceanClient, company_data: Dict[str, Any],
                            config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Stage 3 (alternative): Resolve domain via Ocean.io enrichment

    Args:
        client: OceanClient instance
        company_data: Dict with name, city, state, etc.
        config: Configuration dict

    Returns:
        Result dict or None if no match
    """
    name = company_data.get('name')
    city = company_data.get('city')
    state = company_data.get('state')

    if not name:
        return None

    logger.info(f"Ocean.io enrichment: {name}")

    try:
        response = await client.enrich_company(name, city=city, state=state)

        # Ocean returns data in 'data' field
        company_info = response.get('data', {})

        if not company_info or 'domain' not in company_info:
            logger.debug(f"No domain from Ocean for: {name}")
            return None

        domain = clean_domain(company_info['domain'])

        if not domain:
            return None

        # Ocean.io is a specialized B2B data provider
        # High confidence due to verified business database
        confidence = 88  # Slightly lower than Discolike as initial baseline

        # Boost confidence based on additional signals
        enrichment_signals = 0

        # Check for employee count (indicates verified company)
        if company_info.get('employeeCount') or company_info.get('oceanEmployeeCount'):
            enrichment_signals += 1

        # Check for revenue data
        if company_info.get('revenue'):
            enrichment_signals += 1

        # Check for industry classification
        if company_info.get('industry') or company_info.get('industries'):
            enrichment_signals += 1

        # Check for verified address
        if company_info.get('primaryAddress') or company_info.get('addresses'):
            enrichment_signals += 1

        # Boost confidence by 2 points per signal (max +8)
        confidence = min(confidence + (enrichment_signals * 2), 96)

        logger.info(f"✓ Ocean match: {domain} (confidence: {confidence}, signals: {enrichment_signals})")

        # Extract enrichment details
        details = {
            'employee_count': company_info.get('oceanEmployeeCount') or company_info.get('employeeCount'),
            'industry': company_info.get('industry'),
            'revenue_range': company_info.get('revenue'),
            'year_founded': company_info.get('yearFounded'),
            'description': company_info.get('description', '').strip()[:200]  # First 200 chars
        }

        return {
            'domain': domain,
            'confidence': confidence,
            'source': 'ocean',
            'method': 'b2b_enrichment',
            'details': details
        }

    except Exception as e:
        logger.error(f"Ocean error for {name}: {e}")
        return None
