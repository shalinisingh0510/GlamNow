"""
Catalog and Pricing Enums.
"""

from __future__ import annotations

import enum


class ServiceTierType(str, enum.Enum):
    """
    Standardized service experience tiers.
    """
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"


class WorkflowType(str, enum.Enum):
    """
    Typed extension points for service fulfillment workflows.
    """
    AT_HOME_VISIT = "at_home_visit"          # Standard beauty/hair/massage pro visits customer
    TAILORING_CUSTOM = "tailoring_custom"    # Measurement visit -> Fabric pickup -> Workshop -> Delivery
    TAILORING_ALTERATION = "tailoring_alteration" # Sample fitting / pin-up -> Workshop -> Delivery
    SAREE_CARE = "saree_care"                # Doorstep pickup -> Pico-fall & rolling steam -> Delivery


class DiscountType(str, enum.Enum):
    """
    Pricing discount types.
    """
    PERCENTAGE = "percentage"
    FLAT_PAISE = "flat_paise"
