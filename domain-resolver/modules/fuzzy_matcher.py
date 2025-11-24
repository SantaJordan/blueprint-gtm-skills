"""
Fuzzy matching module for domain-to-company name matching
Uses rapidfuzz for fast string similarity without LLM overhead
"""
from rapidfuzz import fuzz
from typing import Optional, Dict, Any
import logging

from .utils import normalize_company_name, get_base_domain

logger = logging.getLogger(__name__)


def calculate_fuzzy_score(company_name: str, url: str,
                          context: Optional[str] = None,
                          snippet: Optional[str] = None,
                          config: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Calculate fuzzy matching score between company name and domain
    Returns confidence score (0-100) without using LLM

    Args:
        company_name: Company name to match
        url: URL/domain to match against
        context: Optional context (industry, keywords) for disambiguation
        snippet: Optional search result snippet
        config: Configuration dict with thresholds

    Returns:
        {
            'score': int,  # 0-100 confidence
            'method': str,  # Description of matching method
            'details': dict  # Detailed breakdown
        }
    """
    # Default config
    if not config:
        config = {
            'exact_match_threshold': 90,
            'good_match_threshold': 70,
            'min_context_hits': 2
        }

    # Normalize inputs
    clean_name = normalize_company_name(company_name)
    domain_part = get_base_domain(url)

    if not clean_name or not domain_part:
        return {'score': 0, 'method': 'invalid_input', 'details': {}}

    # Calculate various similarity metrics
    exact_ratio = fuzz.ratio(clean_name, domain_part)
    partial_ratio = fuzz.partial_ratio(clean_name, domain_part)
    token_sort_ratio = fuzz.token_sort_ratio(clean_name, domain_part)

    details = {
        'clean_name': clean_name,
        'domain_part': domain_part,
        'exact_ratio': exact_ratio,
        'partial_ratio': partial_ratio,
        'token_sort_ratio': token_sort_ratio,
        'context_hits': 0,
        'snippet_match': False
    }

    # === Scoring Logic ===

    # 1. Perfect or near-perfect domain match
    if exact_ratio >= config['exact_match_threshold']:
        return {
            'score': 95,
            'method': 'exact_domain_match',
            'details': details
        }

    # 2. Check if company name is contained in domain
    if clean_name in domain_part or domain_part in clean_name:
        if exact_ratio >= 80:
            return {
                'score': 92,
                'method': 'high_substring_match',
                'details': details
            }

    # 3. Token-based matching (handles word order differences)
    if token_sort_ratio >= config['exact_match_threshold']:
        return {
            'score': 90,
            'method': 'token_sort_match',
            'details': details
        }

    # 4. Good partial match with context confirmation
    if partial_ratio >= config['good_match_threshold']:
        context_hits = 0

        # Check context words in snippet
        if context and snippet:
            context_words = context.lower().split()
            snippet_lower = snippet.lower()

            for word in context_words:
                if len(word) > 3 and word in snippet_lower:  # Ignore short words
                    context_hits += 1

            details['context_hits'] = context_hits

            # Strong context confirmation
            if context_hits >= config['min_context_hits']:
                return {
                    'score': 85,
                    'method': 'partial_match_with_context',
                    'details': details
                }
            elif context_hits >= 1:
                return {
                    'score': 75,
                    'method': 'partial_match_weak_context',
                    'details': details
                }

        # Partial match without context
        if partial_ratio >= 80:
            return {
                'score': 70,
                'method': 'partial_match_no_context',
                'details': details
            }

    # 5. Check if company name appears in snippet
    if snippet:
        snippet_lower = snippet.lower()
        if clean_name in snippet_lower:
            details['snippet_match'] = True
            # Company name in snippet + reasonable domain match
            if partial_ratio >= 60:
                return {
                    'score': 80,
                    'method': 'snippet_name_match',
                    'details': details
                }

    # 6. Weak match - needs LLM verification
    if partial_ratio >= 50:
        return {
            'score': 50,
            'method': 'weak_match_needs_llm',
            'details': details
        }

    # 7. No meaningful match
    return {
        'score': 0,
        'method': 'no_match',
        'details': details
    }


def match_multiple_candidates(company_name: str, candidates: list,
                               context: Optional[str] = None,
                               config: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
    """
    Match company name against multiple URL candidates
    Returns the best match above threshold

    Args:
        company_name: Company name to match
        candidates: List of dicts with 'url' and optionally 'snippet'
        context: Optional context for disambiguation
        config: Config dict

    Returns:
        Best match dict or None if no good matches
    """
    best_match = None
    best_score = 0

    for candidate in candidates:
        url = candidate.get('url') or candidate.get('link')
        snippet = candidate.get('snippet')

        if not url:
            continue

        result = calculate_fuzzy_score(
            company_name=company_name,
            url=url,
            context=context,
            snippet=snippet,
            config=config
        )

        if result['score'] > best_score:
            best_score = result['score']
            best_match = {
                'url': url,
                'score': result['score'],
                'method': result['method'],
                'details': result['details'],
                'snippet': snippet
            }

    return best_match


def is_acronym_match(company_name: str, domain: str) -> bool:
    """
    Check if domain is likely an acronym of company name
    Example: "International Business Machines" -> "ibm"
    """
    clean_name = normalize_company_name(company_name)
    words = clean_name.split()

    if len(words) < 2:
        return False

    # Create acronym from first letters
    acronym = ''.join(word[0] for word in words if word)

    domain_part = get_base_domain(domain)

    return acronym.lower() == domain_part.lower()


def calculate_advanced_score(company_name: str, url: str,
                             context: Optional[str] = None,
                             snippet: Optional[str] = None,
                             phone: Optional[str] = None,
                             config: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Advanced scoring with additional signals

    Args:
        company_name: Company name
        url: Domain URL
        context: Context keywords
        snippet: Search snippet
        phone: Optional phone number to check in snippet
        config: Config dict

    Returns:
        Scoring result dict
    """
    # Get base fuzzy score
    result = calculate_fuzzy_score(company_name, url, context, snippet, config)

    # Check for acronym match
    if is_acronym_match(company_name, url):
        result['score'] = max(result['score'], 88)
        result['method'] = 'acronym_match'

    # Boost score if phone number appears in snippet
    if phone and snippet:
        # Extract digits from phone
        import re
        phone_digits = re.sub(r'\D', '', phone)
        snippet_digits = re.sub(r'\D', '', snippet)

        if phone_digits and phone_digits[-4:] in snippet_digits:
            result['score'] = min(result['score'] + 10, 95)
            result['details']['phone_in_snippet'] = True

    return result
