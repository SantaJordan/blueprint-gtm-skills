"""
Discovery modules for finding company and contact information
"""

from .linkedin_company import LinkedInCompanyDiscovery, CompanyLinkedInResult
from .contact_search import ContactSearchEngine, ContactCandidate

__all__ = [
    "LinkedInCompanyDiscovery",
    "CompanyLinkedInResult",
    "ContactSearchEngine",
    "ContactCandidate",
]
