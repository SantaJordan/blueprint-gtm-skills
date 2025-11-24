"""
LLM Judge module using local Ollama
Uses lightweight models (7B-14B) for fast inference
"""
import httpx
import json
import logging
from typing import Dict, Any, Optional
import re

logger = logging.getLogger(__name__)


class OllamaJudge:
    """Client for local Ollama LLM to judge domain matches"""

    def __init__(self, endpoint: str = "http://localhost:11434/api/generate",
                 model: str = "qwen2.5:14b", timeout: int = 30):
        """
        Initialize Ollama client

        Args:
            endpoint: Ollama API endpoint
            model: Model name (qwen2.5:14b, qwen2.5:7b, llama3.2:3b, etc.)
            timeout: Request timeout in seconds
        """
        self.endpoint = endpoint
        self.model = model
        self.timeout = timeout

    async def judge_match(self, company_data: Dict[str, Any],
                         url: str, webpage_text: str) -> Dict[str, Any]:
        """
        Use LLM to judge if webpage matches company

        Args:
            company_data: Dict with name, city, phone, address, etc.
            url: Candidate URL
            webpage_text: Extracted webpage text (from Trafilatura)

        Returns:
            {
                'match': bool,
                'confidence': int,  # 0-100
                'evidence': str,
                'reasoning': str
            }
        """
        # Use full text for better validation (Ollama can handle larger context)
        # Most contact info is in first 10000 chars, which is well within model limits
        truncated_text = webpage_text[:10000]

        # Build structured prompt
        prompt = self._build_prompt(company_data, url, truncated_text)

        try:
            # Call Ollama API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.endpoint,
                    json={
                        'model': self.model,
                        'prompt': prompt,
                        'stream': False,
                        'format': 'json',
                        'options': {
                            'temperature': 0.1,  # Low temperature for consistent output
                            'num_predict': 256   # Limit response length
                        }
                    },
                    timeout=self.timeout
                )

                if response.status_code != 200:
                    logger.error(f"Ollama API error: {response.status_code}")
                    return self._fallback_response()

                result = response.json()
                llm_response = result.get('response', '{}')

                # Parse JSON response
                parsed = self._parse_llm_response(llm_response)

                logger.debug(f"LLM judgment: {parsed}")

                return parsed

        except httpx.TimeoutException:
            logger.error(f"Ollama timeout for {company_data.get('name')}")
            return self._fallback_response()
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return self._fallback_response()

    def _build_prompt(self, company_data: Dict[str, Any], url: str, text: str) -> str:
        """Build structured prompt for LLM"""

        company_name = company_data.get('name', 'Unknown')
        city = company_data.get('city', '')
        phone = company_data.get('phone', '')
        address = company_data.get('address', '')
        context = company_data.get('context', '')

        prompt = f"""You are verifying if a website belongs to a specific company or facility.

**Company Information:**
- Name: {company_name}
- City: {city if city else 'Unknown'}
- Phone: {phone if phone else 'Unknown'}
- Address: {address if address else 'Unknown'}
- Context: {context if context else 'N/A'}

**Website URL:** {url}

**Website Content:**
{text}

**Task:**
Determine if this website belongs to the specified company/facility, or if it's a parent company or directory site.

**CRITICAL - Check for these red flags:**
1. **Directory/Listing Site** - Sites like Medicare.gov, US News, Caring.com that list/rank multiple facilities
2. **Parent Company** - Corporate sites managing multiple locations (look for "Our Locations", "Find a Facility", multiple addresses)
3. **Healthcare Associations** - Industry organizations (AHCA, LeadingAge, etc.) vs actual facilities

**Validation Checks:**
1. **Phone number match** - Does the website show the company's phone number (exact or last 4-7 digits)?
2. **Single Location** - Does the site represent ONE facility or MULTIPLE facilities?
3. **Address/City match** - Does the website mention THIS specific city/address (not a list of cities)?
4. **Company name match** - Does the site prominently display THIS company name?
5. **Context match** - Does the content align with the company's industry?

**Return ONLY valid JSON:**
{{
  "match": true or false,
  "confidence": 0-100,
  "evidence": "brief explanation of matching or non-matching signals",
  "phone_found": true or false,
  "address_found": true or false,
  "name_found": true or false,
  "is_parent_company": true or false,
  "is_directory_site": true or false
}}

**Examples:**
- Single facility match: {{"match": true, "confidence": 95, "evidence": "Phone (xxx) xxx-1234 matches, single location in Boston", "is_parent_company": false, "is_directory_site": false}}
- Parent company: {{"match": true, "confidence": 70, "evidence": "Correct company but corporate site with 50+ locations listed", "is_parent_company": true, "is_directory_site": false}}
- Directory site: {{"match": false, "confidence": 10, "evidence": "Medicare.gov directory listing, not facility website", "is_parent_company": false, "is_directory_site": true}}
- No match: {{"match": false, "confidence": 5, "evidence": "Wrong company name, different city, no matching contact info", "is_parent_company": false, "is_directory_site": false}}

Respond with JSON only, no additional text:"""

        return prompt

    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM JSON response"""

        try:
            # Try direct JSON parse
            parsed = json.loads(response_text)

            # Validate required fields
            if 'match' in parsed and 'confidence' in parsed:
                return {
                    'match': bool(parsed.get('match', False)),
                    'confidence': int(parsed.get('confidence', 0)),
                    'evidence': str(parsed.get('evidence', '')),
                    'reasoning': str(parsed.get('evidence', '')),  # Alias
                    'phone_found': parsed.get('phone_found', False),
                    'address_found': parsed.get('address_found', False),
                    'name_found': parsed.get('name_found', False),
                    'is_parent_company': parsed.get('is_parent_company', False),
                    'is_directory_site': parsed.get('is_directory_site', False)
                }

        except json.JSONDecodeError:
            logger.warning(f"Failed to parse LLM JSON: {response_text[:200]}")

        # Fallback: try to extract values using regex
        return self._extract_with_regex(response_text)

    def _extract_with_regex(self, text: str) -> Dict[str, Any]:
        """Extract values from malformed JSON using regex"""

        # Try to find match: true/false
        match_search = re.search(r'"match"\s*:\s*(true|false)', text, re.IGNORECASE)
        match = match_search.group(1).lower() == 'true' if match_search else False

        # Try to find confidence: 0-100
        confidence_search = re.search(r'"confidence"\s*:\s*(\d+)', text)
        confidence = int(confidence_search.group(1)) if confidence_search else 50

        # Try to find evidence
        evidence_search = re.search(r'"evidence"\s*:\s*"([^"]+)"', text)
        evidence = evidence_search.group(1) if evidence_search else "Unable to parse LLM response"

        return {
            'match': match,
            'confidence': min(max(confidence, 0), 100),  # Clamp 0-100
            'evidence': evidence,
            'reasoning': evidence,
            'phone_found': False,
            'address_found': False,
            'name_found': False,
            'is_parent_company': False,
            'is_directory_site': False
        }

    def _fallback_response(self) -> Dict[str, Any]:
        """Return fallback response on error"""
        return {
            'match': False,
            'confidence': 0,
            'evidence': 'LLM call failed',
            'reasoning': 'LLM unavailable or error',
            'phone_found': False,
            'address_found': False,
            'name_found': False,
            'is_parent_company': False,
            'is_directory_site': False
        }


async def verify_with_llm(company_data: Dict[str, Any], url: str,
                         webpage_text: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to verify a domain match using LLM

    Args:
        company_data: Company information
        url: Candidate URL
        webpage_text: Webpage text content
        config: Configuration dict

    Returns:
        LLM judgment result
    """
    llm_config = config.get('llm', {})

    judge = OllamaJudge(
        endpoint=llm_config.get('endpoint', 'http://localhost:11434/api/generate'),
        model=llm_config.get('model', 'qwen2.5:14b'),
        timeout=llm_config.get('timeout', 30)
    )

    result = await judge.judge_match(company_data, url, webpage_text)

    return result


