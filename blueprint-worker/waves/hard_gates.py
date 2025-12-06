"""
Hard Gates: 5-Gate Segment Validation

Validates each segment against 5 mandatory gates:
1. Horizontal Disqualification (ICP specificity)
2. Causal Link Constraint (signal proves pain)
3. No Aggregates Ban (company-specific data only)
4. Technical Feasibility Audit (detectable data)
5. Product Connection (product solves this pain)
"""
from typing import Dict, List
import re


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

    async def validate(self, segments: List[Dict], product_fit: Dict) -> List[Dict]:
        """
        Validate all segments against hard gates.

        Args:
            segments: List of segments from Synthesis
            product_fit: Output from Wave 0.5

        Returns:
            List of validated segments that passed all 5 gates
        """
        validated = []

        for segment in segments:
            result = await self._validate_segment(segment, product_fit)

            if result["verdict"] == "PROCEED":
                segment["validation"] = result
                validated.append(segment)
            elif result["verdict"] == "REVISE_ONCE" and result.get("can_revise"):
                # Attempt one revision
                revised = await self._revise_segment(segment, result, product_fit)
                if revised:
                    validated.append(revised)

        return validated

    async def _validate_segment(self, segment: Dict, product_fit: Dict) -> Dict:
        """Validate a single segment against all 5 gates."""
        prompt = self.VALIDATION_PROMPT.format(
            segment_name=segment.get("name", "Unknown"),
            segment_description=segment.get("description", ""),
            data_sources=", ".join(segment.get("data_sources", [])),
            fields=", ".join(segment.get("fields", [])),
            core_problem=product_fit.get("core_problem", "Unknown"),
            valid_domains=", ".join(product_fit.get("valid_domains", [])),
            invalid_domains=", ".join(product_fit.get("invalid_domains", []))
        )

        response = await self.claude.messages.create(
            model="claude-opus-4-20250514",  # Use Opus for quality judgment
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

        response = await self.claude.messages.create(
            model="claude-sonnet-4-20250514",
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
