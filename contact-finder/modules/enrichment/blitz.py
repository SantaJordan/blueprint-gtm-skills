"""
Blitz API Client
https://beta.blitz-api.ai

Endpoints:
- /api/enrichment/email (1 credit) - LinkedIn URL -> work email
- /api/enrichment/phone (3 credits) - LinkedIn URL -> phone
- /api/enrichment/email_domain (0.5 credits) - LinkedIn company URL -> domain
- /api/email/validate (0.5 credits) - Email validation with catch-all detection
- /api/search/waterfall-icp (1-3 credits/result) - Company LinkedIn -> contacts by title
"""

import aiohttp
import asyncio
from dataclasses import dataclass
from typing import Any


@dataclass
class BlitzEmailResult:
    email: str | None
    status: str
    credits_consumed: float
    raw_response: dict


@dataclass
class BlitzPhoneResult:
    phone: str | None
    status: str
    credits_consumed: float
    raw_response: dict


@dataclass
class BlitzValidationResult:
    valid: bool
    is_catch_all: bool
    status: str
    credits_consumed: float
    raw_response: dict


@dataclass
class BlitzContactResult:
    name: str | None
    title: str | None
    linkedin_url: str | None
    email: str | None
    confidence: float
    raw_response: dict


class BlitzClient:
    """Blitz API client for contact enrichment"""

    BASE_URL = "https://beta.blitz-api.ai/api"

    def __init__(self, api_key: str, timeout: int = 30):
        self.api_key = api_key
        self.timeout = timeout
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={"x-api-key": self.api_key},
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def _post(self, endpoint: str, data: dict) -> dict:
        """Make a POST request to Blitz API"""
        session = await self._get_session()
        url = f"{self.BASE_URL}{endpoint}"

        async with session.post(url, json=data) as response:
            result = await response.json()
            if response.status == 401:
                raise ValueError("Invalid Blitz API key")
            if response.status == 402:
                raise ValueError("Insufficient Blitz credits")
            return result

    async def find_email(self, linkedin_url: str) -> BlitzEmailResult:
        """
        Find work email from LinkedIn profile URL
        Cost: 1 credit on success
        """
        try:
            result = await self._post("/enrichment/email", {"linkedin_url": linkedin_url})

            return BlitzEmailResult(
                email=result.get("email"),
                status=result.get("status", "unknown"),
                credits_consumed=result.get("credits_consumed", 0),
                raw_response=result
            )
        except Exception as e:
            return BlitzEmailResult(
                email=None,
                status=f"error: {str(e)}",
                credits_consumed=0,
                raw_response={}
            )

    async def find_phone(self, linkedin_url: str) -> BlitzPhoneResult:
        """
        Find phone number from LinkedIn profile URL
        Cost: 3 credits on success
        """
        try:
            result = await self._post("/enrichment/phone", {"linkedin_url": linkedin_url})

            return BlitzPhoneResult(
                phone=result.get("phone"),
                status=result.get("status", "unknown"),
                credits_consumed=result.get("credits_consumed", 0),
                raw_response=result
            )
        except Exception as e:
            return BlitzPhoneResult(
                phone=None,
                status=f"error: {str(e)}",
                credits_consumed=0,
                raw_response={}
            )

    async def validate_email(self, email: str) -> BlitzValidationResult:
        """
        Validate email with catch-all detection
        Cost: 0.5 credits on success
        """
        try:
            result = await self._post("/email/validate", {"email": email})

            return BlitzValidationResult(
                valid=result.get("valid", False),
                is_catch_all=result.get("is_catch_all", False),
                status=result.get("status", "unknown"),
                credits_consumed=result.get("credits_consumed", 0),
                raw_response=result
            )
        except Exception as e:
            return BlitzValidationResult(
                valid=False,
                is_catch_all=False,
                status=f"error: {str(e)}",
                credits_consumed=0,
                raw_response={}
            )

    async def waterfall_icp(
        self,
        linkedin_company_url: str,
        titles: list[str],
        locations: list[str] | None = None,
        max_results: int = 5,
        real_time: bool = False
    ) -> list[BlitzContactResult]:
        """
        Find contacts at a company matching specified titles
        Cost: 1 credit/result (regular) or 3 credits/result (real-time)
        """
        endpoint = "/search/waterfall-icp-real-time" if real_time else "/search/waterfall-icp"

        data = {
            "linkedin_company_url": linkedin_company_url,
            "cascade_filters": {
                "titles": titles
            }
        }

        if locations:
            data["cascade_filters"]["locations"] = locations

        try:
            result = await self._post(endpoint, data)
            contacts = []

            for contact_data in result.get("results", []):
                contacts.append(BlitzContactResult(
                    name=contact_data.get("name"),
                    title=contact_data.get("title"),
                    linkedin_url=contact_data.get("linkedin_url"),
                    email=contact_data.get("email"),
                    confidence=contact_data.get("ranking", 0),
                    raw_response=contact_data
                ))

            return contacts[:max_results]

        except Exception as e:
            return []

    async def get_key_info(self) -> dict:
        """Get API key information (credit balance, etc.)"""
        session = await self._get_session()
        url = f"{self.BASE_URL}/blitz/key-info"

        async with session.get(url) as response:
            return await response.json()


# Convenience function
async def test_blitz_api(api_key: str):
    """Test Blitz API connection"""
    client = BlitzClient(api_key)
    try:
        info = await client.get_key_info()
        print(f"Blitz API connected. Credits: {info.get('credits_remaining', 'unknown')}")
        return True
    except Exception as e:
        print(f"Blitz API error: {e}")
        return False
    finally:
        await client.close()
