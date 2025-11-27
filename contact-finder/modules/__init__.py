# Contact Finder Modules
"""
Module hierarchy:

modules/
├── llm/           - LLM provider abstraction (OpenAI, Anthropic)
├── enrichment/    - API clients (Blitz, LeadMagic, Scrapin, Exa, SiteScraper)
├── discovery/     - LinkedIn company and contact discovery
└── validation/    - Email validation, LinkedIn normalization, LLM judge
"""

from .llm import LLMProvider, get_provider
from .enrichment import (
    BlitzClient,
    LeadMagicClient,
    ScrapinClient,
    ExaClient,
    SiteScraper,
    EnrichmentWaterfall,
)
from .discovery import (
    LinkedInCompanyDiscovery,
    ContactSearchEngine,
)
from .validation import (
    EmailValidator,
    EmailOrigin,
    ContactJudge,
    normalize_linkedin_url,
)
