"""
Product Categories Reference Data

Maps product types to their valid/invalid verticals and segment keywords.
Used by Wave 0.5, Wave 1.5, Synthesis, and Hard Gates for validation.

V5: Added to fix wrong segment generation (e.g., engineering teams for restaurants)
"""
from typing import Dict, List, Optional, Tuple


# Product category definitions with validation rules
PRODUCT_CATEGORIES = {
    "restaurant_platform": {
        "keywords": ["restaurant", "menu", "ordering", "food service", "hospitality", "delivery", "online ordering"],
        "valid_segments": [
            "review velocity", "commission bleed", "delivery fees", "online ordering",
            "menu optimization", "customer retention", "table booking", "food cost",
            "restaurant marketing", "review management", "third-party fees"
        ],
        "invalid_segments": [
            "engineering team", "series a", "series b", "funding round", "saas metrics",
            "software development", "tech startup", "venture capital", "developer tools",
            "code review", "sprint planning", "product roadmap"
        ],
        "valid_verticals": [
            "restaurants", "cafes", "food service", "hospitality", "quick service restaurants",
            "full service restaurants", "food delivery", "catering", "ghost kitchens"
        ],
        "invalid_verticals": [
            "saas companies", "tech startups", "software companies", "healthcare", "fintech"
        ]
    },

    "healthcare_dpc": {
        "keywords": ["dpc", "direct primary care", "primary care", "healthcare", "patient", "physician", "clinic", "medicare"],
        "valid_segments": [
            "medicare compliance", "patient panel", "employer contracts", "membership management",
            "patient retention", "clinical workflows", "healthcare billing", "practice growth",
            "dpc transition", "fee-for-service", "value-based care"
        ],
        "invalid_segments": [
            "beverage", "vending machine", "sugary drink", "water brand", "consumer packaged",
            "retail distribution", "grocery", "convenience store", "restaurant"
        ],
        "valid_verticals": [
            "dpc practices", "primary care clinics", "family medicine", "internal medicine",
            "concierge medicine", "employer health", "healthcare providers"
        ],
        "invalid_verticals": [
            "restaurants", "retail", "consumer goods", "beverages", "food service"
        ]
    },

    "healthcare_ehr": {
        "keywords": ["ehr", "electronic health record", "emr", "clinical", "patient record", "healthcare api", "interoperability"],
        "valid_segments": [
            "interoperability requirements", "ehr migration", "clinical documentation",
            "patient data", "healthcare compliance", "medical records", "api integration",
            "clinical workflows", "care coordination"
        ],
        "invalid_segments": [
            "sales productivity", "email engagement", "restaurant ordering", "networking events",
            "contact sharing", "engineering team"
        ],
        "valid_verticals": [
            "healthcare providers", "clinics", "hospitals", "medical practices", "health systems",
            "urgent care", "specialty care", "behavioral health"
        ],
        "invalid_verticals": [
            "restaurants", "retail", "sales teams", "marketing agencies"
        ]
    },

    "sales_engagement": {
        "keywords": ["sales", "email", "sequence", "outreach", "engagement", "prospecting", "productivity", "inbox"],
        "valid_segments": [
            "sales productivity", "email engagement", "meeting booking", "sales pipeline",
            "prospecting efficiency", "follow-up automation", "response rates", "sales workflow",
            "inbox management", "email scheduling", "sales cadence"
        ],
        "invalid_segments": [
            "healthcare compliance", "medical billing", "patient care", "nursing home",
            "cms deficiency", "restaurant ordering", "food service", "environmental permit",
            "regulatory violation"
        ],
        "valid_verticals": [
            "b2b sales teams", "saas companies", "tech companies", "sales organizations",
            "account executives", "sdr teams", "business development"
        ],
        "invalid_verticals": [
            "healthcare facilities", "nursing homes", "restaurants", "environmental services"
        ]
    },

    "contact_networking": {
        "keywords": ["contact", "business card", "networking", "connect", "share contact", "qr code", "digital card"],
        "valid_segments": [
            "contact sharing", "networking events", "employee onboarding", "sales introductions",
            "conference networking", "lead capture", "contact management", "digital business card",
            "team scaling", "new hire onboarding"
        ],
        "invalid_segments": [
            "regulatory violation", "compliance deadline", "license renewal", "epa citation",
            "osha violation", "cms deficiency", "healthcare compliance", "food safety",
            "trucking regulations"
        ],
        "valid_verticals": [
            "professional services", "consulting", "real estate", "financial services",
            "sales teams", "enterprise", "event management"
        ],
        "invalid_verticals": [
            "healthcare facilities", "trucking companies", "environmental services",
            "food manufacturing", "nursing homes"
        ]
    },

    "compliance_regulatory": {
        "keywords": ["compliance", "regulatory", "audit", "violation", "inspection", "permit", "license"],
        "valid_segments": [
            "regulatory violations", "audit preparation", "compliance deadlines", "permit management",
            "license renewal", "inspection readiness", "violation remediation", "compliance tracking",
            "regulatory reporting"
        ],
        "invalid_segments": [
            "sales productivity", "email engagement", "networking events", "contact sharing",
            "social events", "marketing campaigns"
        ],
        "valid_verticals": [
            "regulated industries", "healthcare", "financial services", "food manufacturing",
            "environmental services", "trucking", "construction"
        ],
        "invalid_verticals": [
            "general tech", "saas companies", "marketing agencies", "consulting firms"
        ]
    }
}


