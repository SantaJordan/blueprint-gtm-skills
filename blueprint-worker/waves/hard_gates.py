"""
Hard Gates: 5-Gate Segment Validation

Validates each segment against 5 mandatory gates:
1. Horizontal Disqualification (ICP specificity)
2. Causal Link Constraint (signal proves pain)
3. No Aggregates Ban (company-specific data only)
4. Technical Feasibility Audit (detectable data)
5. Product Connection (product solves this pain)

Includes PRODUCT_DOMAIN_MAP for fast domain-based pre-validation.
"""
from typing import Dict, List, Optional, Tuple
import re
import asyncio

from tools.claude_retry import call_claude_with_retry


# Product type to pain domain mapping for fast Gate 5 pre-check
# If segment description contains terms from invalid_keywords, auto-destroy
PRODUCT_DOMAIN_MAP = {
    # Contact sharing / networking products (e.g., Blinq, Popl)
    "contact_networking": {
        "keywords": ["contact", "card", "networking", "connect", "share contact", "business card"],
        "valid_domains": [
            "contact sharing", "networking events", "employee onboarding",
            "sales introductions", "conference networking", "lead capture",
            "contact management", "digital business card"
        ],
        "invalid_domains": [
            "compliance deadlines", "license management", "regulatory violations",
            "EPA violations", "OSHA citations", "FDA warnings", "CMS deficiencies",
            "audit preparation", "permit expiration", "regulatory fines"
        ]
    },
    # Sales engagement / productivity (e.g., Mixmax, Outreach)
    "sales_engagement": {
        "keywords": ["sales", "email", "sequence", "outreach", "engagement", "prospecting"],
        "valid_domains": [
            "sales productivity", "email engagement", "meeting booking",
            "sales pipeline", "prospecting efficiency", "follow-up automation",
            "response rates", "sales workflow", "inbox management"
        ],
        "invalid_domains": [
            "healthcare compliance", "environmental violations", "food safety",
            "trucking regulations", "nursing home deficiencies", "medical licensing"
        ]
    },
    # Restaurant management (e.g., Owner.com, Toast)
    "restaurant_management": {
        "keywords": ["restaurant", "menu", "online ordering", "food service", "hospitality"],
        "valid_domains": [
            "online ordering", "menu management", "restaurant marketing",
            "customer reviews", "delivery operations", "table booking",
            "food cost management", "staff scheduling"
        ],
        "invalid_domains": [
            "trucking violations", "nursing home deficiencies", "EPA compliance",
            "pharmaceutical regulations", "financial audits"
        ]
    },
    # Healthcare / compliance (e.g., Hint Health, Jane App)
    "healthcare_compliance": {
        "keywords": ["healthcare", "patient", "EHR", "medical", "HIPAA", "clinical"],
        "valid_domains": [
            "patient management", "healthcare billing", "clinical workflows",
            "HIPAA compliance", "EHR integration", "medical scheduling",
            "patient engagement", "care coordination", "medical licensing"
        ],
        "invalid_domains": [
            "trucking violations", "restaurant inspections", "sales prospecting",
            "networking events", "contact sharing"
        ]
    },
    # Compliance / regulatory (generic)
    "compliance_regulatory": {
        "keywords": ["compliance", "regulatory", "audit", "violation", "inspection"],
        "valid_domains": [
            "regulatory violations", "audit preparation", "compliance deadlines",
            "permit management", "license renewal", "inspection readiness",
            "violation remediation", "compliance tracking"
        ],
        "invalid_domains": [
            "general productivity", "sales efficiency", "networking",
            "contact sharing", "social events"
        ]
    }
}


def detect_product_type(company_context: Dict) -> Optional[str]:
    """Detect product type from company context to enable domain pre-check."""
    offering = company_context.get("offering", "").lower()
    company_name = company_context.get("company_name", "").lower()

    for product_type, config in PRODUCT_DOMAIN_MAP.items():
        for keyword in config["keywords"]:
            if keyword.lower() in offering or keyword.lower() in company_name:
                return product_type

    return None


