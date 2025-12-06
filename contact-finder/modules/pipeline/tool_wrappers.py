"""
Tool Wrappers for LLMController and AdaptiveController

Wraps existing discovery modules to return ToolResult format.
Each tool returns: {tool_name, success, data, cost}

Tools available:
- google_maps_lookup: Search Google Maps (SMB)
- website_contacts: Scrape website (all)
- serper_osint: Web search for owner (all)
- data_fill: Fill missing domain/phone (all)
- linkedin_search: Search LinkedIn for employees (franchise/corporate)
- npi_lookup: Search NPI registry (healthcare)
"""

import logging
import httpx
from typing import Any, Callable, Awaitable
from urllib.parse import urlparse

from modules.discovery.openweb_ninja import OpenWebNinjaClient
from modules.discovery.serper_osint import SerperOsint
from modules.discovery.serper_filler import SerperDataFiller
from modules.pipeline.llm_controller import ToolResult

logger = logging.getLogger(__name__)


# NPI Registry API endpoint (free, no API key needed)
NPI_API_URL = "https://npiregistry.cms.hhs.gov/api/"


class ToolFactory:
    """
    Factory that creates tool wrapper functions for the LLMController.

    Each wrapper converts the discovery module response to a standardized ToolResult.
    """

    def __init__(
        self,
        openweb_api_key: str | None = None,
        serper_api_key: str | None = None,
        openai_api_key: str | None = None  # Kept for API compatibility but not used by Serper modules
    ):
        # Initialize clients
        self.openweb_client = OpenWebNinjaClient(api_key=openweb_api_key)
        self.serper_osint = SerperOsint(api_key=serper_api_key)
        self.serper_filler = SerperDataFiller(api_key=serper_api_key)

        # Tool costs (USD)
        self.costs = {
            "google_maps_lookup": 0.002,
            "website_contacts": 0.002,
            "serper_osint": 0.001,
            "data_fill": 0.001,
            "linkedin_search": 0.002,  # Uses serper to find LinkedIn profiles
            "npi_lookup": 0.0,  # Free NPI registry API
        }

    def get_tools(self) -> dict[str, Callable[..., Awaitable[ToolResult]]]:
        """Get all tool wrapper functions"""
        return {
            "google_maps_lookup": self._google_maps_lookup,
            "website_contacts": self._website_contacts,
            "serper_osint": self._serper_osint,
            "data_fill": self._data_fill,
            "linkedin_search": self._linkedin_search,
            "npi_lookup": self._npi_lookup,
        }

    async def _google_maps_lookup(self, query: str) -> ToolResult:
        """
        Search Google Maps for business info.

        Args:
            query: Search query (company name + city)

        Returns:
            ToolResult with owner_name, phone, email, address, domain
        """
        try:
            result = await self.openweb_client.search_local_business(query)

            if not result.success:
                return ToolResult(
                    tool_name="google_maps_lookup",
                    success=False,
                    data={"error": result.error or "No results found"},
                    cost=self.costs["google_maps_lookup"]
                )

            # Extract domain from website URL
            domain = None
            if result.website:
                try:
                    parsed = urlparse(result.website)
                    domain = parsed.netloc.replace("www.", "")
                except Exception:
                    pass

            return ToolResult(
                tool_name="google_maps_lookup",
                success=True,
                data={
                    "place_id": result.place_id,
                    "name": result.name,
                    "owner_name": result.owner_name,
                    "phone": result.phone,
                    "email": result.email,
                    "website": result.website,
                    "domain": domain,
                    "address": result.address,
                    "city": result.city,
                    "state": result.state,
                    "rating": result.rating,
                    "reviews_count": result.reviews_count,
                    "category": result.category,
                    "social_links": result.social_links,
                },
                cost=self.costs["google_maps_lookup"]
            )

        except Exception as e:
            logger.error(f"Google Maps lookup failed: {e}")
            return ToolResult(
                tool_name="google_maps_lookup",
                success=False,
                data={"error": str(e)},
                cost=self.costs["google_maps_lookup"]
            )

    async def _website_contacts(self, domain: str) -> ToolResult:
        """
        Scrape website for contact info.

        Args:
            domain: Company domain to scrape

        Returns:
            ToolResult with emails, phones, social links
        """
        try:
            result = await self.openweb_client.scrape_contacts(domain)

            if not result.success:
                return ToolResult(
                    tool_name="website_contacts",
                    success=False,
                    data={"error": result.error or "No contacts found"},
                    cost=self.costs["website_contacts"]
                )

            # Extract email values from email list
            emails = []
            for email_info in result.emails:
                if isinstance(email_info, dict):
                    emails.append(email_info.get("value"))
                else:
                    emails.append(email_info)

            # Extract phone values
            phones = []
            for phone_info in result.phone_numbers:
                if isinstance(phone_info, dict):
                    phones.append(phone_info.get("value"))
                else:
                    phones.append(phone_info)

            return ToolResult(
                tool_name="website_contacts",
                success=True,
                data={
                    "domain": result.domain,
                    "emails": [e for e in emails if e],
                    "phones": [p for p in phones if p],
                    "phone": result.primary_phone,
                    "linkedin": result.linkedin,
                    "facebook": result.facebook,
                    "twitter": result.twitter,
                    "instagram": result.instagram,
                },
                cost=self.costs["website_contacts"]
            )

        except Exception as e:
            logger.error(f"Website contacts scrape failed: {e}")
            return ToolResult(
                tool_name="website_contacts",
                success=False,
                data={"error": str(e)},
                cost=self.costs["website_contacts"]
            )

    async def _serper_osint(
        self,
        company_name: str,
        domain: str | None = None,
        city: str | None = None,
        state: str | None = None
    ) -> ToolResult:
        """
        Search web for owner/contact info.

        Args:
            company_name: Company name to search for
            domain: Company domain (optional)
            city: City hint (optional)
            state: State hint (optional)

        Returns:
            ToolResult with owner_name, title, linkedin_url
        """
        try:
            # Build search domain - use provided domain or company name
            search_domain = domain or company_name.lower().replace(" ", "")

            result = await self.serper_osint.find_executive(
                company_domain=search_domain,
                target_title="Owner",  # SMB pipeline always looks for owner
                company_name=company_name
            )

            if result.best_match is None:
                return ToolResult(
                    tool_name="serper_osint",
                    success=False,
                    data={"error": "No owner found", "candidates": len(result.candidates)},
                    cost=self.costs["serper_osint"]
                )

            best = result.best_match
            return ToolResult(
                tool_name="serper_osint",
                success=True,
                data={
                    "owner_name": best.name,
                    "title": best.title,
                    "linkedin_url": best.linkedin_url,
                    "source_url": best.source_url,
                    "source_type": best.source_type,
                    "snippet": best.snippet,
                    "confidence": best.confidence,
                    "total_candidates": len(result.candidates),
                },
                cost=self.costs["serper_osint"]
            )

        except Exception as e:
            logger.error(f"Serper OSINT failed: {e}")
            return ToolResult(
                tool_name="serper_osint",
                success=False,
                data={"error": str(e)},
                cost=self.costs["serper_osint"]
            )

    async def _data_fill(
        self,
        company_name: str,
        city: str | None = None,
        state: str | None = None,
        missing_fields: list[str] | None = None
    ) -> ToolResult:
        """
        Fill missing data using web search.

        Args:
            company_name: Company name to search for
            city: City hint
            state: State hint
            missing_fields: Fields to fill (defaults to domain, phone, owner)

        Returns:
            ToolResult with domain, phone, address
        """
        try:
            # Build company dict for filler
            company_data = {
                "name": company_name,
                "city": city,
                "state": state,
            }

            # Default fields to fill if not specified
            fields_to_fill = missing_fields or ["domain", "phone", "owner"]

            result = await self.serper_filler.fill_missing(company_data, fields_to_fill)

            filled = result.filled
            return ToolResult(
                tool_name="data_fill",
                success=len(result.fields_filled) > 0,
                data={
                    "domain": filled.get("domain"),
                    "phone": filled.get("phone"),
                    "address": filled.get("address"),
                    "owner_name": filled.get("owner"),
                    "fields_filled": result.fields_filled,
                    "queries_run": result.queries_run,
                },
                cost=result.cost
            )

        except Exception as e:
            logger.error(f"Data fill failed: {e}")
            return ToolResult(
                tool_name="data_fill",
                success=False,
                data={"error": str(e)},
                cost=self.costs["data_fill"]
            )

    async def _linkedin_search(
        self,
        company_name: str,
        title_keywords: str = "owner OR manager"
    ) -> ToolResult:
        """
        Search for LinkedIn profiles of employees at a company.

        Uses Serper to search LinkedIn for people with specific titles.
        Good for franchises and corporate locations where owner isn't in Google Maps.

        Args:
            company_name: Company name to search for
            title_keywords: Title keywords like "owner OR manager"

        Returns:
            ToolResult with list of people found
        """
        try:
            # Use serper to search LinkedIn
            query = f'site:linkedin.com/in "{company_name}" {title_keywords}'

            result = await self.serper_osint.find_executive(
                company_domain=company_name.lower().replace(" ", ""),
                target_title=title_keywords.split(" OR ")[0] if " OR " in title_keywords else title_keywords,
                company_name=company_name
            )

            # Extract people from candidates
            people = []
            for candidate in result.candidates[:5]:  # Top 5
                people.append({
                    "name": candidate.name,
                    "title": candidate.title,
                    "linkedin_url": candidate.linkedin_url,
                    "confidence": candidate.confidence,
                })

            if not people and result.best_match:
                people.append({
                    "name": result.best_match.name,
                    "title": result.best_match.title,
                    "linkedin_url": result.best_match.linkedin_url,
                    "confidence": result.best_match.confidence,
                })

            return ToolResult(
                tool_name="linkedin_search",
                success=len(people) > 0,
                data={
                    "people": people,
                    "total_found": len(result.candidates),
                },
                cost=self.costs["linkedin_search"]
            )

        except Exception as e:
            logger.error(f"LinkedIn search failed: {e}")
            return ToolResult(
                tool_name="linkedin_search",
                success=False,
                data={"error": str(e)},
                cost=self.costs["linkedin_search"]
            )

    async def _npi_lookup(
        self,
        name_or_org: str,
        city: str | None = None,
        state: str | None = None
    ) -> ToolResult:
        """
        Search NPI registry for healthcare providers.

        Free API, no key needed. Returns practitioner info.

        Args:
            name_or_org: Provider or organization name
            city: City (optional)
            state: State code (optional)

        Returns:
            ToolResult with provider info
        """
        try:
            # Build NPI API query
            params = {
                "version": "2.1",
                "limit": 5,
            }

            # Determine if this is an organization or individual search
            # Organizations usually have words like "clinic", "health", "medical"
            org_keywords = ["clinic", "health", "medical", "hospital", "center", "care"]
            is_org = any(kw in name_or_org.lower() for kw in org_keywords)

            if is_org:
                params["organization_name"] = name_or_org
            else:
                # Try to split name into first/last
                parts = name_or_org.split()
                if len(parts) >= 2:
                    params["first_name"] = parts[0]
                    params["last_name"] = parts[-1]
                else:
                    params["organization_name"] = name_or_org

            if city:
                params["city"] = city
            if state:
                params["state"] = state

            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(NPI_API_URL, params=params)
                resp.raise_for_status()
                data = resp.json()

            results = data.get("results", [])
            if not results:
                return ToolResult(
                    tool_name="npi_lookup",
                    success=False,
                    data={"error": "No providers found"},
                    cost=self.costs["npi_lookup"]
                )

            # Parse first result
            provider = results[0]
            basic = provider.get("basic", {})

            # Get address and phone
            addresses = provider.get("addresses", [])
            primary_address = addresses[0] if addresses else {}

            # Build response
            if provider.get("enumeration_type") == "NPI-2":
                # Organization
                provider_name = basic.get("organization_name", "")
                specialty = "Healthcare Organization"
            else:
                # Individual
                first = basic.get("first_name", "")
                last = basic.get("last_name", "")
                provider_name = f"{first} {last}".strip()
                # Get specialty from taxonomy
                taxonomies = provider.get("taxonomies", [])
                specialty = taxonomies[0].get("desc", "") if taxonomies else ""

            return ToolResult(
                tool_name="npi_lookup",
                success=True,
                data={
                    "npi": provider.get("number"),
                    "provider_name": provider_name,
                    "specialty": specialty,
                    "phone": primary_address.get("telephone_number"),
                    "address": primary_address.get("address_1"),
                    "city": primary_address.get("city"),
                    "state": primary_address.get("state"),
                    "zip": primary_address.get("postal_code"),
                    "total_results": len(results),
                },
                cost=self.costs["npi_lookup"]
            )

        except Exception as e:
            logger.error(f"NPI lookup failed: {e}")
            return ToolResult(
                tool_name="npi_lookup",
                success=False,
                data={"error": str(e)},
                cost=self.costs["npi_lookup"]
            )

    async def close(self):
        """Close all clients"""
        await self.openweb_client.close()


def create_tool_factory(
    openweb_api_key: str | None = None,
    serper_api_key: str | None = None,
    openai_api_key: str | None = None
) -> ToolFactory:
    """
    Create a tool factory with the given API keys.

    If keys are not provided, they will be read from environment variables.
    """
    return ToolFactory(
        openweb_api_key=openweb_api_key,
        serper_api_key=serper_api_key,
        openai_api_key=openai_api_key
    )
