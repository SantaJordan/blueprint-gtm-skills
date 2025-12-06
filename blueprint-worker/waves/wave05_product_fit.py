"""
Wave 0.5: Product Value Analysis

Anchors all subsequent work on what the product ACTUALLY solves.
Prevents generating segments with data that doesn't connect to product value.
"""
from typing import Dict, List
import re


class Wave05ProductFit:
    """Wave 0.5: Product value anchoring."""

    def __init__(self, claude_client):
        self.claude = claude_client

    async def execute(self, company_context: Dict) -> Dict:
        """
        Analyze product value and define valid/invalid pain domains.

        Args:
            company_context: Output from Wave 1

        Returns:
            {
                "core_problem": str,
                "product_type": str,
                "urgency_triggers": [str],
                "target_personas": [str],
                "valid_domains": [str],
                "invalid_domains": [str],
                "product_fit_question": str
            }
        """
        prompt = f"""Analyze this product to understand its core value proposition.

COMPANY: {company_context.get('company_name', 'Unknown')}
OFFERING: {company_context.get('offering', 'Unknown')}
VALUE PROP: {company_context.get('value_prop', 'Unknown')}
TARGET PERSONA: {company_context.get('persona_title', 'Unknown')}

Answer these questions:

1. CORE PROBLEM SOLVED:
What specific PROBLEM does this product eliminate? (Not features, not benefits - the PROBLEM)
Example: "Need to share contact info quickly without paper cards"
Example: "Need to track compliance training completion to avoid survey deficiencies"

2. PRODUCT TYPE:
Classify as one of:
- Compliance/Regulatory (solves legal/regulatory requirements)
- Operational Efficiency (reduces time/cost of operations)
- Revenue Enablement (helps make more money)
- Risk Mitigation (prevents bad outcomes)
- Communication/Collaboration (improves team interaction)

3. URGENCY TRIGGERS:
What SITUATIONS create urgency for this product?
- Time pressure: (conference tomorrow, audit next week)
- Scale pressure: (100 new employees, can't process manually)
- Change pressure: (rebranding, acquisition, moving)

4. VALID PAIN DOMAINS:
Based on product type, what pain domains are VALID for this product?
List 3-5 pain domains that this product directly solves.

5. INVALID PAIN DOMAINS:
What pain domains should we REJECT for this product?
List 3-5 pain domains that are NOT relevant (even if data exists for them).

Format your response as:
CORE_PROBLEM: [1-2 sentences]
PRODUCT_TYPE: [one of the types above]
URGENCY_TRIGGERS:
- [trigger 1]
- [trigger 2]
- [trigger 3]
TARGET_PERSONAS:
- [persona 1]
- [persona 2]
VALID_DOMAINS: [domain1, domain2, domain3]
INVALID_DOMAINS: [domain1, domain2, domain3]
PRODUCT_FIT_QUESTION: "Would resolving [pain] require buying [this product]?" """

        response = await self.claude.messages.create(
            model="claude-opus-4-20250514",  # Use Opus for critical decisions
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )

        return self._parse_response(response.content[0].text)

    def _parse_response(self, text: str) -> Dict:
        """Parse Claude's response into structured data."""
        result = {
            "core_problem": "",
            "product_type": "",
            "urgency_triggers": [],
            "target_personas": [],
            "valid_domains": [],
            "invalid_domains": [],
            "product_fit_question": ""
        }

        # Extract core problem
        match = re.search(r"CORE_PROBLEM:\s*(.+?)(?=\n[A-Z_]+:|$)", text, re.DOTALL)
        if match:
            result["core_problem"] = match.group(1).strip()

        # Extract product type
        match = re.search(r"PRODUCT_TYPE:\s*(.+?)(?=\n[A-Z_]+:|$)", text, re.DOTALL)
        if match:
            result["product_type"] = match.group(1).strip()

        # Extract urgency triggers
        match = re.search(r"URGENCY_TRIGGERS:\s*(.+?)(?=\n[A-Z_]+:|$)", text, re.DOTALL)
        if match:
            triggers_text = match.group(1)
            result["urgency_triggers"] = [
                t.strip().lstrip("-").strip()
                for t in triggers_text.split("\n")
                if t.strip() and t.strip() != "-"
            ]

        # Extract target personas
        match = re.search(r"TARGET_PERSONAS:\s*(.+?)(?=\n[A-Z_]+:|$)", text, re.DOTALL)
        if match:
            personas_text = match.group(1)
            result["target_personas"] = [
                p.strip().lstrip("-").strip()
                for p in personas_text.split("\n")
                if p.strip() and p.strip() != "-"
            ]

        # Extract valid domains
        match = re.search(r"VALID_DOMAINS:\s*(.+?)(?=\n[A-Z_]+:|$)", text, re.DOTALL)
        if match:
            domains_text = match.group(1)
            result["valid_domains"] = [
                d.strip()
                for d in re.split(r'[,\[\]]', domains_text)
                if d.strip()
            ]

        # Extract invalid domains
        match = re.search(r"INVALID_DOMAINS:\s*(.+?)(?=\n[A-Z_]+:|$)", text, re.DOTALL)
        if match:
            domains_text = match.group(1)
            result["invalid_domains"] = [
                d.strip()
                for d in re.split(r'[,\[\]]', domains_text)
                if d.strip()
            ]

        # Extract product fit question
        match = re.search(r"PRODUCT_FIT_QUESTION:\s*(.+?)$", text, re.DOTALL)
        if match:
            result["product_fit_question"] = match.group(1).strip().strip('"')

        return result
