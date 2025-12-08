"""
Reference data for Blueprint GTM worker.

Contains pre-scored verticals, niche conversions, database field catalogs,
and product category validation rules.
"""

from .data_moat_verticals import (
    TIER_1_VERTICALS,
    NICHE_CONVERSIONS,
    get_vertical_score,
    convert_to_niche
)

from .common_databases import (
    DATABASE_CATALOG,
    get_database_fields,
    get_database_url
)

from .product_categories import (
    PRODUCT_CATEGORIES,
    detect_product_category,
    get_category_config,
    validate_segment_for_category,
    validate_vertical_for_category,
    get_segment_examples
)
