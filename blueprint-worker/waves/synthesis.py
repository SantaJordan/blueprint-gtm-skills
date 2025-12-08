"""
Synthesis: Extended Thinking for Segment Generation

Uses Claude's native extended thinking API to generate pain segment hypotheses
that combine available data sources with deep reasoning.
"""
from typing import Dict, List
import re

from tools.claude_retry import call_claude_with_retry

# Extended thinking budget tiers
THINKING_BUDGET_STANDARD = 8000   # Standard synthesis (2-5 data sources)
THINKING_BUDGET_COMPLEX = 16000  # Complex synthesis (6+ data sources)


class Synthesis:
    """Synthesis: Generate pain segments using extended thinking."""

    # Removed SYSTEM_PROMPT - extended thinking doesn't use system prompts

    def __init__(self, claude_client):
        self.claude = claude_client

    async def generate_segments(
        self,
        company_context: Dict,
        data_landscape: Dict,
        product_fit: Dict
    ) -> Dict:
        """
        Use extended thinking to generate pain segments.

        Args:
            company_context: Output from Wave 1
            data_landscape: Output from Wave 2
            product_fit: Output from Wave 0.5

        Returns:
            {
                "segments": [
                    {
                        "name": str,
                        "description": str,
                        "data_sources": [str],
                        "fields": [str],
                        "confidence": str,
                        "texada_check": {...},
                        "message_type": str
                    }
                ],
                "thinking": str,
                "success": bool
            }
        """
        # Count data sources to determine thinking budget
        source_count = sum(
            len(sources) for sources in data_landscape.values()
            if isinstance(sources, list)
        )
        thinking_budget = THINKING_BUDGET_COMPLEX if source_count > 5 else THINKING_BUDGET_STANDARD
        print(f"[Synthesis] {source_count} data sources detected, using {thinking_budget} token thinking budget")

        # Get product category if available (from Wave 1 validation)
        product_category = company_context.get('product_category', '')

        # Build comprehensive prompt for extended thinking
        prompt = f"""You are generating pain segment hypotheses for Blueprint GTM outreach.

COMPANY CONTEXT:
Company: {company_context.get('company_name', 'Unknown')}
Offering: {company_context.get('offering', 'Unknown')}
Product Category: {product_category or 'General'}
ICP: {company_context.get('icp', 'Unknown')}
Target Persona: {company_context.get('persona_title', 'Unknown')} - {company_context.get('persona', '')}

PRODUCT FIT ANALYSIS:
Core Problem Solved: {product_fit.get('core_problem', 'Unknown')}
Valid Pain Domains: {', '.join(product_fit.get('valid_domains', []))}
Invalid Pain Domains: {', '.join(product_fit.get('invalid_domains', []))}

DATA LANDSCAPE (Available Sources):
{self._format_data_landscape(data_landscape)}

=== CRITICAL PRODUCT-SEGMENT ALIGNMENT CONSTRAINT ===

**MANDATORY TEST**: For EVERY segment you generate, answer this question:
"If a company in this segment resolves their pain, would they NEED {company_context.get('company_name', 'this product')}?"
If the answer is NO, the segment is INVALID and MUST NOT be included.

**PRODUCT**: {company_context.get('offering', 'Unknown')}
**CORE PROBLEM IT SOLVES**: {product_fit.get('core_problem', 'Unknown')}

**DO NOT generate segments about:**
- Generic tech/SaaS pain (like "engineering team growth") unless the product is specifically for engineering teams
- Verticals that don't match the product's ICP: {company_context.get('icp', 'Unknown')}
- Pain that doesn't require THIS SPECIFIC PRODUCT to solve
- Funding rounds, hiring, or M&A unless the product directly serves those moments

**PRODUCT-SPECIFIC EXAMPLES:**
{self._get_product_examples(product_category, company_context)}

=== END CONSTRAINT ===

TASK: Generate 2-4 pain segment hypotheses using ONLY the data sources listed above.

CRITICAL REQUIREMENTS:
1. Each segment MUST combine 2-3 data sources for non-obvious synthesis
2. Use specific field names from the data sources (not generic placeholders)
3. Validate against Texada Test:
   - HYPER-SPECIFIC: Uses actual field names, dates, record numbers (NOT "recent", "many", "several")
   - FACTUALLY GROUNDED: Every claim traces to specific database field, NO assumptions
   - NON-OBVIOUS: Insight the persona doesn't already have access to
4. Classify as PQS (pure government data mirror, 90%+ data) or PVP (hybrid value delivery, 60-75%)
5. Ensure segment connects to product's VALID pain domains (not invalid ones!)
6. **NEW**: Each segment MUST pass the product-alignment test above

OUTPUT FORMAT (exactly as shown):

SEGMENT 1:
- Name: [descriptive segment name]
- Description: [what painful situation this captures and why it matters]
- Data Sources: [source1 + source2 + source3]
- Fields: [specific field names to extract from each source]
- Confidence: [HIGH 90%+ / MEDIUM 60-75% / LOW 50-70%]
- Texada: [PASS/FAIL] Hyper-specific, [PASS/FAIL] Factually Grounded, [PASS/FAIL] Non-obvious
- Message Type: [PQS or PVP]

SEGMENT 2:
...

SEGMENT 3:
..."""

        response = await call_claude_with_retry(
            self.claude,
            model="claude-sonnet-4-5-20250929",  # Sonnet 4.5 supports extended thinking
            max_tokens=16000,  # Higher for extended thinking response
            messages=[{"role": "user", "content": prompt}],
            thinking_budget=thinking_budget
        )

        # Extract text and thinking from response
        raw_text = ""
        thinking_text = ""
        for block in response.content:
            if hasattr(block, 'type'):
                if block.type == "thinking":
                    thinking_text = getattr(block, 'thinking', '')
                elif block.type == "text":
                    raw_text = getattr(block, 'text', '')
            elif hasattr(block, 'text'):
                raw_text = block.text

        print(f"[Synthesis] Extended thinking used {len(thinking_text)} chars of reasoning")
        segments = self._parse_segments(raw_text)

        # Post-generation validation: filter out segments that don't align with product
        validated_segments = []
        rejected_count = 0
        for segment in segments:
            if self._validate_segment_product_fit(segment, company_context, product_fit):
                validated_segments.append(segment)
            else:
                rejected_count += 1
                print(f"[Synthesis] REJECTED segment: '{segment.get('name')}' - product misalignment")

        if rejected_count > 0:
            print(f"[Synthesis] Post-validation: {rejected_count}/{len(segments)} segments rejected for product misalignment")

        return {
            "segments": validated_segments,
            "thinking": thinking_text,  # Store actual thinking for debugging
            "raw_output": raw_text,
            "segments_rejected": rejected_count,
            "success": len(validated_segments) > 0
        }

    def _parse_segments(self, text: str) -> List[Dict]:
        """Parse segment definitions from thinking output."""
        segments = []

        # Find SEGMENT blocks
        segment_pattern = r'SEGMENT\s*\d+[:\s]+(.+?)(?=SEGMENT\s*\d+|$)'
        matches = re.findall(segment_pattern, text, re.DOTALL | re.IGNORECASE)

        for match in matches:
            segment = {
                "name": "",
                "description": "",
                "data_sources": [],
                "fields": [],
                "confidence": "MEDIUM",
                "texada_check": {
                    "hyper_specific": False,
                    "factually_grounded": False,
                    "non_obvious": False
                },
                "message_type": "PQS"
            }

            # Parse fields
            name_match = re.search(r'Name[:\s]+(.+?)(?=\n-|\n[A-Z]|$)', match)
            if name_match:
                segment["name"] = name_match.group(1).strip()

            desc_match = re.search(r'Description[:\s]+(.+?)(?=\n-|\n[A-Z]|$)', match, re.DOTALL)
            if desc_match:
                segment["description"] = desc_match.group(1).strip()

            sources_match = re.search(r'Data Sources?[:\s]+(.+?)(?=\n-|\nFields|$)', match, re.DOTALL)
            if sources_match:
                sources_text = sources_match.group(1)
                segment["data_sources"] = [s.strip() for s in re.split(r'[+,\[\]]', sources_text) if s.strip()]

            fields_match = re.search(r'Fields?[:\s]+(.+?)(?=\n-|\nConfidence|$)', match, re.DOTALL)
            if fields_match:
                fields_text = fields_match.group(1)
                segment["fields"] = [f.strip() for f in re.split(r'[,\[\]]', fields_text) if f.strip()]

            conf_match = re.search(r'Confidence[:\s]+(HIGH|MEDIUM|LOW)', match, re.IGNORECASE)
            if conf_match:
                segment["confidence"] = conf_match.group(1).upper()

            type_match = re.search(r'Message Type[:\s]+(PQS|PVP)', match, re.IGNORECASE)
            if type_match:
                segment["message_type"] = type_match.group(1).upper()

            # Check Texada criteria
            texada_match = re.search(r'Texada[:\s]+(.+?)(?=\n-|\nMessage|$)', match, re.DOTALL)
            if texada_match:
                texada_text = texada_match.group(1).lower()
                segment["texada_check"]["hyper_specific"] = "pass" in texada_text.split("hyper")[0] if "hyper" in texada_text else False
                segment["texada_check"]["factually_grounded"] = "pass" in texada_text
                segment["texada_check"]["non_obvious"] = "pass" in texada_text

            if segment["name"]:
                segments.append(segment)

        return segments

    def _format_data_landscape(self, data_landscape: Dict) -> str:
        """Format data landscape for prompt."""
        lines = []

        for category, sources in data_landscape.items():
            if isinstance(sources, list) and sources:
                lines.append(f"\n{category.upper()}:")
                for source in sources:
                    if isinstance(source, dict):
                        name = source.get('name', 'Unknown')
                        feasibility = source.get('feasibility', 'UNKNOWN')
                        fields = source.get('fields', [])
                        lines.append(f"  - {name} ({feasibility} feasibility)")
                        if fields:
                            lines.append(f"    Fields: {', '.join(fields[:5])}")

        return "\n".join(lines) if lines else "Limited data sources available"

    def _get_product_examples(self, product_category: str, company_context: Dict) -> str:
        """Get product-specific segment examples to guide synthesis."""
        company_name = company_context.get('company_name', 'Unknown')
        offering = company_context.get('offering', 'Unknown')

        # Product category specific examples
        PRODUCT_EXAMPLES = {
            "restaurant_platform": f"""
For {company_name} (restaurant online ordering/website platform):
GOOD segments:
- Restaurants with declining Google review velocity (needs marketing help)
- Multi-location restaurants with inconsistent online ordering (needs unified platform)
- Restaurants paying 25%+ DoorDash commissions (needs direct ordering to save money)
BAD segments (DO NOT generate these):
- "Post-Series-A Engineering Team Explosion" - NOT relevant to restaurants
- "SaaS Metrics Dashboard Adoption" - restaurants don't care about SaaS metrics
- Generic "growing companies" - be specific to RESTAURANTS
""",
            "healthcare_dpc": f"""
For {company_name} (DPC/primary care software):
GOOD segments:
- DPC practices approaching Medicare compliance deadlines (needs billing software)
- Primary care clinics with high patient churn (needs patient management)
- Physicians transitioning from insurance to DPC model (needs membership management)
BAD segments (DO NOT generate these):
- "Beverage distribution" or "vending machines" - NOT healthcare
- "Restaurant health inspections" - wrong type of health
- "Consumer beverage preferences" - NOT DPC software
""",
            "sales_engagement": f"""
For {company_name} (sales engagement/email platform):
GOOD segments:
- Sales teams with declining email response rates (needs better engagement tools)
- SDR teams using 3+ disconnected tools (needs unified platform)
- Companies with long sales cycles seeking to improve follow-up (needs sequences)
BAD segments (DO NOT generate these):
- "Healthcare compliance violations" - sales tools don't fix compliance
- "Restaurant ordering" - not relevant to sales engagement
- "Environmental permits" - not a sales problem
""",
            "contact_networking": f"""
For {company_name} (digital business cards/contact sharing):
GOOD segments:
- Companies onboarding 10+ new employees per month (needs contact sharing at scale)
- Sales teams attending 5+ conferences per year (needs networking tools)
- Professional services firms with high client turnover (needs contact management)
BAD segments (DO NOT generate these):
- "Regulatory compliance violations" - not solved by contact sharing
- "EPA or OSHA citations" - wrong domain entirely
- "License renewal deadlines" - not a networking problem
""",
            "healthcare_ehr": f"""
For {company_name} (EHR/electronic health records):
GOOD segments:
- Clinics migrating from paper records (needs digitization)
- Practices failing interoperability requirements (needs compliant EHR)
- Healthcare organizations with duplicate patient records (needs data cleanup)
BAD segments (DO NOT generate these):
- Generic "tech company scaling" - be specific to healthcare
- "Sales team productivity" - wrong vertical
- "Restaurant management" - not healthcare
"""
        }

        # Return specific examples if category matches, otherwise generic guidance
        if product_category and product_category in PRODUCT_EXAMPLES:
            return PRODUCT_EXAMPLES[product_category]

        # Generic fallback
        return f"""
For {company_name} ({offering}):
GOOD segments: Pain that THIS PRODUCT directly solves
BAD segments: Generic business pain unrelated to the product

Think: "Would buying {company_name} solve this specific problem?" If NO, reject the segment.
"""

    def _validate_segment_product_fit(
        self,
        segment: Dict,
        company_context: Dict,
        product_fit: Dict
    ) -> bool:
        """
        Post-generation validation that segment actually aligns with product.

        Returns True if segment passes product fit check, False otherwise.
        """
        segment_name = segment.get("name", "").lower()
        segment_desc = segment.get("description", "").lower()
        product_category = company_context.get("product_category", "")
        offering = company_context.get("offering", "").lower()

        # Define red flag keywords per product category
        RED_FLAGS = {
            "restaurant_platform": [
                "engineering team", "series a", "series b", "funding round",
                "saas metrics", "software development", "tech startup", "venture"
            ],
            "healthcare_dpc": [
                "beverage", "vending", "sugary", "drinks", "water brand",
                "consumer packaged", "retail distribution"
            ],
            "sales_engagement": [
                "healthcare compliance", "medical billing", "patient care",
                "restaurant ordering", "food service", "environmental permit"
            ],
            "contact_networking": [
                "regulatory violation", "compliance deadline", "license renewal",
                "epa citation", "osha violation", "cms deficiency"
            ]
        }

        # Check for red flags based on product category
        if product_category and product_category in RED_FLAGS:
            for red_flag in RED_FLAGS[product_category]:
                if red_flag in segment_name or red_flag in segment_desc:
                    print(f"[Synthesis] RED FLAG: Segment '{segment.get('name')}' contains '{red_flag}' - misaligned with {product_category}")
                    return False

        # Positive check: segment should mention something related to the product
        # Extract key product terms from offering
        product_terms = [term.strip().lower() for term in offering.split() if len(term) > 3]

        # For known categories, check for category-relevant terms
        CATEGORY_TERMS = {
            "restaurant_platform": ["restaurant", "menu", "order", "food", "delivery", "dining", "review"],
            "healthcare_dpc": ["healthcare", "patient", "clinic", "medical", "dpc", "physician", "primary care", "medicare"],
            "sales_engagement": ["sales", "email", "prospect", "outreach", "pipeline", "response", "meeting", "follow-up"],
            "contact_networking": ["contact", "network", "business card", "connect", "introduction", "conference", "event"],
            "healthcare_ehr": ["ehr", "electronic health", "patient record", "clinical", "interoperability", "hipaa"]
        }

        if product_category and product_category in CATEGORY_TERMS:
            has_relevant_term = any(
                term in segment_name or term in segment_desc
                for term in CATEGORY_TERMS[product_category]
            )
            if not has_relevant_term:
                print(f"[Synthesis] REJECTED: Segment '{segment.get('name')}' lacks {product_category} keywords")
                print(f"[Synthesis] Expected one of: {CATEGORY_TERMS[product_category][:5]}")
                # V5 FIX: STRICT enforcement - reject segments without product-relevant terms
                return False

        return True
