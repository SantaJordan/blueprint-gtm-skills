"""
Wave 1.5: Niche Conversion

Converts generic verticals to regulated niches with data moats.
Ensures Wave 2 searches for data moat sources, not generic signals.
"""
from typing import Dict, List
import re


class Wave15NicheConversion:
    """Wave 1.5: Convert generic verticals to regulated niches."""

    # Auto-reject generic verticals
    AUTO_REJECT = [
        "saas companies",
        "tech startups",
        "b2b companies",
        "sales teams",
        "growing companies",
        "professional services",
        "enterprises",
        "smbs",
        "startups",
    ]

    def __init__(self, claude_client, web_search):
        self.claude = claude_client
        self.web_search = web_search

    async def execute(self, company_context: Dict, product_fit: Dict) -> Dict:
        """
        Convert generic verticals to regulated niches.

        Args:
            company_context: Output from Wave 1
            product_fit: Output from Wave 0.5

        Returns:
            {
                "qualified_niches": [
                    {
                        "niche": str,
                        "original_vertical": str,
                        "score": {
                            "regulatory_footprint": int,
                            "compliance_driven_pain": int,
                            "data_accessibility": int,
                            "specificity_potential": int,
                            "product_solution_alignment": int
                        },
                        "total_score": int,
                        "tier": str
                    }
                ],
                "rejected_niches": [str],
                "fallback_needed": bool
            }
        """
        industries = company_context.get("industries_served", [])

        if not industries:
            # If no industries identified, use the ICP as a starting point
            industries = [company_context.get("icp", "general business")]

        qualified = []
        rejected = []

        for vertical in industries:
            vertical_lower = vertical.lower().strip()

            # Check if auto-reject
            if any(reject in vertical_lower for reject in self.AUTO_REJECT):
                # Need to find a regulated niche
                niche = await self._find_regulated_niche(vertical, product_fit)
                if niche:
                    score = await self._score_niche(niche, product_fit)
                    qualified.append({
                        "niche": niche,
                        "original_vertical": vertical,
                        "score": score,
                        "total_score": sum(score.values()),
                        "tier": self._determine_tier(score)
                    })
                else:
                    rejected.append(f"{vertical} (no regulated alternative found)")
            else:
                # Score the existing vertical
                score = await self._score_niche(vertical, product_fit)
                if score["product_solution_alignment"] >= 5:
                    qualified.append({
                        "niche": vertical,
                        "original_vertical": vertical,
                        "score": score,
                        "total_score": sum(score.values()),
                        "tier": self._determine_tier(score)
                    })
                else:
                    rejected.append(f"{vertical} (product-fit score too low: {score['product_solution_alignment']}/10)")

        # Sort by total score
        qualified.sort(key=lambda x: x["total_score"], reverse=True)

        # Determine if fallback is needed
        fallback_needed = all(
            n["score"]["product_solution_alignment"] < 5
            for n in qualified
        ) if qualified else True

        return {
            "qualified_niches": qualified,
            "rejected_niches": rejected,
            "fallback_needed": fallback_needed
        }

    async def _find_regulated_niche(self, generic_vertical: str, product_fit: Dict) -> str:
        """Find a regulated alternative to a generic vertical."""
        searches = [
            f"{generic_vertical} licensing board database",
            f"{generic_vertical} government records public",
            f"{generic_vertical} compliance violations database",
        ]

        results = await self.web_search.search_parallel(searches)

        # Use Claude to identify regulated niche
        prompt = f"""Given this generic vertical: "{generic_vertical}"
And this product type: {product_fit.get('product_type', 'Unknown')}

Based on these search results about regulated industries:
{self._format_search_results(results)}

Identify a SPECIFIC regulated niche that:
1. Has government/licensing databases
2. Has compliance requirements
3. Could benefit from {product_fit.get('core_problem', 'this product')}

Return ONLY the niche name (e.g., "Licensed insurance agents in multi-state operations")
If no regulated niche applies, return "NONE"
"""

        response = await self.claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}]
        )

        result = response.content[0].text.strip()
        return None if result.upper() == "NONE" else result

    async def _score_niche(self, niche: str, product_fit: Dict) -> Dict:
        """Score a niche on 5 criteria (0-10 each)."""
        prompt = f"""Score this niche on 5 criteria (0-10 for each):

NICHE: {niche}
PRODUCT CORE PROBLEM: {product_fit.get('core_problem', 'Unknown')}
PRODUCT TYPE: {product_fit.get('product_type', 'Unknown')}
VALID PAIN DOMAINS: {', '.join(product_fit.get('valid_domains', []))}

CRITERIA:

1. REGULATORY_FOOTPRINT (0-10)
How heavily regulated is this niche?
10 = Federal regulations + state licensing + mandatory reporting
0 = No regulations

2. COMPLIANCE_DRIVEN_PAIN (0-10)
How much pain comes from compliance requirements?
10 = Violations cause business shutdown, heavy fines
0 = No compliance pressure

3. DATA_ACCESSIBILITY (0-10)
How accessible is government/public data for this niche?
10 = Free APIs with documented fields, daily updates
0 = No public data available

4. SPECIFICITY_POTENTIAL (0-10)
How specific can we get with targeting?
10 = Can target by facility address, license number, violation date
0 = Only generic industry targeting possible

5. PRODUCT_SOLUTION_ALIGNMENT (0-10) - CRITICAL
Does the product directly solve this niche's pain?
10 = Product is the obvious solution to their primary pain
5 = Product helps with secondary pain
0 = No connection between niche pain and product

Return scores in this format:
REGULATORY_FOOTPRINT: [0-10]
COMPLIANCE_DRIVEN_PAIN: [0-10]
DATA_ACCESSIBILITY: [0-10]
SPECIFICITY_POTENTIAL: [0-10]
PRODUCT_SOLUTION_ALIGNMENT: [0-10]"""

        response = await self.claude.messages.create(
            model="claude-opus-4-20250514",  # Use Opus for critical scoring
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}]
        )

        return self._parse_scores(response.content[0].text)

    def _parse_scores(self, text: str) -> Dict:
        """Parse score response into dictionary."""
        scores = {
            "regulatory_footprint": 0,
            "compliance_driven_pain": 0,
            "data_accessibility": 0,
            "specificity_potential": 0,
            "product_solution_alignment": 0
        }

        patterns = {
            "regulatory_footprint": r"REGULATORY_FOOTPRINT:\s*(\d+)",
            "compliance_driven_pain": r"COMPLIANCE_DRIVEN_PAIN:\s*(\d+)",
            "data_accessibility": r"DATA_ACCESSIBILITY:\s*(\d+)",
            "specificity_potential": r"SPECIFICITY_POTENTIAL:\s*(\d+)",
            "product_solution_alignment": r"PRODUCT_SOLUTION_ALIGNMENT:\s*(\d+)",
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                scores[key] = min(10, max(0, int(match.group(1))))

        return scores

    def _determine_tier(self, score: Dict) -> str:
        """Determine tier based on scores."""
        total = sum(score.values())
        product_fit = score.get("product_solution_alignment", 0)

        if product_fit < 5:
            return "REJECTED"
        elif total >= 35 and product_fit >= 7:
            return "TIER_1"
        elif total >= 30 and product_fit >= 5:
            return "TIER_2"
        else:
            return "TIER_3"

    def _format_search_results(self, results: List[Dict]) -> str:
        """Format search results for prompt."""
        lines = []
        for r in results:
            if r.get("success"):
                for item in r.get("organic", [])[:3]:
                    lines.append(f"- {item.get('title', '')}: {item.get('snippet', '')}")
        return "\n".join(lines) if lines else "No relevant results found"