def pre_check_domain_fit(
    segment_description: str,
    product_type: str
) -> Tuple[bool, Optional[str]]:
    """
    Fast domain pre-check BEFORE LLM validation.

    Returns:
        (should_proceed, reason) - NOW ALWAYS proceeds (warning only, no auto-destroy)
    """
    if product_type not in PRODUCT_DOMAIN_MAP:
        return True, None  # Unknown product type, proceed to LLM

    config = PRODUCT_DOMAIN_MAP[product_type]
    description_lower = segment_description.lower()

    # Check for invalid domain keywords - WARNING ONLY (V4 fix - no longer auto-destroys)
    for invalid_term in config["invalid_domains"]:
        if invalid_term.lower() in description_lower:
            # V4 FIX: Changed from auto-destroy to warning only
            # Let LLM make final call - pre-check was too aggressive
            print(f"[Hard Gates] DOMAIN WARNING: Segment mentions '{invalid_term}' - flagging for LLM review")
            return True, f"Warning: Segment mentions '{invalid_term}' (flagged for review)"

    # Check for at least one valid domain keyword (optional, just for logging)
    has_valid = any(
        valid_term.lower() in description_lower
        for valid_term in config["valid_domains"]
    )

    if not has_valid:
        # Warn but don't auto-destroy - let LLM make final call
        print(f"[Hard Gates] Warning: Segment may not align with {product_type} valid domains")

    return True, None


