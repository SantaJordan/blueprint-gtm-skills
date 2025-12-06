"""
Wave 2: Multi-Modal Data Landscape Scan

Executes parallel searches across 4 data categories:
- Government/Regulatory
- Competitive Intelligence
- Velocity Signals
- Tech/Operational
"""
import asyncio
from typing import Dict, List
import re


class Wave2DataLandscape:
    """Wave 2: Map available data sources for the target niche."""

    # Search templates by category
    GOVERNMENT_SEARCHES = [
        "{industry} government database violations API",
        "{industry} licensing board public records search",
        "{industry} inspection records database field names",
        "OSHA {industry} violation data downloadable",
        "{industry} permit database API documentation",
        "EPA {industry} compliance data public access",
    ]

    COMPETITIVE_SEARCHES = [
        "{industry} pricing data scraping tools",
        "{industry} review data extraction API",
        "{industry} competitive analysis data sources",
        "scrape reviews {industry}",
    ]

    VELOCITY_SEARCHES = [
        "Google Maps API review data documentation",
        "review velocity tracking tools {industry}",
        "{industry} hiring velocity job posting data API",
    ]

    TECH_SEARCHES = [
        "BuiltWith API pricing technology detection",
        "job posting API {industry} Indeed LinkedIn",
        "{industry} tech stack data sources",
    ]

    def __init__(self, claude_client, web_search):
        self.claude = claude_client
        self.web_search = web_search

    async def execute(self, niche: Dict, company_context: Dict) -> Dict:
        """
        Execute Wave 2 data landscape scan.

        Args:
            niche: Qualified niche from Wave 1.5
            company_context: Context from Wave 1

        Returns:
            {
                "government": [
                    {
                        "name": str,
                        "url": str,
                        "fields": [str],
                        "feasibility": "HIGH" | "MEDIUM" | "LOW",
                        "update_frequency": str,
                        "cost": str
                    }
                ],
                "competitive": [...],
                "velocity": [...],
                "tech": [...]
            }
        """
        industry = niche.get("niche", company_context.get("industries_served", ["business"])[0] if company_context.get("industries_served") else "business")

        # Build all search queries
        all_searches = []
        search_categories = []

        for template in self.GOVERNMENT_SEARCHES:
            all_searches.append(template.format(industry=industry))
            search_categories.append("government")

        for template in self.COMPETITIVE_SEARCHES:
            all_searches.append(template.format(industry=industry))
            search_categories.append("competitive")

        for template in self.VELOCITY_SEARCHES:
            all_searches.append(template.format(industry=industry))
            search_categories.append("velocity")

        for template in self.TECH_SEARCHES:
            all_searches.append(template.format(industry=industry))
            search_categories.append("tech")

        # Execute all searches in parallel
        search_results = await self.web_search.search_parallel(all_searches)

        # Group results by category
        categorized_results = {
            "government": [],
            "competitive": [],
            "velocity": [],
            "tech": []
        }

        for i, result in enumerate(search_results):
            if result.get("success"):
                category = search_categories[i]
                categorized_results[category].append({
                    "query": all_searches[i],
                    "results": result.get("organic", [])[:5]
                })

        # Use Claude to evaluate and extract data sources
        data_landscape = await self._evaluate_sources(categorized_results, industry)

        return data_landscape

    async def _evaluate_sources(self, categorized_results: Dict, industry: str) -> Dict:
        """Use Claude to evaluate discovered data sources."""

        prompt = f"""Analyze these search results to identify available data sources for {industry}.

SEARCH RESULTS BY CATEGORY:

GOVERNMENT/REGULATORY:
{self._format_category_results(categorized_results.get('government', []))}

COMPETITIVE INTELLIGENCE:
{self._format_category_results(categorized_results.get('competitive', []))}

VELOCITY SIGNALS:
{self._format_category_results(categorized_results.get('velocity', []))}

TECH/OPERATIONAL:
{self._format_category_results(categorized_results.get('tech', []))}

For each category, identify 2-4 specific data sources with this information:

FORMAT:
GOVERNMENT SOURCES:
1. NAME: [database name]
   URL: [actual URL if found]
   FIELDS: [field1, field2, field3]
   FEASIBILITY: HIGH/MEDIUM/LOW
   FREQUENCY: [daily/weekly/monthly]
   COST: [free/paid amount]

COMPETITIVE SOURCES:
1. NAME: [source name]
   ...

VELOCITY SOURCES:
1. NAME: [source name]
   ...

TECH SOURCES:
1. NAME: [source name]
   ...

FEASIBILITY DEFINITIONS:
- HIGH: API exists, free or cheap, documented fields, frequent updates
- MEDIUM: Manual access or expensive, sparse docs, weekly updates
- LOW: No automation, prohibitively expensive, poor docs"""

        response = await self.claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )

        return self._parse_data_sources(response.content[0].text)

    def _parse_data_sources(self, text: str) -> Dict:
        """Parse Claude's response into structured data sources."""
        result = {
            "government": [],
            "competitive": [],
            "velocity": [],
            "tech": []
        }

        # Split by category
        category_patterns = {
            "government": r"GOVERNMENT SOURCES?:(.+?)(?=COMPETITIVE|VELOCITY|TECH|$)",
            "competitive": r"COMPETITIVE SOURCES?:(.+?)(?=GOVERNMENT|VELOCITY|TECH|$)",
            "velocity": r"VELOCITY SOURCES?:(.+?)(?=GOVERNMENT|COMPETITIVE|TECH|$)",
            "tech": r"TECH SOURCES?:(.+?)(?=GOVERNMENT|COMPETITIVE|VELOCITY|$)",
        }

        for category, pattern in category_patterns.items():
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                section = match.group(1)
                sources = self._parse_sources_section(section)
                result[category] = sources

        return result

    def _parse_sources_section(self, section: str) -> List[Dict]:
        """Parse individual sources from a section."""
        sources = []

        # Split by numbered items
        items = re.split(r'\n\d+\.', section)

        for item in items:
            if not item.strip():
                continue

            source = {
                "name": "",
                "url": "",
                "fields": [],
                "feasibility": "MEDIUM",
                "update_frequency": "unknown",
                "cost": "unknown"
            }

            # Parse fields
            name_match = re.search(r"NAME:\s*(.+?)(?=\n|$)", item)
            if name_match:
                source["name"] = name_match.group(1).strip()

            url_match = re.search(r"URL:\s*(.+?)(?=\n|$)", item)
            if url_match:
                source["url"] = url_match.group(1).strip()

            fields_match = re.search(r"FIELDS?:\s*(.+?)(?=\n|$)", item)
            if fields_match:
                fields_text = fields_match.group(1)
                source["fields"] = [f.strip() for f in re.split(r'[,\[\]]', fields_text) if f.strip()]

            feasibility_match = re.search(r"FEASIBILITY:\s*(HIGH|MEDIUM|LOW)", item, re.IGNORECASE)
            if feasibility_match:
                source["feasibility"] = feasibility_match.group(1).upper()

            frequency_match = re.search(r"FREQUENCY:\s*(.+?)(?=\n|$)", item)
            if frequency_match:
                source["update_frequency"] = frequency_match.group(1).strip()

            cost_match = re.search(r"COST:\s*(.+?)(?=\n|$)", item)
            if cost_match:
                source["cost"] = cost_match.group(1).strip()

            if source["name"]:
                sources.append(source)

        return sources

    def _format_category_results(self, results: List[Dict]) -> str:
        """Format search results for a category."""
        lines = []
        for r in results:
            lines.append(f"Query: {r.get('query', 'Unknown')}")
            for item in r.get("results", []):
                lines.append(f"  - {item.get('title', '')}")
                lines.append(f"    {item.get('snippet', '')}")
        return "\n".join(lines) if lines else "No results found"
