"""
Incremental Contact Validator

Quick sanity checks for contact candidates BEFORE adding them to the candidate pool.
Catches garbage early instead of waiting for final validation.

Cost: ~$0.0001 per check (one-shot mini classification)
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Any

from ..llm.openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)


@dataclass
class QuickValidationResult:
    """Result of quick validation check"""
    is_plausible: bool
    confidence: float  # 0-100
    red_flags: list[str] = field(default_factory=list)
    reasoning: str = ""


# Known invalid patterns that should be rejected instantly (no LLM needed)
INSTANT_REJECT_PATTERNS = [
    # Obituary patterns
    "passes away", "passed away", "died", "death of", "memorial",
    "in memoriam", "obituary", "rip ", " rip",
    # Partial phrases / titles
    "senior vice", "vice president", "report project",
    "scholarships expanding", "forum ", " forum",
    # Organization names
    "rotary club", "chamber of commerce", "association", "foundation",
    "committee", "council", "group ", " group", "team ", " team",
    # Corporate keywords in name position
    "headquarters", "corporate", "international", "national",
]

# Corporate suffixes that indicate a company name, not a person
CORPORATE_SUFFIXES = [
    " inc", " inc.", " llc", " llc.", " corp", " corp.",
    " co.", " company", " services", " service", " bros",
    " brothers", " plumbing", " roofing", " hvac", " heating",
    " electric", " electrical", " construction", " contractors",
    " landscaping", " lawn", " tree", " auto", " automotive",
    " repair", " movers", " moving", " removal", " junk",
]


def is_company_name_match(contact_name: str, company_name: str) -> tuple[bool, str]:
    """
    Check if contact name is actually the company name (not a real person).

    Important: A person name like "John Miller" where only the last name matches
    "Miller's Plumbing" is VALID - the company is named after the owner.
    We only reject when the entire contact name IS the company name.

    Returns:
        (is_company_name, reason)
    """
    if not contact_name or not company_name:
        return False, ""

    contact_lower = contact_name.lower().strip()
    company_lower = company_name.lower().strip()

    # Check for corporate suffixes in the contact name - these are never person names
    for suffix in CORPORATE_SUFFIXES:
        if suffix in contact_lower:
            return True, f"Contact name contains corporate suffix: '{suffix.strip()}'"

    # If contact name looks like a person name (first + last, both capitalized in original),
    # then it's probably a real person even if part matches company name
    contact_parts = contact_name.split()
    if len(contact_parts) >= 2:
        # Check if it looks like "FirstName LastName" format
        first = contact_parts[0]
        last = contact_parts[-1]

        # If both parts start with uppercase and are reasonable length, it's likely a person
        if (len(first) >= 2 and len(last) >= 2 and
            first[0].isupper() and last[0].isupper() and
            first.lower() not in ["the", "a", "an"]):
            # This looks like a person name - allow it even if surname matches company
            # Only reject if the entire name IS the company
            pass
        else:
            # Doesn't look like a person name, continue with company matching
            pass

    # Normalize names for comparison
    def normalize(s):
        for suffix in [" inc", " llc", " corp", " co", ".", "'s", "'", "-"]:
            s = s.replace(suffix, "")
        return s.strip()

    contact_norm = normalize(contact_lower)
    company_norm = normalize(company_lower)

    # Direct match - contact name is exactly the company name
    if contact_norm == company_norm:
        return True, "Contact name matches company name exactly"

    # Check if contact name has person-like structure (2+ words with first being a likely first name)
    contact_words = contact_norm.split()
    if len(contact_words) >= 2:
        # Common first names indicator - if first word is short and second is longer, likely a name
        first_word = contact_words[0]
        # Skip this check for now - rely on LLM for nuanced cases
        return False, ""

    # Single word contact that matches company
    if len(contact_words) == 1:
        company_words = company_norm.split()
        if contact_words[0] in company_words:
            return True, "Single-word contact matches company name word"

    return False, ""

# Known franchise/corporate chains (should look for local operator)
KNOWN_FRANCHISES = [
    "starbucks", "dunkin", "mcdonald", "subway", "taco bell",
    "burger king", "wendy", "chick-fil-a", "popeyes", "kfc",
    "pizza hut", "domino", "papa john", "little caesar",
    "7-eleven", "cvs", "walgreens", "ace hardware",
    "jiffy lube", "midas", "pep boys", "firestone",
    "holiday inn", "marriott", "hilton", "best western",
]


class IncrementalValidator:
    """
    Quick validation checks for contact candidates.

    Use BEFORE adding candidates to the pool to catch obvious garbage.
    Much faster and cheaper than full LLM validation.

    Checks:
    1. Instant reject patterns (no LLM needed)
    2. Name plausibility (is this a real person name?)
    3. Company type detection (SMB vs franchise vs corporate)
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4o-mini"
    ):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.llm: OpenAIProvider | None = None
        self.model = model

        if self.api_key:
            try:
                self.llm = OpenAIProvider(
                    api_key=self.api_key,
                    model=model,
                    default_temperature=0.0,
                    default_max_tokens=150
                )
            except Exception as e:
                logger.warning(f"Failed to initialize LLM: {e}")

    def instant_reject_check(self, name: str) -> tuple[bool, str]:
        """
        Check if name matches known invalid patterns.
        No LLM needed - instant rejection.

        Args:
            name: Name to check

        Returns:
            (should_reject, reason)
        """
        if not name:
            return True, "Empty name"

        name_lower = name.lower()

        # Check instant reject patterns
        for pattern in INSTANT_REJECT_PATTERNS:
            if pattern in name_lower:
                return True, f"Matches reject pattern: '{pattern}'"

        # Check if too short (single word or very short)
        parts = name.split()
        if len(parts) < 2:
            return True, "Name has fewer than 2 parts"

        if any(len(p) < 2 for p in parts):
            return True, "Name contains very short parts"

        # Check if all caps (likely acronym or organization)
        if name.isupper() and len(name) > 5:
            return True, "All uppercase - likely organization"

        # Check for numbers in name
        if any(c.isdigit() for c in name):
            return True, "Contains numbers"

        return False, ""

    def is_known_franchise(self, company_name: str) -> bool:
        """Check if company is a known franchise chain"""
        company_lower = company_name.lower()
        return any(f in company_lower for f in KNOWN_FRANCHISES)

    async def quick_validate(
        self,
        name: str,
        company_name: str,
        context: str | None = None
    ) -> QuickValidationResult:
        """
        Quick validation check for a candidate name.

        Args:
            name: Candidate name to validate
            company_name: Company name for context
            context: Optional source snippet

        Returns:
            QuickValidationResult with plausibility and red flags
        """
        # Step 1: Instant reject check (no LLM)
        should_reject, reason = self.instant_reject_check(name)
        if should_reject:
            return QuickValidationResult(
                is_plausible=False,
                confidence=100.0,
                red_flags=[reason],
                reasoning=f"Instant reject: {reason}"
            )

        # Step 2: LLM plausibility check (if available)
        if self.llm:
            return await self._llm_validate(name, company_name, context)

        # Fallback: assume valid if passes instant checks
        return QuickValidationResult(
            is_plausible=True,
            confidence=60.0,
            reasoning="Passed instant checks, LLM not available"
        )

    async def _llm_validate(
        self,
        name: str,
        company_name: str,
        context: str | None
    ) -> QuickValidationResult:
        """LLM-based validation check"""
        prompt = f"""Quick check: Is "{name}" a plausible person name for the owner/operator of "{company_name}"?

Context: {context[:200] if context else 'None'}

Check for:
1. Is this a real person name (first + last)?
2. Is it an organization, phrase, or title fragment?
3. Any red flags (deceased, former, historical)?

Reply JSON: {{"is_plausible": true/false, "confidence": 0-100, "red_flags": [], "reasoning": "brief explanation"}}"""

        try:
            result = await self.llm.complete_json(
                prompt=prompt,
                system="You quickly validate if text is a real person name. Be strict - reject anything suspicious.",
                temperature=0.0,
                max_tokens=150
            )

            return QuickValidationResult(
                is_plausible=result.get("is_plausible", False),
                confidence=float(result.get("confidence", 0)),
                red_flags=result.get("red_flags", []),
                reasoning=result.get("reasoning", "")
            )

        except Exception as e:
            logger.error(f"LLM validation failed: {e}")
            return QuickValidationResult(
                is_plausible=True,  # Don't reject on LLM failure
                confidence=50.0,
                reasoning=f"LLM failed: {e}"
            )

    async def validate_batch(
        self,
        candidates: list[dict],
        company_name: str
    ) -> list[tuple[dict, QuickValidationResult]]:
        """
        Validate multiple candidates.

        Args:
            candidates: List of candidate dicts with 'name' key
            company_name: Company name for context

        Returns:
            List of (candidate, validation_result) tuples
        """
        results = []
        for c in candidates:
            name = c.get("name")
            context = c.get("source_snippet") or c.get("snippet")

            result = await self.quick_validate(name, company_name, context)
            results.append((c, result))

        return results

    def filter_valid_candidates(
        self,
        candidates: list[dict],
        validations: list[tuple[dict, QuickValidationResult]],
        min_confidence: float = 50.0
    ) -> list[dict]:
        """
        Filter candidates to only those passing validation.

        Args:
            candidates: Original candidate list
            validations: Validation results from validate_batch
            min_confidence: Minimum confidence to pass

        Returns:
            Filtered list of valid candidates
        """
        valid = []
        for c, v in validations:
            if v.is_plausible and v.confidence >= min_confidence:
                # Add validation info to candidate
                c["validation_confidence"] = v.confidence
                c["validation_reasoning"] = v.reasoning
                valid.append(c)
            else:
                logger.debug(f"Rejected candidate '{c.get('name')}': {v.reasoning}")

        return valid


