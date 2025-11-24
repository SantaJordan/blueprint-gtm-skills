"""
Path Router - Intelligent Resolution Strategy Selection

Routes company resolution to appropriate strategies based on data completeness.
This is the "brain" of the V2 system that enables adaptive resolution.

Data Tiers:
- Tier 1: name + city + phone → High-confidence local business path
- Tier 2: name + city → Local business path (no phone verification)
- Tier 3: name + context → General business path (multi-source)
- Tier 4: name only → Aggressive multi-source path
"""

import logging
from typing import Dict, List, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ResolutionPath(Enum):
    """Available resolution paths"""
    HIGH_CONFIDENCE_LOCAL = "tier1_high_confidence"  # name+city+phone
    LOCAL_NO_PHONE = "tier2_local"                   # name+city
    GENERAL_BUSINESS = "tier3_general"               # name+context
    AGGRESSIVE_MULTI = "tier4_aggressive"            # name only


class PathRouter:
    """Routes companies to appropriate resolution strategies"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize path router

        Args:
            config: Configuration dict
        """
        self.config = config

    def route(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine resolution path for a company

        Args:
            company_data: Company information (must have _data_tier field)

        Returns:
            {
                'path': ResolutionPath,
                'strategies': List[str],  # Ordered list of strategies to try
                'parallel': bool,         # Execute strategies in parallel?
                'tier': int              # Data tier (1-4)
            }
        """
        tier = company_data.get('_data_tier', 4)

        if tier == 1:
            return self._tier1_strategy(company_data)
        elif tier == 2:
            return self._tier2_strategy(company_data)
        elif tier == 3:
            return self._tier3_strategy(company_data)
        else:  # tier == 4
            return self._tier4_strategy(company_data)

    def _tier1_strategy(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tier 1: name + city + phone (optimal data)

        Strategy:
        1. Try Places API with phone verification (99% confidence)
        2. If not found, fall through to Tier 2 strategy

        Expected: 90-95% success rate
        """
        return {
            'path': ResolutionPath.HIGH_CONFIDENCE_LOCAL,
            'strategies': [
                'places_phone_verify',  # Try phone verification first
                'places_name_match',    # Fall back to name match
                'serper_search',        # Fall back to general search
            ],
            'parallel': False,  # Sequential (each is a fallback)
            'tier': 1,
            'validation': 'always'  # Always validate final result
        }

    def _tier2_strategy(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tier 2: name + city (no phone)

        Strategy:
        1. Run Places API (name fuzzy match) + Serper Search in parallel
        2. Take best result or consensus

        Expected: 65-80% success rate
        """
        return {
            'path': ResolutionPath.LOCAL_NO_PHONE,
            'strategies': [
                'places_name_match',  # Places API without phone
                'serper_search',      # Knowledge Graph + organic results
            ],
            'parallel': True,  # Run both, take best result
            'tier': 2,
            'validation': 'always'
        }

    def _tier3_strategy(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tier 3: name + context (no location)

        Strategy:
        1. Run multiple sources in parallel:
           - LLM-powered search (intelligent queries)
           - Directory scraper (ZoomInfo, Crunchbase, etc.)
           - Serper Search + KG
           - Discolike
        2. Use consensus validation

        Expected: 50-70% success rate
        """
        return {
            'path': ResolutionPath.GENERAL_BUSINESS,
            'strategies': [
                'llm_search',          # LLM generates smart queries
                'directory_scraper',   # Search B2B directories
                'serper_search',       # Knowledge Graph
                'discolike',           # B2B enrichment database
            ],
            'parallel': True,  # All in parallel for speed
            'tier': 3,
            'validation': 'always',
            'consensus_required': True  # Prefer results from 2+ sources
        }

    def _tier4_strategy(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tier 4: name only (minimal data)

        Strategy:
        1. Aggressive multi-source approach (all methods in parallel)
        2. LLM analyzes results to pick best candidate
        3. Mandatory validation

        Expected: 30-50% success rate
        """
        return {
            'path': ResolutionPath.AGGRESSIVE_MULTI,
            'strategies': [
                'llm_search',          # LLM-powered search
                'directory_scraper',   # Directory sites
                'serper_search',       # Google Search
                'discolike',           # B2B data
            ],
            'parallel': True,  # All sources in parallel
            'tier': 4,
            'validation': 'mandatory',  # Must validate
            'consensus_required': True,  # Prefer agreement
            'llm_analysis': True  # Use LLM to pick best result
        }

    def should_use_strategy(self, strategy_name: str, company_data: Dict[str, Any]) -> bool:
        """
        Check if a specific strategy should be used

        Args:
            strategy_name: Name of strategy
            company_data: Company data

        Returns:
            True if strategy should be used
        """
        config = self.config.get('stages', {})

        # Check if strategy is enabled in config
        strategy_config_map = {
            'places_phone_verify': 'use_places',
            'places_name_match': 'use_places',
            'serper_search': 'use_search',
            'discolike': 'use_discolike',
            'llm_search': 'use_llm_search',
            'directory_scraper': 'use_directory_search',
        }

        config_key = strategy_config_map.get(strategy_name)
        if config_key:
            return config.get(config_key, True)

        return True

    def get_strategy_description(self, path: ResolutionPath) -> str:
        """Get human-readable description of resolution path"""

        descriptions = {
            ResolutionPath.HIGH_CONFIDENCE_LOCAL: "High-confidence local business (phone verification)",
            ResolutionPath.LOCAL_NO_PHONE: "Local business without phone (name matching)",
            ResolutionPath.GENERAL_BUSINESS: "General business (multi-source search)",
            ResolutionPath.AGGRESSIVE_MULTI: "Name-only (aggressive multi-source)"
        }

        return descriptions.get(path, "Unknown path")


def route_company(company_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to route a single company

    Args:
        company_data: Company information (must have _data_tier)
        config: Configuration dict

    Returns:
        Routing decision dict
    """
    router = PathRouter(config)
    return router.route(company_data)
