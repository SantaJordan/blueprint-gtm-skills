"""
Contact Judge - LLM-based validation of contacts
Final QA layer that validates contacts with reasoning
"""

import json
from dataclasses import dataclass
from typing import Any

from ..llm.provider import LLMProvider


@dataclass
class ContactJudgment:
    """Result of contact validation by LLM judge"""
    accept: bool
    overall_confidence: float
    email_confidence: float
    person_match_confidence: float
    linkedin_confidence: float
    reasoning: str
    red_flags: list[str]
    raw_response: dict


CONTACT_JUDGE_SYSTEM = """You are a B2B contact validator for SMB (Small & Medium Business) sales outreach.

PRIMARY GOAL: Find a real PERSON NAME (first + last name) who is the owner/decision-maker.
SECONDARY GOAL: Find LinkedIn URL if available.
TERTIARY: Email and phone are nice-to-have, NOT required.

CRITICAL RULES:
1. NEVER invent or guess information - only use what's explicitly provided
2. If person appears to be ex-employee (past tense, "former", "previous", dates ended), reject
3. REJECT if name looks like a company name (contains LLC, Inc, Corp, Services, etc.)
4. Missing email is NOT a red flag for SMBs - many small business owners don't publish emails
5. Missing phone is NOT a red flag for SMBs - we're finding people, not contact methods
6. Missing LinkedIn is NOT a red flag - most SMB owners don't have LinkedIn profiles

SMB-SPECIFIC SIGNALS (these are STRONG evidence for small businesses):
- Google Maps listing with owner name = HIGH confidence (small businesses list owners)
- Owner/Founder/Proprietor/CEO title = HIGH confidence for SMBs
- Name found on company website contact/about page = GOOD evidence
- Full name (first + last) = GOOD evidence
- Facebook profile for SMB owner = GOOD evidence (SMB owners use Facebook, not LinkedIn)

CONFIDENCE SCORING GUIDELINES FOR SMB:
- 70-100: Strong match - owner/founder name from Google Maps or website, even without email
- 50-69: Good match - name + owner title from any reliable source (Serper, website scrape)
- 30-49: Weak match - name found but no owner title, or ambiguous evidence
- 0-29: No match, company name instead of person, or clear disqualifiers

DECISION RULE: Set accept=true if overall_confidence >= 50, otherwise set accept=false.

DO NOT add red_flags for: missing email, missing phone, missing LinkedIn.
ONLY add red_flags for: company name as person, ex-employee indicators, contradictory evidence.

You must respond with valid JSON only."""


CONTACT_JUDGE_PROMPT = """Validate this contact for B2B sales outreach.

COMPANY:
- Name: {company_name}
- Domain: {domain}
- Domain Confidence: {domain_confidence}
- Industry: {industry}
- Location: {location}

CANDIDATE CONTACT:
- Name: {name}
- Title: {title}
- Email: {email}
- Email Source: {email_source}
- Email Verified: {email_verified}
- Is Catch-All: {is_catch_all}
- LinkedIn URL: {linkedin_url}
- Phone: {phone}

EVIDENCE:
{evidence}

TARGET TITLES:
{target_titles}

Based on the above, provide your judgment in this exact JSON format:
{{
  "accept": boolean,
  "overall_confidence": 0-100,
  "email_confidence": 0-100,
  "person_match_confidence": 0-100,
  "linkedin_confidence": 0-100,
  "reasoning": "one sentence explanation with evidence citations",
  "red_flags": ["list of concerns if any"]
}}"""