class HardGates:
    """Hard Gates: Validate segments against 5 mandatory quality gates."""

    VALIDATION_PROMPT = """Validate this pain segment against 5 mandatory gates.

SEGMENT: {segment_name}
DESCRIPTION: {segment_description}
DATA SOURCES: {data_sources}
FIELDS: {fields}

PRODUCT CONTEXT:
Core Problem: {core_problem}
Valid Pain Domains: {valid_domains}
Invalid Pain Domains: {invalid_domains}

VALIDATE EACH GATE:

GATE 1: HORIZONTAL DISQUALIFICATION
- Is the ICP operationally specific?
- NOT "any B2B company," "SaaS companies," "sales teams" (generic)
- MUST have industry + regulatory/operational context
- FAIL = AUTO-DESTROY

GATE 2: CAUSAL LINK CONSTRAINT
- Does the signal DIRECTLY PROVE the pain?
- NOT growth proxies (funding, hiring, expansion, M&A)
- Ask: "Could they have this signal but NOT have the pain?" If YES = FAIL
- FAIL = AUTO-DESTROY

GATE 3: NO AGGREGATES BAN
- Are ALL statistics company-specific?
- NOT industry averages presented as insights
- ALLOWED format: "Your [X] vs benchmark [Y]"
- FAIL = Can revise once

GATE 4: TECHNICAL FEASIBILITY AUDIT
- Can you name the API field or scraping selector?
- Can you explain the mechanical detection method?
- NOT "we could infer" or "likely detectable"
- FAIL = Can revise once

GATE 5: PRODUCT CONNECTION (CRITICAL)
- Does resolving this pain require/benefit from this product?
- Ask: "If prospect resolves this pain, would they NEED this product?"
- Check against valid/invalid pain domains
- FAIL = AUTO-DESTROY (no revision possible)

Return validation in this format:

GATE_1: PASS/FAIL
- ICP: [description]
- Rationale: [why]

GATE_2: PASS/FAIL
- Signal: [what data signal]
- Pain: [what pain it proves]
- Rationale: [why]

GATE_3: PASS/FAIL
- Statistics: [list]
- Company-specific: YES/NO
- Rationale: [why]

GATE_4: PASS/FAIL
- Detection method: [how to detect]
- Fields: [specific fields/selectors]
- Rationale: [why]

GATE_5: PASS/FAIL
- Pain: [identified pain]
- Product connection: [how product solves]
- Domain check: VALID/INVALID
- Rationale: [why]

VERDICT: PROCEED / DESTROY / REVISE_ONCE
CAN_REVISE: YES/NO (only YES if failed Gate 3 or 4 only)"""

    def __init__(self, claude_client):
        self.claude = claude_client
        self._product_type = None  # Cached product type for pre-check

    async def validate(
        self,
        segments: List[Dict],
        product_fit: Dict,
        company_context: Dict = None
    ) -> List[Dict]:
        """
        Validate all segments against hard gates IN PARALLEL.

        Uses a 2-phase approach:
        1. Fast domain pre-check (no LLM) - auto-destroy mismatched segments
        2. Full LLM validation for remaining segments

        Args:
            segments: List of segments from Synthesis
            product_fit: Output from Wave 0.5
            company_context: Optional company context for domain pre-check

        Returns:
            List of validated segments that passed all 5 gates
        """
        if not segments:
            return []

        # Detect product type for domain pre-check
        if company_context:
            self._product_type = detect_product_type(company_context)
            if self._product_type:
                print(f"[Hard Gates] Product type detected: {self._product_type}")

        # Phase 0: Fast domain pre-check (no LLM call)
        pre_checked_segments = []
        destroyed_count = 0

        for segment in segments:
            if self._product_type:
                should_proceed, reason = pre_check_domain_fit(
                    segment.get("description", ""),
                    self._product_type
                )
                if not should_proceed:
                    print(f"[Hard Gates] PRE-CHECK DESTROY: {segment.get('name', 'Unknown')} - {reason}")
                    destroyed_count += 1
                    continue

            pre_checked_segments.append(segment)

        if destroyed_count > 0:
            print(f"[Hard Gates] Pre-check destroyed {destroyed_count}/{len(segments)} segments")

        if not pre_checked_segments:
            print("[Hard Gates] All segments destroyed by pre-check")
            return []

        # Phase 1: Validate remaining segments in parallel
        validation_tasks = [
            self._validate_segment(segment, product_fit)
            for segment in pre_checked_segments
        ]
        results = await asyncio.gather(*validation_tasks, return_exceptions=True)

        # Phase 2: Identify segments that passed, failed, or need revision
        validated = []
        needs_revision = []

        for segment, result in zip(pre_checked_segments, results):
            # Handle exceptions from gather
            if isinstance(result, Exception):
                print(f"[Hard Gates] Validation error for {segment.get('name', 'Unknown')}: {result}")
                continue

            if result["verdict"] == "PROCEED":
                segment["validation"] = result
                validated.append(segment)
            elif result["verdict"] == "REVISE_ONCE" and result.get("can_revise"):
                needs_revision.append((segment, result))

        # Phase 3: Process all revisions in parallel
        if needs_revision:
            revision_tasks = [
                self._revise_segment(segment, result, product_fit)
                for segment, result in needs_revision
            ]
            revised_results = await asyncio.gather(*revision_tasks, return_exceptions=True)

            for revised in revised_results:
                if revised and not isinstance(revised, Exception):
                    validated.append(revised)

        return validated

    async def _validate_segment(self, segment: Dict, product_fit: Dict) -> Dict:
        """Validate a single segment against all 5 gates."""
        # V5: Add pre-validation check for obvious product mismatches
        pre_check_fail = self._pre_validate_gate5(segment, product_fit)
        if pre_check_fail:
            print(f"[Hard Gates] PRE-CHECK GATE 5 FAIL: {segment.get('name')} - {pre_check_fail}")
            return {
                "gates": {
                    "gate_1": {"passed": True, "rationale": "Pre-check only"},
                    "gate_2": {"passed": True, "rationale": "Pre-check only"},
                    "gate_3": {"passed": True, "rationale": "Pre-check only"},
                    "gate_4": {"passed": True, "rationale": "Pre-check only"},
                    "gate_5": {"passed": False, "rationale": pre_check_fail}
                },
                "verdict": "DESTROY",
                "can_revise": False,
                "pre_check_fail": True
            }

        prompt = self.VALIDATION_PROMPT.format(
            segment_name=segment.get("name", "Unknown"),
            segment_description=segment.get("description", ""),
            data_sources=", ".join(segment.get("data_sources", [])),
            fields=", ".join(segment.get("fields", [])),
            core_problem=product_fit.get("core_problem", "Unknown"),
            valid_domains=", ".join(product_fit.get("valid_domains", [])),
            invalid_domains=", ".join(product_fit.get("invalid_domains", []))
        )

        response = await call_claude_with_retry(
            self.claude,
            model="claude-sonnet-4-5-20250929",  # Use Sonnet 4.5 for validation (faster)
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )

        return self._parse_validation(response.content[0].text)

    def _parse_validation(self, text: str) -> Dict:
        """Parse validation response."""
        result = {
            "gates": {
                "gate_1": {"passed": False, "rationale": ""},
                "gate_2": {"passed": False, "rationale": ""},
                "gate_3": {"passed": False, "rationale": ""},
                "gate_4": {"passed": False, "rationale": ""},
                "gate_5": {"passed": False, "rationale": ""}
            },
            "verdict": "DESTROY",
            "can_revise": False
        }

        # Parse each gate
        for i in range(1, 6):
            pattern = rf"GATE_{i}:\s*(PASS|FAIL)"
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result["gates"][f"gate_{i}"]["passed"] = match.group(1).upper() == "PASS"

            # Extract rationale
            rationale_pattern = rf"GATE_{i}:.*?Rationale:\s*(.+?)(?=GATE_|VERDICT|$)"
            rationale_match = re.search(rationale_pattern, text, re.DOTALL | re.IGNORECASE)
            if rationale_match:
                result["gates"][f"gate_{i}"]["rationale"] = rationale_match.group(1).strip()[:200]

        # Parse verdict
        verdict_match = re.search(r"VERDICT:\s*(PROCEED|DESTROY|REVISE_ONCE)", text, re.IGNORECASE)
        if verdict_match:
            result["verdict"] = verdict_match.group(1).upper()

        # Parse can_revise
        revise_match = re.search(r"CAN_REVISE:\s*(YES|NO)", text, re.IGNORECASE)
        if revise_match:
            result["can_revise"] = revise_match.group(1).upper() == "YES"

        # Override logic: if gates 1, 2, or 5 failed, cannot proceed
        critical_failures = not (
            result["gates"]["gate_1"]["passed"] and
            result["gates"]["gate_2"]["passed"] and
            result["gates"]["gate_5"]["passed"]
        )

        if critical_failures:
            result["verdict"] = "DESTROY"
            result["can_revise"] = False

        return result

    async def _revise_segment(self, segment: Dict, validation: Dict, product_fit: Dict) -> Dict:
        """Attempt to revise a segment that failed Gate 3 or 4 only."""
        failed_gates = []
        if not validation["gates"]["gate_3"]["passed"]:
            failed_gates.append("Gate 3 (Aggregates)")
        if not validation["gates"]["gate_4"]["passed"]:
            failed_gates.append("Gate 4 (Feasibility)")

        prompt = f"""This segment failed validation. Revise it to pass.

ORIGINAL SEGMENT:
Name: {segment.get('name', '')}
Description: {segment.get('description', '')}
Data Sources: {', '.join(segment.get('data_sources', []))}
Fields: {', '.join(segment.get('fields', []))}

FAILED GATES: {', '.join(failed_gates)}

GATE FEEDBACK:
{validation["gates"]["gate_3"]["rationale"] if not validation["gates"]["gate_3"]["passed"] else ""}
{validation["gates"]["gate_4"]["rationale"] if not validation["gates"]["gate_4"]["passed"] else ""}

PRODUCT CONTEXT:
Core Problem: {product_fit.get('core_problem', '')}
Valid Domains: {', '.join(product_fit.get('valid_domains', []))}

REVISE THE SEGMENT to:
- Use company-specific statistics (not industry averages) for Gate 3
- Specify exact API fields or scraping selectors for Gate 4

Output the revised segment:
REVISED_SEGMENT:
- Name: [name]
- Description: [description]
- Data Sources: [sources]
- Fields: [specific field names/selectors]
- Message Type: [PQS or PVP]"""

        response = await call_claude_with_retry(
            self.claude,
            model="claude-sonnet-4-5-20250929",  # Use Sonnet 4.5 for revision (faster)
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse revised segment
        revised = self._parse_revised_segment(response.content[0].text, segment)

        if revised:
            # Validate the revision
            revision_result = await self._validate_segment(revised, product_fit)
            if revision_result["verdict"] == "PROCEED":
                revised["validation"] = revision_result
                return revised

        return None

    def _parse_revised_segment(self, text: str, original: Dict) -> Dict:
        """Parse revised segment from response."""
        segment = original.copy()

        name_match = re.search(r'Name[:\s]+(.+?)(?=\n-|$)', text)
        if name_match:
            segment["name"] = name_match.group(1).strip()

        desc_match = re.search(r'Description[:\s]+(.+?)(?=\n-|$)', text, re.DOTALL)
        if desc_match:
            segment["description"] = desc_match.group(1).strip()

        sources_match = re.search(r'Data Sources?[:\s]+(.+?)(?=\n-|$)', text, re.DOTALL)
        if sources_match:
            sources_text = sources_match.group(1)
            segment["data_sources"] = [s.strip() for s in re.split(r'[+,\[\]]', sources_text) if s.strip()]

        fields_match = re.search(r'Fields?[:\s]+(.+?)(?=\n-|$)', text, re.DOTALL)
        if fields_match:
            fields_text = fields_match.group(1)
            segment["fields"] = [f.strip() for f in re.split(r'[,\[\]]', fields_text) if f.strip()]

        return segment

    def _pre_validate_gate5(self, segment: Dict, product_fit: Dict) -> Optional[str]:
        """
        V5: Pre-validate Gate 5 without LLM call for obvious mismatches.

        Returns:
            None if validation passes
            Error message string if validation fails
        """
        segment_name = segment.get("name", "").lower()
        segment_desc = segment.get("description", "").lower()
        combined_text = f"{segment_name} {segment_desc}"

        # Get product type from product_fit (if Wave 0.5 detected it)
        product_type = product_fit.get("product_type", "").lower()
        valid_domains = [d.lower() for d in product_fit.get("valid_domains", [])]
        invalid_domains = [d.lower() for d in product_fit.get("invalid_domains", [])]

        # Hard-coded red flags that are NEVER valid for specific product types
        # These are based on QA findings where Modal generated completely wrong segments
        HARD_REJECTION_MAP = {
            # Restaurant platforms should NEVER have engineering/SaaS segments
            "restaurant": [
                ("engineering team", "Engineering teams are not restaurant customers"),
                ("series a", "Funding rounds are not restaurant pain points"),
                ("series b", "Funding rounds are not restaurant pain points"),
                ("saas metrics", "SaaS metrics don't apply to restaurants"),
                ("software development", "Software development is not restaurant pain"),
                ("tech startup", "Tech startups are not the ICP for restaurant platforms"),
                ("venture capital", "VC funding is not relevant to restaurant platforms"),
            ],
            # Healthcare DPC platforms should NEVER have beverage segments
            "healthcare": [
                ("beverage", "Beverages are not healthcare pain points"),
                ("vending machine", "Vending machines are not DPC pain points"),
                ("sugary drink", "Sugary drinks are not healthcare software pain"),
                ("water brand", "Water brands are not DPC customers"),
                ("consumer packaged", "CPG is not healthcare software pain"),
                ("retail distribution", "Retail distribution is not DPC pain"),
            ],
            "dpc": [
                ("beverage", "Beverages are not DPC pain points"),
                ("vending machine", "Vending machines are not DPC pain points"),
                ("sugary drink", "Sugary drinks are not DPC pain"),
                ("water brand", "Water brands are not DPC customers"),
            ],
            # Sales engagement should NEVER have healthcare compliance segments
            "sales": [
                ("healthcare compliance", "Healthcare compliance is not sales pain"),
                ("medical billing", "Medical billing is not sales engagement pain"),
                ("patient care", "Patient care is not sales engagement pain"),
                ("nursing home", "Nursing homes are not sales engagement ICP"),
                ("cms deficiency", "CMS deficiencies are not sales pain"),
            ],
            # Contact networking should NEVER have regulatory segments
            "contact": [
                ("regulatory violation", "Regulatory violations not solved by contact sharing"),
                ("compliance deadline", "Compliance deadlines not solved by business cards"),
                ("license renewal", "License renewal not solved by networking"),
                ("epa citation", "EPA citations not solved by contact sharing"),
                ("osha violation", "OSHA violations not solved by business cards"),
            ],
            "networking": [
                ("regulatory violation", "Regulatory violations not solved by networking"),
                ("compliance deadline", "Compliance deadlines not solved by networking"),
                ("license renewal", "License renewal not solved by networking"),
            ]
        }

        # Check if product type matches any rejection category
        for category, rejections in HARD_REJECTION_MAP.items():
            if category in product_type or any(category in vd for vd in valid_domains):
                for (red_flag, reason) in rejections:
                    if red_flag in combined_text:
                        return f"Product-segment mismatch: {reason}"

        # Check against explicit invalid domains from product_fit
        for invalid in invalid_domains:
            if invalid and invalid in combined_text:
                return f"Segment mentions invalid domain: {invalid}"

        # Additional check: segment should mention at least one valid domain
        # (soft check - only warn, don't auto-fail)
        if valid_domains:
            has_valid = any(vd in combined_text for vd in valid_domains if vd)
            if not has_valid:
                # Log warning but don't auto-fail - let LLM make final call
                print(f"[Hard Gates] WARNING: Segment '{segment.get('name')}' doesn't mention any valid domain")

        return None  # Validation passed
