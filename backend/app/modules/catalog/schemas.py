"""
Pydantic v2 schemas for Catalog, Tiers, Effective-Dated Pricing, and Transparent Quotes.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.modules.catalog.enums import DiscountType, ServiceTierType, WorkflowType


# ─── Category Schemas ────────────────────────────────────────────────────────

class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    name: str
    description: str | None = None
    icon: str
    display_order: int
    is_active: bool
    service_count: int = 0


class CategoryCreateRequest(BaseModel):
    slug: str = Field(..., min_length=2, max_length=100)
    name: str = Field(..., min_length=2, max_length=150)
    description: str | None = None
    icon: str = Field(default="✨", max_length=50)
    display_order: int = 0
    is_active: bool = True


# ─── Tier & Add-On Schemas ───────────────────────────────────────────────────

class ServiceAddOnResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    service_id: uuid.UUID
    name: str
    description: str | None = None
    price_paise: int
    duration_minutes: int
    is_active: bool


class ServiceTierResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    service_id: uuid.UUID
    tier: ServiceTierType
    name: str
    description: str
    brands: str
    duration_minutes: int
    inclusions: list[str]
    exclusions: list[str]
    is_popular: bool
    is_active: bool
    current_price_paise: int = 0  # Resolved from active pricing rule


class ServiceSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    category_id: uuid.UUID
    category_name: str | None = None
    slug: str
    name: str
    description: str
    icon: str
    workflow_type: WorkflowType
    starting_price_paise: int = 0
    duration_minutes: int = 0
    available_tiers: list[ServiceTierType] = []


class ServiceDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    category_id: uuid.UUID
    slug: str
    name: str
    description: str
    icon: str
    workflow_type: WorkflowType
    display_order: int
    is_active: bool
    tiers: list[ServiceTierResponse]
    add_ons: list[ServiceAddOnResponse]


# ─── Admin Creation Schemas ──────────────────────────────────────────────────

class ServiceCreateRequest(BaseModel):
    category_id: uuid.UUID
    slug: str = Field(..., min_length=2, max_length=100)
    name: str = Field(..., min_length=2, max_length=150)
    description: str = Field(..., min_length=5)
    icon: str = Field(default="✨", max_length=50)
    workflow_type: WorkflowType = WorkflowType.AT_HOME_VISIT
    display_order: int = 0
    is_active: bool = True


class TierCreateRequest(BaseModel):
    service_id: uuid.UUID
    tier: ServiceTierType
    name: str = Field(..., min_length=2, max_length=150)
    description: str = Field(..., min_length=5)
    brands: str = Field(..., min_length=2, max_length=255)
    duration_minutes: int = Field(..., gt=0)
    inclusions: list[str] = Field(default_factory=list)
    exclusions: list[str] = Field(default_factory=list)
    is_popular: bool = False
    base_price_paise: int = Field(..., gt=0, description="Initial base price in paise")


class PricingRuleCreateRequest(BaseModel):
    tier_id: uuid.UUID
    base_price_paise: int = Field(..., gt=0)
    effective_from: datetime
    effective_to: datetime | None = None


class AddOnCreateRequest(BaseModel):
    service_id: uuid.UUID
    name: str = Field(..., min_length=2, max_length=150)
    description: str | None = None
    price_paise: int = Field(..., gt=0)
    duration_minutes: int = Field(default=0, ge=0)


class DiscountCreateRequest(BaseModel):
    code: str = Field(..., min_length=3, max_length=50)
    discount_type: DiscountType
    value: int = Field(..., gt=0)
    max_discount_paise: int | None = None
    min_order_paise: int = 0
    valid_from: datetime
    valid_to: datetime | None = None


# ─── Quote & Pricing Engine Schemas ──────────────────────────────────────────

class QuoteItemAddOn(BaseModel):
    id: uuid.UUID
    name: str
    price_paise: int
    duration_minutes: int


class QuoteRequest(BaseModel):
    service_id: uuid.UUID
    tier: ServiceTierType
    add_on_ids: list[uuid.UUID] = Field(default_factory=list)
    discount_code: str | None = None
    professional_price_paise: int | None = None  # Specific pro override (if applicable)
    pincode: str = Field(default="560038")


class QuoteResponse(BaseModel):
    quote_id: uuid.UUID
    service_id: uuid.UUID
    service_name: str
    tier: ServiceTierType
    tier_name: str
    duration_minutes: int
    brands: str
    inclusions: list[str]
    base_price_paise: int
    add_ons: list[QuoteItemAddOn]
    travel_fee_paise: int
    pickup_delivery_fee_paise: int
    subtotal_paise: int
    discount_paise: int
    tax_cgst_paise: int
    tax_sgst_paise: int
    tax_rate_percent: int = 18
    total_paise: int
    expires_at: datetime
    immutable_price_snapshot: dict[str, Any]
