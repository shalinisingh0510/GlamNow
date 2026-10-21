"""
Catalog and pricing engine ORM models with effective-dated price versioning.
"""

from __future__ import annotations

from datetime import datetime
import uuid

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.modules.catalog.enums import DiscountType, ServiceTierType, WorkflowType


class ServiceCategory(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Top-level category (e.g., Beauty, Hair, Makeup, Massage, Nails, Saree Draping, Pico-Fall, Tailoring).
    """

    __tablename__ = "service_categories"

    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon: Mapped[str] = mapped_column(String(50), default="✨", nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    services: Mapped[list[Service]] = relationship(
        "Service", back_populates="category", cascade="all, delete-orphan", order_by="Service.display_order"
    )


class Service(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    A specific catalog service offering (e.g., Hydra Facial, Designer Blouse Stitching).
    """

    __tablename__ = "services"

    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("service_categories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    icon: Mapped[str] = mapped_column(String(50), default="✨", nullable=False)
    workflow_type: Mapped[WorkflowType] = mapped_column(
        Enum(WorkflowType, name="workflow_type_enum", native_enum=False),
        default=WorkflowType.AT_HOME_VISIT,
        nullable=False,
    )
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    category: Mapped[ServiceCategory] = relationship("ServiceCategory", back_populates="services")
    tiers: Mapped[list[ServiceTier]] = relationship(
        "ServiceTier", back_populates="service", cascade="all, delete-orphan"
    )
    add_ons: Mapped[list[ServiceAddOn]] = relationship(
        "ServiceAddOn", back_populates="service", cascade="all, delete-orphan"
    )


class ServiceTier(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Configurable experience tier (Basic, Standard, Premium) for a service.
    """

    __tablename__ = "service_tiers"

    service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("services.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tier: Mapped[ServiceTierType] = mapped_column(
        Enum(ServiceTierType, name="service_tier_type_enum", native_enum=False),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    brands: Mapped[str] = mapped_column(String(255), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    inclusions: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    exclusions: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    is_popular: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    service: Mapped[Service] = relationship("Service", back_populates="tiers")
    pricing_rules: Mapped[list[PricingRule]] = relationship(
        "PricingRule", back_populates="tier", cascade="all, delete-orphan", order_by="desc(PricingRule.effective_from)"
    )


class PricingRule(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Effective-dated pricing rules for a tier.

    ADR-0003: Modifying a price creates a new pricing rule with effective dates
    rather than overwriting existing records.
    """

    __tablename__ = "pricing_rules"

    tier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("service_tiers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    base_price_paise: Mapped[int] = mapped_column(Integer, nullable=False)  # Integer paise (e.g. 79900 = ₹799)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    tier: Mapped[ServiceTier] = relationship("ServiceTier", back_populates="pricing_rules")


class ServiceAddOn(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Optional add-on service attachments (e.g., Argan Hair Mask, French polish, designer latkan).
    """

    __tablename__ = "service_add_ons"

    service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("services.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    service: Mapped[Service] = relationship("Service", back_populates="add_ons")


class DiscountRule(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Promotional discounts and coupons.
    """

    __tablename__ = "discount_rules"

    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    discount_type: Mapped[DiscountType] = mapped_column(
        Enum(DiscountType, name="discount_type_enum", native_enum=False),
        nullable=False,
    )
    value: Mapped[int] = mapped_column(Integer, nullable=False)  # Percentage (e.g. 10) or Paise (e.g. 10000 = ₹100)
    max_discount_paise: Mapped[int | None] = mapped_column(Integer, nullable=True)
    min_order_paise: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
