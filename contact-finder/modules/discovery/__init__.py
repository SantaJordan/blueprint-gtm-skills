"""
Discovery modules for finding company and contact information
"""

from .linkedin_company import LinkedInCompanyDiscovery, CompanyLinkedInResult
from .contact_search import ContactSearchEngine, ContactCandidate
from .openweb_ninja import (
    OpenWebNinjaClient,
    LocalBusinessResult,
    OpenWebContactResult,
    SocialLinksResult,
)
from .email_permutator import (
    generate_email_permutations,
    parse_name,
    split_name,
    is_valid_for_permutation,
    NameComponents,
)
from .email_finder import (
    EmailFinder,
    EmailFinderResult,
    EmailCandidate,
    find_email_for_contact,
)

__all__ = [
    "LinkedInCompanyDiscovery",
    "CompanyLinkedInResult",
    "ContactSearchEngine",
    "ContactCandidate",
    # OpenWeb Ninja
    "OpenWebNinjaClient",
    "LocalBusinessResult",
    "OpenWebContactResult",
    "SocialLinksResult",
    # Email Finder
    "generate_email_permutations",
    "parse_name",
    "split_name",
    "is_valid_for_permutation",
    "NameComponents",
    "EmailFinder",
    "EmailFinderResult",
    "EmailCandidate",
    "find_email_for_contact",
]