# =============================================================================
# V2 UNIVERSAL VALIDATION
# =============================================================================

async def universal_validate(company_data: Dict[str, Any],
                             domain: str,
                             scrape_result: Optional[Dict[str, Any]],
                             config: Dict[str, Any]) -> Dict[str, Any]:
    """
    V2 Universal validation combining scraper signals + LLM judgment

    This is the enhanced validation that ALWAYS runs for V2 system.
    It combines:
    1. Automated validation signals from scraper (phone, email, name extraction)
    2. LLM judgment for deeper analysis
    3. Confidence boosting based on multiple signals

    Args:
        company_data: Expected company data
        domain: Candidate domain
        scrape_result: Result from scrape_and_validate() (enhanced scraper)
        config: Configuration dict

    Returns:
        {
            'validated': bool,           # Is this domain valid?
            'confidence': int,            # 0-100 confidence score
            'evidence': str,              # Human-readable explanation
            'signals': {                  # Individual validation signals
                'phone_match': bool,
                'name_similarity': float,
                'llm_match': bool,
                'llm_confidence': int
            },
            'method': str                 # 'automated', 'llm', or 'hybrid'
        }
    """
    if not scrape_result:
        return {
            'validated': False,
            'confidence': 0,
            'evidence': 'Failed to scrape domain',
            'signals': {},
            'method': 'none'
        }

    validation_data = scrape_result.get('validation', {})
    webpage_text = scrape_result.get('text', '')

    # Extract automated signals
    phone_match = validation_data.get('phone_match', False)
    name_similarity = validation_data.get('name_similarity', 0.0)
    extracted_name = validation_data.get('company_name', '')
    extracted_phones = validation_data.get('phone_numbers', [])
    extracted_emails = validation_data.get('emails', [])

    # High-confidence automated validation (no LLM needed)
    if phone_match and name_similarity >= 70:
        logger.info(f"✓ Auto-validated {domain}: phone match + name similarity {name_similarity:.1f}")
        return {
            'validated': True,
            'confidence': 95,
            'evidence': f"Phone verification passed + company name match ({name_similarity:.1f}% similar)",
            'signals': {
                'phone_match': True,
                'name_similarity': name_similarity,
                'llm_match': None,
                'llm_confidence': None
            },
            'method': 'automated'
        }

    # Medium-confidence automated validation
    if phone_match or name_similarity >= 85:
        confidence = 85 if phone_match else int(name_similarity)
        logger.info(f"✓ Auto-validated {domain}: {'phone match' if phone_match else f'name similarity {name_similarity:.1f}'}")
        return {
            'validated': True,
            'confidence': confidence,
            'evidence': f"{'Phone verification passed' if phone_match else f'Company name match ({name_similarity:.1f}% similar)'}",
            'signals': {
                'phone_match': phone_match,
                'name_similarity': name_similarity,
                'llm_match': None,
                'llm_confidence': None
            },
            'method': 'automated'
        }

    # Low/no automated signals → Use LLM for deeper analysis
    logger.info(f"→ Using LLM validation for {domain} (auto signals insufficient)")

    llm_result = await verify_with_llm(company_data, domain, webpage_text, config)

    llm_match = llm_result.get('match', False)
    llm_confidence = llm_result.get('confidence', 0)
    llm_evidence = llm_result.get('evidence', '')

    # Hybrid scoring: Boost LLM confidence if automated signals present
    final_confidence = llm_confidence
    if name_similarity >= 60:
        final_confidence = min(100, llm_confidence + 10)  # +10 boost for name similarity
    if extracted_phones:
        final_confidence = min(100, final_confidence + 5)  # +5 for having contact info

    validated = llm_match and final_confidence >= 60

    evidence_parts = [llm_evidence]
    if name_similarity >= 60:
        evidence_parts.append(f"Name similarity: {name_similarity:.1f}%")
    if extracted_phones:
        evidence_parts.append(f"Contact info found: {len(extracted_phones)} phones")

    return {
        'validated': validated,
        'confidence': final_confidence,
        'evidence': ' | '.join(evidence_parts),
        'signals': {
            'phone_match': phone_match,
            'name_similarity': name_similarity,
            'llm_match': llm_match,
            'llm_confidence': llm_confidence
        },
        'method': 'hybrid' if name_similarity >= 60 or extracted_phones else 'llm'
    }
