"""
LeadMagic API Client
https://api.leadmagic.io

Endpoint:
- POST /email-finder - Find work email from name + domain/company
"""

import aiohttp
from dataclasses import dataclass
from typing import Any


@dataclass
class LeadMagicEmailResult:
    email: str | None
    status: str  # valid, invalid, unknown
    is_catch_all: bool
    mx_record: bool
    mx_provider: str | None
    credits_consumed: int
    company_data: dict | None
    raw_response: dict


class LeadMagicClient:
    """LeadMagic API client for email finding"""

    BASE_URL = "https://api.leadmagic.io"

    def __init__(self, api_key: str, timeout: int = 30):
        self.api_key = api_key
        self.timeout = timeout
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={"X-API-Key": self.api_key, "Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def find_email(
        self,
        first_name: str,
        last_name: str | None = None,
        domain: str | None = None,
        company_name: str | None = None
    ) -> LeadMagicEmailResult:
        """
        Find email address using name and company info
        Pay-if-found model - only charged if email is found

        Args:
            first_name: Person's first name (required)
            last_name: Person's last name (optional but recommended)
            domain: Company domain (optional)
            company_name: Company name (optional)

        Returns:
            LeadMagicEmailResult with email and validation data
        """
        session = await self._get_session()
        url = f"{self.BASE_URL}/email-finder"

        payload = {"first_name": first_name}

        if last_name:
            payload["last_name"] = last_name
        if domain:
            payload["domain"] = domain
        if company_name:
            payload["company_name"] = company_name

        try:
            async with session.post(url, json=payload) as response:
                if response.status == 400:
                    return LeadMagicEmailResult(
                        email=None,
                        status="invalid_request",
                        is_catch_all=False,
                        mx_record=False,
                        mx_provider=None,
                        credits_consumed=0,
                        company_data=None,
                        raw_response={"error": "Invalid request or missing parameters"}
                    )

                result = await response.json()

                # Extract company data if present
                company_data = None
                if "company" in result:
                    company_data = {
                        "name": result["company"].get("name"),
                        "industry": result["company"].get("industry"),
                        "size": result["company"].get("size"),
                        "linkedin_url": result["company"].get("linkedin_url"),
                        "facebook_url": result["company"].get("facebook_url"),
                        "twitter_url": result["company"].get("twitter_url"),
                    }

                return LeadMagicEmailResult(
                    email=result.get("email"),
                    status=result.get("status", "unknown"),
                    is_catch_all=result.get("is_domain_catch_all", False),
                    mx_record=result.get("mx_record", False),
                    mx_provider=result.get("mx_provider"),
                    credits_consumed=result.get("credits_consumed", 0),
                    company_data=company_data,
                    raw_response=result
                )

        except Exception as e:
            return LeadMagicEmailResult(
                email=None,
                status=f"error: {str(e)}",
                is_catch_all=False,
                mx_record=False,
                mx_provider=None,
                credits_consumed=0,
                company_data=None,
                raw_response={}
            )


def split_name(full_name: str) -> tuple[str, str | None]:
    """Split a full name into first and last name"""
    parts = full_name.strip().split()
    if len(parts) == 0:
        return "", None
    elif len(parts) == 1:
        return parts[0], None
    else:
        return parts[0], " ".join(parts[1:])


# Convenience function
async def test_leadmagic_api(api_key: str):
    """Test LeadMagic API connection"""
    client = LeadMagicClient(api_key)
    try:
        # Try a known test case
        result = await client.find_email(
            first_name="Bill",
            last_name="Gates",
            domain="microsoft.com"
        )
        print(f"LeadMagic API connected. Test result: {result.status}")
        return result.email is not None
    except Exception as e:
        print(f"LeadMagic API error: {e}")
        return False
    finally:
        await client.close()
