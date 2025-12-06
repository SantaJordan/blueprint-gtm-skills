"""
LLM-based Owner Extraction

Replaces brittle regex extraction with GPT-4o-mini structured output.
Designed to eliminate parsing errors like "Passes Away", "Report Project".
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Any

from ..llm.openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)


@dataclass
class OwnerCandidate:
    """Extracted owner candidate from search snippets"""
    name: str | None = None
    title: str | None = None
    confidence: float = 0.0  # 0-100
    source_snippet: str | None = None
    source_url: str | None = None
    reasoning: str | None = None
    red_flags: list[str] = field(default_factory=list)
    is_current: bool = True  # False if detected as former/deceased
    company_type: str | None = None  # "smb", "franchise", "corporate"


@dataclass
class ExtractionResult:
    """Result of owner extraction"""
    candidates: list[OwnerCandidate] = field(default_factory=list)
    best_candidate: OwnerCandidate | None = None
    company_type: str | None = None  # "smb", "franchise", "corporate"
    extraction_notes: str | None = None


# Output schema for GPT-4o-mini
EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "company_type": {
            "type": "string",
            "enum": ["smb", "franchise", "corporate"],
            "description": "Type of business: smb (local independent), franchise (chain location), corporate (large company)"
        },
        "candidates": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Full name (first + last) of the owner/operator"},
                    "title": {"type": "string", "description": "Title (Owner, President, CEO, Manager, etc.)"},
                    "confidence": {"type": "number", "description": "0-100 confidence this is the current owner"},
                    "reasoning": {"type": "string", "description": "Why you extracted this name"},
                    "red_flags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Any concerns (deceased, former, outdated, etc.)"
                    },
                    "is_current": {"type": "boolean", "description": "True if currently at company, false if former/deceased"}
                },
                "required": ["name", "title", "confidence", "reasoning", "is_current"]
            }
        },
        "extraction_notes": {
            "type": "string",
            "description": "Any notes about the extraction (e.g., 'No clear owner found', 'Multiple candidates')"
        }
    },
    "required": ["company_type", "candidates", "extraction_notes"]
}


EXTRACTION_SYSTEM_PROMPT = """You are an expert at extracting business owner information from search results.

Your task: Extract the CURRENT owner, founder, or primary decision-maker from search snippets.

CRITICAL RULES:
1. Only extract REAL PERSON NAMES (first + last name required)
2. NEVER extract:
   - Organization names (e.g., "Rotary Club", "ACVIM Forum")
   - Partial phrases (e.g., "Passes Away", "Report Project", "Senior Vice")
   - Titles without names (e.g., "CEO", "President")
   - Historical figures not currently at the company
3. Check for RECENCY:
   - Prefer names mentioned with 2024/2025 dates
   - Flag former employees, deceased persons, or outdated references