def detect_product_category(offering: str, company_name: str = "") -> Optional[str]:
    """
    Detect product category from offering description.

    Args:
        offering: Product/service description
        company_name: Company name for additional context

    Returns:
        Category key if detected, None otherwise
    """
    text = f"{offering} {company_name}".lower()

    for category, config in PRODUCT_CATEGORIES.items():
        for keyword in config["keywords"]:
            if keyword.lower() in text:
                return category

    return None


def get_category_config(category: str) -> Optional[Dict]:
    """Get full configuration for a product category."""
    return PRODUCT_CATEGORIES.get(category)


def validate_segment_for_category(
    segment_name: str,
    segment_description: str,
    category: str
) -> Tuple[bool, Optional[str]]:
    """
    Validate a segment against product category rules.

    Args:
        segment_name: Name of the segment
        segment_description: Description of the segment
        category: Product category key

    Returns:
        (is_valid, error_message)
    """
    if category not in PRODUCT_CATEGORIES:
        return True, None  # Unknown category, allow

    config = PRODUCT_CATEGORIES[category]
    combined = f"{segment_name} {segment_description}".lower()

    # Check for invalid segment keywords
    for invalid in config["invalid_segments"]:
        if invalid.lower() in combined:
            return False, f"Segment contains invalid keyword '{invalid}' for {category}"

    # Check for at least one valid segment keyword (soft check)
    has_valid = any(
        valid.lower() in combined
        for valid in config["valid_segments"]
    )

    if not has_valid:
        # Warn but don't auto-reject - could be a novel valid segment
        print(f"[Product Categories] Warning: Segment may not match {category} valid keywords")

    return True, None


def validate_vertical_for_category(
    vertical: str,
    category: str
) -> Tuple[bool, Optional[str]]:
    """
    Validate a vertical/industry against product category rules.

    Args:
        vertical: Industry/vertical name
        category: Product category key

    Returns:
        (is_valid, error_message)
    """
    if category not in PRODUCT_CATEGORIES:
        return True, None

    config = PRODUCT_CATEGORIES[category]
    vertical_lower = vertical.lower()

    # Check for invalid verticals
    for invalid in config["invalid_verticals"]:
        if invalid.lower() in vertical_lower:
            return False, f"Vertical '{vertical}' is invalid for {category}"

    return True, None


def get_segment_examples(category: str) -> Dict[str, List[str]]:
    """Get valid and invalid segment examples for a category."""
    if category not in PRODUCT_CATEGORIES:
        return {"valid": [], "invalid": []}

    config = PRODUCT_CATEGORIES[category]
    return {
        "valid": config["valid_segments"][:5],
        "invalid": config["invalid_segments"][:5]
    }