# Convenience functions
async def quick_validate_name(
    name: str,
    company_name: str,
    context: str | None = None,
    api_key: str | None = None
) -> QuickValidationResult:
    """Convenience function for quick validation"""
    validator = IncrementalValidator(api_key=api_key)
    return await validator.quick_validate(name, company_name, context)


def instant_reject(name: str) -> tuple[bool, str]:
    """Convenience function for instant reject check (no LLM)"""
    validator = IncrementalValidator()
    return validator.instant_reject_check(name)


# Test
async def test_validator():
    """Test the validator"""
    validator = IncrementalValidator()

    test_cases = [
        ("John Smith", "Joe's Plumbing"),
        ("Passes Away", "Dunkin' Phoenix"),  # Should reject
        ("Report Project", "West Pavilion"),  # Should reject
        ("Senior Vice", "Tractor Supply"),  # Should reject
        ("ACVIM Forum", "Vet Specialty"),  # Should reject
        ("Rotary Club", "Crossroads Care"),  # Should reject
        ("Mike Johnson", "Starbucks Downtown"),
        ("", "Empty Test"),  # Should reject
    ]

    print("Testing Incremental Validator\n" + "=" * 50)

    for name, company in test_cases:
        # First check instant reject
        reject, reason = validator.instant_reject_check(name)

        if reject:
            print(f"\n[INSTANT REJECT] '{name}'")
            print(f"  Reason: {reason}")
        else:
            # Full validation
            result = await validator.quick_validate(name, company)
            status = "PASS" if result.is_plausible else "REJECT"
            print(f"\n[{status}] '{name}' @ {company}")
            print(f"  Confidence: {result.confidence:.0f}%")
            print(f"  Reasoning: {result.reasoning}")
            if result.red_flags:
                print(f"  Red flags: {result.red_flags}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_validator())
