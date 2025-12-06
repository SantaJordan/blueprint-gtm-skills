"""
Wave 1: Company Intelligence Gathering

Executes parallel WebFetch + WebSearch to gather:
- Company context (offering, value prop, differentiators)
- ICP profile (industries, company scale, operational context)
- Target persona (title, responsibilities, KPIs, blind spots)
"""
import asyncio
from typing import Dict, List
import re


class Wave1CompanyResearch:
    """Wave 1: Explosive intelligence gathering with parallel calls."""

    def __init__(self, claude_client, web_fetch, web_search):
        self.claude = claude_client
        self.web_fetch = web_fetch
        self.web_search = web_search

    async def execute(self, company_url: str) -> Dict:
        """
        Execute Wave 1 company research.

        Args:
            company_url: Company website URL

        Returns:
            {
                "company_name": str,
                "offering": str,
                "value_prop": str,
                "differentiators": [str],
                "industries_served": [str],
                "icp": str,
                "persona": str,
                "persona_title": str,
                "persona_kpis": [str],
                "raw_data": {...}
            }
        """
        # Extract base domain
        domain = self._extract_domain(company_url)
        company_name = self._infer_company_name(domain)

        # Build URLs to fetch
        base_url = f"https://{domain}"
        pages_to_fetch = [
            base_url,
            f"{base_url}/about",
            f"{base_url}/about-us",
            f"{base_url}/company",
            f"{base_url}/customers",
            f"{base_url}/case-studies",
            f"{base_url}/solutions",
            f"{base_url}/product",
            f"{base_url}/platform",
        ]

        # Build search queries
        searches_to_run = [
            f"{company_name} customer reviews",
            f"{company_name} case studies success stories",
            f"{company_name} target customers industries",
            f"what problems does {company_name} solve",
            f"{company_name} vs competitors comparison",
            f"{company_name} pricing",
        ]

        # Execute in parallel
        fetch_task = self.web_fetch.fetch_parallel(pages_to_fetch)
        search_task = self.web_search.search_parallel(searches_to_run)

        fetch_results, search_results = await asyncio.gather(fetch_task, search_task)

        # Combine all text content
        all_content = self._combine_content(fetch_results, search_results)

        # Use Claude to synthesize
        synthesis = await self._synthesize_with_claude(company_name, all_content)

        return {
            **synthesis,
            "company_name": company_name,
            "company_url": company_url,
            "domain": domain,
            "raw_data": {
                "pages_fetched": len([r for r in fetch_results if r.get("success")]),
                "searches_completed": len([r for r in search_results if r.get("success")]),
            }
        }

    async def _synthesize_with_claude(self, company_name: str, content: str) -> Dict:
        """Use Claude to extract structured information from raw content."""

        prompt = f"""Analyze this company research data and extract key information.

COMPANY: {company_name}

RAW CONTENT:
{content[:50000]}  # Limit content size

Extract and return this information in a structured format:

1. OFFERING: What does this company sell? (1-2 sentences)
2. VALUE_PROP: What's their main value proposition? (1-2 sentences)
3. DIFFERENTIATORS: What makes them unique? (list 3-5 points)
4. INDUSTRIES_SERVED: What industries do they target? (list specific industries)
5. ICP: Who is their ideal customer? (describe company type, size, characteristics)
6. PERSONA_TITLE: What job title is the primary buyer? (e.g., "VP of Operations")
7. PERSONA_RESPONSIBILITIES: What does this persona do daily?
8. PERSONA_KPIS: What metrics is this persona measured on? (list 3-5)
9. PERSONA_BLIND_SPOTS: What operational challenges might this persona not see coming?

Format your response as:
OFFERING: [text]
VALUE_PROP: [text]
DIFFERENTIATORS: [item1, item2, item3]
INDUSTRIES_SERVED: [industry1, industry2, industry3]
ICP: [text]
PERSONA_TITLE: [title]
PERSONA_RESPONSIBILITIES: [text]
PERSONA_KPIS: [kpi1, kpi2, kpi3]
PERSONA_BLIND_SPOTS: [text]"""

        response = await self.claude.messages.create(
            model="claude-sonnet-4-20250514",  # Use Sonnet for bulk work
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )

        return self._parse_synthesis(response.content[0].text)

    def _parse_synthesis(self, text: str) -> Dict:
        """Parse Claude's structured response into a dictionary."""
        result = {
            "offering": "",
            "value_prop": "",
            "differentiators": [],
            "industries_served": [],
            "icp": "",
            "persona_title": "",
            "persona": "",
            "persona_kpis": [],
            "persona_blind_spots": ""
        }

        patterns = {
            "offering": r"OFFERING:\s*(.+?)(?=\n[A-Z_]+:|$)",
            "value_prop": r"VALUE_PROP:\s*(.+?)(?=\n[A-Z_]+:|$)",
            "differentiators": r"DIFFERENTIATORS:\s*(.+?)(?=\n[A-Z_]+:|$)",
            "industries_served": r"INDUSTRIES_SERVED:\s*(.+?)(?=\n[A-Z_]+:|$)",
            "icp": r"ICP:\s*(.+?)(?=\n[A-Z_]+:|$)",
            "persona_title": r"PERSONA_TITLE:\s*(.+?)(?=\n[A-Z_]+:|$)",
            "persona": r"PERSONA_RESPONSIBILITIES:\s*(.+?)(?=\n[A-Z_]+:|$)",
            "persona_kpis": r"PERSONA_KPIS:\s*(.+?)(?=\n[A-Z_]+:|$)",
            "persona_blind_spots": r"PERSONA_BLIND_SPOTS:\s*(.+?)(?=\n[A-Z_]+:|$)",
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                if key in ["differentiators", "industries_served", "persona_kpis"]:
                    # Parse as list
                    result[key] = [item.strip() for item in re.split(r'[,\[\]]', value) if item.strip()]
                else:
                    result[key] = value

        return result

    def _combine_content(self, fetch_results: List[Dict], search_results: List[Dict]) -> str:
        """Combine fetch and search results into a single text block."""
        parts = []

        # Add fetched page content
        parts.append("=== WEBSITE CONTENT ===\n")
        for result in fetch_results:
            if result.get("success") and result.get("text"):
                parts.append(f"--- {result.get('url', 'Unknown URL')} ---")
                parts.append(result["text"][:5000])  # Limit per page
                parts.append("")

        # Add search results
        parts.append("\n=== SEARCH RESULTS ===\n")
        for result in search_results:
            if result.get("success"):
                parts.append(f"--- Search: {result.get('query', '')} ---")
                for r in result.get("organic", [])[:5]:  # Top 5 results per search
                    parts.append(f"Title: {r.get('title', '')}")
                    parts.append(f"Snippet: {r.get('snippet', '')}")
                    parts.append("")

        return "\n".join(parts)

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        url = url.lower().strip()
        url = re.sub(r'^https?://', '', url)
        url = re.sub(r'^www\.', '', url)
        url = url.split('/')[0]
        return url

    def _infer_company_name(self, domain: str) -> str:
        """Infer company name from domain."""
        # Remove TLD
        name = domain.split('.')[0]
        # Capitalize
        return name.title()
