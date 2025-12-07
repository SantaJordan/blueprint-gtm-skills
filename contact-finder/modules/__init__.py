# Contact Finder Modules
"""
Module hierarchy:

modules/
├── llm/           - LLM provider abstraction (OpenAI, Anthropic)
├── enrichment/    - API clients (Blitz, LeadMagic, Scrapin, Exa)
├── discovery/     - LinkedIn company and contact discovery, email finding
└── validation/    - Email validation, LinkedIn normalization, LLM judge, MillionVerifier
"""

from .llm import LLMProvider, get_provider
from .enrichment import (
    BlitzClient,
    LeadMagicClient,
    ScrapinClient,
    ExaClient,
    EnrichmentWaterfall,
)
from .discovery import (
    LinkedInCompanyDiscovery,
    ContactSearchEngine,
    EmailFinder,
    generate_email_permutations,
)
from .validation import (
    EmailValidator,
    EmailOrigin,
    ContactJudge,
    normalize_linkedin_url,
    MillionVerifierClient,
)
