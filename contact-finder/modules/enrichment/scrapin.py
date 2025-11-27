"""
Scrapin API Client
https://docs.scrapin.io

Endpoints:
- Person Profile (1 credit) - Get LinkedIn profile data from URL
- Company Profile (1 credit) - Get company data from LinkedIn URL
- Person Matching (1 credit) - Find person from parameters
- Company Search (1 credit) - Find company from domain
- Email Discovery (2 credits) - Get email from profile URL or name/company
"""

import aiohttp
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ScrapinPersonProfile:
    """LinkedIn person profile data"""
    full_name: str | None
    first_name: str | None
    last_name: str | None
    headline: str | None
    title: str | None
    company: str | None
    location: str | None
    linkedin_url: str | None
    profile_picture: str | None
    summary: str | None
    experience: list[dict] = field(default_factory=list)
    education: list[dict] = field(default_factory=list)
    raw_response: dict = field(default_factory=dict)


@dataclass
class ScrapinCompanyProfile:
    """LinkedIn company profile data"""
    name: str | None
    linkedin_url: str | None
    website: str | None
    industry: str | None
    company_size: str | None
    employee_count: int | None
    headquarters: str | None
    description: str | None
    specialties: list[str] = field(default_factory=list)
    raw_response: dict = field(default_factory=dict)


@dataclass
class ScrapinEmailResult:
    """Email discovery result"""
    email: str | None
    email_type: str | None  # professional, personal
    confidence: float
    raw_response: dict = field(default_factory=dict)


class ScrapinClient:
    """Scrapin API client for LinkedIn data extraction"""

    BASE_URL = "https://api.scrapin.io"

    def __init__(self, api_key: str, timeout: int = 30):
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

    async def _request(self, method: str, endpoint: str, data: dict | None = None) -> dict:
        """Make a request to Scrapin API"""
        session = await self._get_session()
        url = f"{self.BASE_URL}{endpoint}"

        if method == "GET":
            async with session.get(url, params=data) as response:
                if response.status == 401:
                    raise ValueError("Invalid Scrapin API key")
                if response.status == 402:
                    raise ValueError("Insufficient Scrapin credits")
                return await response.json()
        else:
            async with session.post(url, json=data) as response:
                if response.status == 401:
                    raise ValueError("Invalid Scrapin API key")
                if response.status == 402:
                    raise ValueError("Insufficient Scrapin credits")
                return await response.json()

    async def get_person_profile(self, linkedin_url: str) -> ScrapinPersonProfile:
        """
        Get full LinkedIn profile data from URL
        Cost: 1 credit (0.5 if cached)
        """
        try:
            result = await self._request("GET", "/person/profile", {"linkedInUrl": linkedin_url})

            # Extract current position
            current_title = None
            current_company = None
            experience = result.get("experience", [])
            if experience:
                current = experience[0]
                current_title = current.get("title")
                current_company = current.get("companyName")

            return ScrapinPersonProfile(
                full_name=result.get("fullName"),
                first_name=result.get("firstName"),
                last_name=result.get("lastName"),
                headline=result.get("headline"),
                title=current_title,
                company=current_company,
                location=result.get("location"),
                linkedin_url=result.get("linkedInUrl"),
                profile_picture=result.get("profilePicture"),
                summary=result.get("summary"),
                experience=experience,
                education=result.get("education", []),
                raw_response=result
            )

        except Exception as e:
            return ScrapinPersonProfile(
                full_name=None,
                first_name=None,
                last_name=None,
                headline=None,
                title=None,
                company=None,
                location=None,
                linkedin_url=linkedin_url,
                profile_picture=None,
                summary=None,
                raw_response={"error": str(e)}
            )

    async def get_company_profile(self, linkedin_url: str) -> ScrapinCompanyProfile:
        """
        Get LinkedIn company profile data
        Cost: 1 credit (0.5 if cached)
        """
        try:
            result = await self._request("GET", "/company/profile", {"linkedInUrl": linkedin_url})

            return ScrapinCompanyProfile(
                name=result.get("name"),
                linkedin_url=result.get("linkedInUrl"),
                website=result.get("website"),
                industry=result.get("industry"),
                company_size=result.get("companySize"),
                employee_count=result.get("employeeCount"),
                headquarters=result.get("headquarters"),
                description=result.get("description"),
                specialties=result.get("specialties", []),
                raw_response=result
            )

        except Exception as e:
            return ScrapinCompanyProfile(
                name=None,
                linkedin_url=linkedin_url,
                website=None,
                industry=None,
                company_size=None,
                employee_count=None,
                headquarters=None,
                description=None,
                raw_response={"error": str(e)}
            )

    async def search_company(self, domain: str) -> ScrapinCompanyProfile | None:
        """
        Find company LinkedIn profile by domain
        Cost: 1 credit (0.5 if cached)
        """
        try:
            result = await self._request("GET", "/company/search", {"domain": domain})

            if not result or "linkedInUrl" not in result:
                return None

            return ScrapinCompanyProfile(
                name=result.get("name"),
                linkedin_url=result.get("linkedInUrl"),
                website=result.get("website"),
                industry=result.get("industry"),
                company_size=result.get("companySize"),
                employee_count=result.get("employeeCount"),
                headquarters=result.get("headquarters"),
                description=result.get("description"),
                specialties=result.get("specialties", []),
                raw_response=result
            )

        except Exception as e:
            return None

    async def match_person(
        self,
        first_name: str,
        last_name: str | None = None,
        company_name: str | None = None,
        company_domain: str | None = None
    ) -> ScrapinPersonProfile | None:
        """
        Find a person's LinkedIn profile from parameters
        Cost: 1 credit (0.5 if cached)
        """
        data = {"firstName": first_name}
        if last_name:
            data["lastName"] = last_name
        if company_name:
            data["companyName"] = company_name
        if company_domain:
            data["companyDomain"] = company_domain

        try:
            result = await self._request("POST", "/person/match", data)

            if not result or "linkedInUrl" not in result:
                return None

            return await self.get_person_profile(result["linkedInUrl"])

        except Exception as e:
            return None

    async def find_email(
        self,
        linkedin_url: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        company_domain: str | None = None
    ) -> ScrapinEmailResult:
        """
        Find email for a person
        Cost: 2 credits

        Either provide linkedin_url OR (first_name + company info)
        """
        if linkedin_url:
            data = {"linkedInUrl": linkedin_url}
        elif first_name:
            data = {"firstName": first_name}
            if last_name:
                data["lastName"] = last_name
            if company_domain:
                data["companyDomain"] = company_domain
        else:
            return ScrapinEmailResult(
                email=None,
                email_type=None,
                confidence=0,
                raw_response={"error": "Either linkedin_url or first_name required"}
            )

        try:
            result = await self._request("POST", "/person/email", data)

            return ScrapinEmailResult(
                email=result.get("email"),
                email_type=result.get("emailType"),
                confidence=result.get("confidence", 0),
                raw_response=result
            )

        except Exception as e:
            return ScrapinEmailResult(
                email=None,
                email_type=None,
                confidence=0,
                raw_response={"error": str(e)}
            )


# Convenience function
async def test_scrapin_api(api_key: str):
    """Test Scrapin API connection"""
    client = ScrapinClient(api_key)
    try:
        # Search for a known company
        result = await client.search_company("microsoft.com")
        if result and result.name:
            print(f"Scrapin API connected. Found: {result.name}")
            return True
        else:
            print("Scrapin API connected but no results")
            return True
    except Exception as e:
        print(f"Scrapin API error: {e}")
        return False
    finally:
        await client.close()