4. Detect COMPANY TYPE:
   - "smb": Independent local business (Joe's Plumbing, Main Street Bakery)
   - "franchise": Chain location (Starbucks, Dunkin', McDonald's) - look for local franchisee/operator
   - "corporate": Large corporation (Apple, Microsoft) - may not have single "owner"

For FRANCHISE businesses (Starbucks, Dunkin', etc.):
- The "owner" is the local franchisee or operator, NOT the corporate CEO
- Search for "franchisee", "operator", "owner of this location"

Return structured JSON with candidates and confidence scores."""


class LLMOwnerExtractor:
    """
    Extract owner names from search snippets using GPT-4o-mini.

    Replaces regex-based extraction which produced garbage like "Passes Away".
    Cost: ~$0.001 per extraction (similar to one Serper query)
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
                    default_temperature=0.1,
                    default_max_tokens=800
                )
            except Exception as e:
                logger.warning(f"Failed to initialize LLM: {e}")

    async def extract_owner(
        self,
        company_name: str,
        snippets: list[dict],  # [{text, url, source}]
        city: str | None = None,
        state: str | None = None,
        industry: str | None = None
    ) -> ExtractionResult:
        """
        Extract owner from search snippets using LLM.

        Args:
            company_name: Name of the company
            snippets: List of search result snippets [{text, url, source}]
            city: Optional city for context
            state: Optional state for context
            industry: Optional industry/vertical

        Returns:
            ExtractionResult with candidates and best match
        """
        if not self.llm:
            logger.warning("LLM not initialized, returning empty result")
            return ExtractionResult()

        if not snippets:
            return ExtractionResult(extraction_notes="No snippets provided")

        # Build prompt with snippets
        location = f"{city}, {state}" if city and state else ""

        snippet_text = ""
        for i, s in enumerate(snippets[:10], 1):  # Limit to 10 snippets
            text = s.get("text", s.get("snippet", ""))
            url = s.get("url", s.get("link", ""))
            source = s.get("source", "unknown")
            snippet_text += f"\n[{i}] Source: {source}\nURL: {url}\nText: {text}\n"

        prompt = f"""Company: {company_name}
Location: {location or "Unknown"}
Industry: {industry or "Unknown"}

Search Results:
{snippet_text}

Extract the CURRENT owner/founder/operator of this business.
If this is a franchise (Starbucks, Dunkin', etc.), look for the LOCAL franchisee/operator.
Return JSON with company_type, candidates, and extraction_notes."""

        try:
            result = await self.llm.complete_json(
                prompt=prompt,
                schema=EXTRACTION_SCHEMA,
                system=EXTRACTION_SYSTEM_PROMPT,
                temperature=0.1,
                max_tokens=800
            )

            return self._parse_result(result, snippets)

        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return ExtractionResult(extraction_notes=f"Extraction failed: {e}")

    def _parse_result(self, result: dict, snippets: list[dict]) -> ExtractionResult:
        """Parse LLM response into ExtractionResult"""
        extraction = ExtractionResult(
            company_type=result.get("company_type"),
            extraction_notes=result.get("extraction_notes")
        )

        candidates_data = result.get("candidates", [])

        for c in candidates_data:
            name = c.get("name")

            # Skip if no name or clearly invalid
            if not name or len(name.split()) < 2:
                continue

            candidate = OwnerCandidate(
                name=name,
                title=c.get("title", "Owner"),
                confidence=float(c.get("confidence", 0)),
                reasoning=c.get("reasoning"),
                red_flags=c.get("red_flags", []),
                is_current=c.get("is_current", True),
                company_type=extraction.company_type
            )

            # Find source snippet
            for s in snippets:
                text = s.get("text", s.get("snippet", ""))
                if name.split()[0] in text or name.split()[-1] in text:
                    candidate.source_snippet = text[:200]
                    candidate.source_url = s.get("url", s.get("link"))
                    break

            extraction.candidates.append(candidate)

        # Pick best candidate (highest confidence, current, no red flags)
        current_candidates = [
            c for c in extraction.candidates
            if c.is_current and not c.red_flags
        ]

        if current_candidates:
            extraction.best_candidate = max(current_candidates, key=lambda x: x.confidence)
        elif extraction.candidates:
            # Fall back to best overall
            extraction.best_candidate = max(extraction.candidates, key=lambda x: x.confidence)

        return extraction

    async def validate_name_is_real(self, name: str) -> tuple[bool, str]:
        """
        Quick check if a name looks like a real person name.

        Args:
            name: Name to validate

        Returns:
            (is_valid, reason)
        """
        if not self.llm:
            return True, "LLM not available, assuming valid"

        prompt = f"""Is "{name}" a valid person name?

Rules:
- Must be a real first + last name
- Cannot be an organization name
- Cannot be a phrase or sentence fragment
- Cannot be a title without a name

Reply with JSON: {{"is_valid": true/false, "reason": "explanation"}}"""

        try:
            result = await self.llm.complete_json(
                prompt=prompt,
                system="You validate whether text is a real person name.",
                temperature=0.0,
                max_tokens=100
            )

            return result.get("is_valid", False), result.get("reason", "")

        except Exception as e:
            logger.error(f"Name validation failed: {e}")
            return True, f"Validation failed: {e}"

    async def verify_current_role(
        self,
        name: str,
        company: str,
        snippets: list[dict]
    ) -> tuple[bool, float, str]:
        """
        Verify that a person is currently at the company.

        Args:
            name: Person's name
            company: Company name
            snippets: Recent search snippets about this person + company

        Returns:
            (is_current, confidence, reasoning)
        """
        if not self.llm:
            return True, 50.0, "LLM not available"

        snippet_text = "\n".join([
            s.get("text", s.get("snippet", ""))[:200]
            for s in snippets[:5]
        ])

        prompt = f"""Is {name} CURRENTLY working at {company}?

Recent search results:
{snippet_text}

Look for:
- Recent dates (2024, 2025) confirming current role
- "Former", "previously", "left", "departed" indicating past role
- Obituaries or "passed away" indicating deceased

Reply with JSON: {{"is_current": true/false, "confidence": 0-100, "reasoning": "explanation"}}"""

        try:
            result = await self.llm.complete_json(
                prompt=prompt,
                system="You verify whether someone currently works at a company.",
                temperature=0.0,
                max_tokens=200
            )

            return (
                result.get("is_current", True),
                float(result.get("confidence", 50)),
                result.get("reasoning", "")
            )

        except Exception as e:
            logger.error(f"Role verification failed: {e}")
            return True, 50.0, f"Verification failed: {e}"


# Convenience function
async def extract_owner_from_snippets(
    company_name: str,
    snippets: list[dict],
    api_key: str | None = None,
    **kwargs
) -> ExtractionResult:
    """
    Convenience function to extract owner from snippets.

    Args:
        company_name: Company name
        snippets: Search result snippets
        api_key: Optional OpenAI API key
        **kwargs: Additional args passed to extract_owner

    Returns:
        ExtractionResult
    """
    extractor = LLMOwnerExtractor(api_key=api_key)
    return await extractor.extract_owner(company_name, snippets, **kwargs)


# Test
async def test_extractor():
    """Test the extractor"""
    extractor = LLMOwnerExtractor()

    # Test case 1: Clear owner
    snippets = [
        {
            "text": "John Smith, owner of Joe's Plumbing in Phoenix, has been serving the community for 20 years.",
            "url": "https://phoenixbiz.com/joesplumbing",
            "source": "news"
        }
    ]

    result = await extractor.extract_owner("Joe's Plumbing", snippets, city="Phoenix", state="AZ")
    print(f"Test 1 - Clear owner:")
    print(f"  Best: {result.best_candidate.name if result.best_candidate else None}")
    print(f"  Confidence: {result.best_candidate.confidence if result.best_candidate else 0}")

    # Test case 2: Garbage that should be rejected
    snippets = [
        {
            "text": "Dunkin' owner passes away after long illness. Memorial service to be held.",
            "url": "https://news.com/obituary",
            "source": "news"
        }
    ]

    result = await extractor.extract_owner("Dunkin' Phoenix", snippets, city="Phoenix", state="AZ")
    print(f"\nTest 2 - Obituary (should reject 'Passes Away'):")
    print(f"  Best: {result.best_candidate.name if result.best_candidate else 'None - Correctly rejected'}")
    print(f"  Notes: {result.extraction_notes}")

    # Test case 3: Franchise
    snippets = [
        {
            "text": "Mike Johnson operates the Starbucks franchise on Main Street. The location opened in 2019.",
            "url": "https://localnews.com/starbucks",
            "source": "news"
        }
    ]

    result = await extractor.extract_owner("Starbucks Main Street", snippets, city="Denver", state="CO")
    print(f"\nTest 3 - Franchise operator:")
    print(f"  Company type: {result.company_type}")
    print(f"  Best: {result.best_candidate.name if result.best_candidate else None}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_extractor())