class ContactJudge:
    """LLM-based contact validation"""

    def __init__(self, llm_provider: LLMProvider):
        """
        Initialize contact judge.

        Args:
            llm_provider: LLM provider for validation
        """
        self.llm = llm_provider

    async def validate_contact(
        self,
        company_name: str,
        domain: str,
        domain_confidence: float,
        contact_name: str | None,
        contact_title: str | None,
        contact_email: str | None,
        email_source: str | None,
        email_verified: bool | None,
        is_catch_all: bool | None,
        linkedin_url: str | None,
        phone: str | None,
        evidence: str | None,
        target_titles: list[str] | None = None,
        industry: str | None = None,
        location: str | None = None
    ) -> ContactJudgment:
        """
        Validate a contact using LLM judge.

        Args:
            company_name: Company name
            domain: Company domain
            domain_confidence: Confidence in domain match (0-100)
            contact_name: Contact's full name
            contact_title: Contact's job title
            contact_email: Contact's email address
            email_source: Where email came from (site_observed, enriched, pattern_guess)
            email_verified: Whether email was verified deliverable
            is_catch_all: Whether domain is catch-all
            linkedin_url: Contact's LinkedIn URL
            phone: Contact's phone number
            evidence: Evidence bundle (text snippets, sources)
            target_titles: Target job titles we're looking for
            industry: Company industry
            location: Company location

        Returns:
            ContactJudgment with validation results
        """
        # Build prompt
        prompt = CONTACT_JUDGE_PROMPT.format(
            company_name=company_name or "Unknown",
            domain=domain or "Unknown",
            domain_confidence=domain_confidence or 0,
            industry=industry or "Unknown",
            location=location or "Unknown",
            name=contact_name or "Unknown",
            title=contact_title or "Unknown",
            email=contact_email or "None",
            email_source=email_source or "Unknown",
            email_verified="Yes" if email_verified else ("No" if email_verified is False else "Not checked"),
            is_catch_all="Yes" if is_catch_all else ("No" if is_catch_all is False else "Unknown"),
            linkedin_url=linkedin_url or "None",
            phone=phone or "None",
            evidence=evidence or "No additional evidence provided",
            target_titles=", ".join(target_titles) if target_titles else "Owner, Manager, Director"
        )

        try:
            result = await self.llm.complete_json(
                prompt=prompt,
                system=CONTACT_JUDGE_SYSTEM,
                temperature=0.1,
                max_tokens=500
            )

            return ContactJudgment(
                accept=result.get("accept", False),
                overall_confidence=float(result.get("overall_confidence", 0)),
                email_confidence=float(result.get("email_confidence", 0)),
                person_match_confidence=float(result.get("person_match_confidence", 0)),
                linkedin_confidence=float(result.get("linkedin_confidence", 0)),
                reasoning=result.get("reasoning", "No reasoning provided"),
                red_flags=result.get("red_flags", []),
                raw_response=result
            )

        except Exception as e:
            # Return a conservative judgment on error
            return ContactJudgment(
                accept=False,
                overall_confidence=0,
                email_confidence=0,
                person_match_confidence=0,
                linkedin_confidence=0,
                reasoning=f"Validation error: {str(e)}",
                red_flags=["LLM validation failed"],
                raw_response={"error": str(e)}
            )

    async def batch_validate(
        self,
        contacts: list[dict],
        company_info: dict
    ) -> list[ContactJudgment]:
        """
        Validate multiple contacts for the same company.

        Args:
            contacts: List of contact dicts with name, title, email, etc.
            company_info: Dict with company_name, domain, domain_confidence, etc.

        Returns:
            List of ContactJudgment results
        """
        results = []

        for contact in contacts:
            judgment = await self.validate_contact(
                company_name=company_info.get("company_name"),
                domain=company_info.get("domain"),
                domain_confidence=company_info.get("domain_confidence", 0),
                contact_name=contact.get("name"),
                contact_title=contact.get("title"),
                contact_email=contact.get("email"),
                email_source=contact.get("email_source"),
                email_verified=contact.get("email_verified"),
                is_catch_all=contact.get("is_catch_all"),
                linkedin_url=contact.get("linkedin_url"),
                phone=contact.get("phone"),
                evidence=contact.get("evidence"),
                target_titles=company_info.get("target_titles"),
                industry=company_info.get("industry"),
                location=company_info.get("location")
            )
            results.append(judgment)

        return results


def create_evidence_bundle(
    sources: list[dict]
) -> str:
    """
    Create an evidence bundle string from multiple sources.

    Args:
        sources: List of dicts with 'source', 'url', and 'content' keys

    Returns:
        Formatted evidence string
    """
    if not sources:
        return "No evidence collected"

    lines = []
    for i, source in enumerate(sources, 1):
        source_type = source.get("source", "unknown")
        url = source.get("url", "")
        content = source.get("content", "")  # Full content - no truncation

        lines.append(f"[{i}] Source: {source_type}")
        if url:
            lines.append(f"    URL: {url}")
        if content:
            lines.append(f"    Content: {content}")
        lines.append("")

    return "\n".join(lines)
