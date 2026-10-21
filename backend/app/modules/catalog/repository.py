"""
Catalog database repositories supporting effective-dated queries and filtering.
"""

from __future__ import annotations

from datetime import datetime, timezone
import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.catalog.enums import ServiceTierType
from app.modules.catalog.models import (
    DiscountRule,
    PricingRule,
    Service,
    ServiceAddOn,
    ServiceCategory,
    ServiceTier,
)


class CategoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_active(self) -> list[ServiceCategory]:
        stmt = (
            select(ServiceCategory)
            .where(ServiceCategory.is_active == True)  # noqa: E712
            .order_by(ServiceCategory.display_order, ServiceCategory.name)
            .options(selectinload(ServiceCategory.services))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, category_id: uuid.UUID) -> ServiceCategory | None:
        result = await self.session.execute(
            select(ServiceCategory).where(ServiceCategory.id == category_id)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> ServiceCategory | None:
        result = await self.session.execute(
            select(ServiceCategory).where(ServiceCategory.slug == slug)
        )
        return result.scalar_one_or_none()

    async def create(self, category: ServiceCategory) -> ServiceCategory:
        self.session.add(category)
        await self.session.flush()
        return category


class ServiceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_services(
        self,
        category_id: uuid.UUID | None = None,
        search: str | None = None,
    ) -> list[Service]:
        stmt = (
            select(Service)
            .where(Service.is_active == True)  # noqa: E712
            .options(
                selectinload(Service.category),
                selectinload(Service.tiers).selectinload(ServiceTier.pricing_rules),
                selectinload(Service.add_ons),
            )
            .order_by(Service.display_order, Service.name)
        )

        if category_id is not None:
            stmt = stmt.where(Service.category_id == category_id)

        if search:
            search_pattern = f"%{search.strip().lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(Service.name).like(search_pattern),
                    func.lower(Service.description).like(search_pattern),
                )
            )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id_or_slug(self, identifier: str) -> Service | None:
        """Finds service by UUID string or slug with loaded tiers and add-ons."""
        stmt = (
            select(Service)
            .options(
                selectinload(Service.category),
                selectinload(Service.tiers).selectinload(ServiceTier.pricing_rules),
                selectinload(Service.add_ons),
            )
        )
        try:
            val_uuid = uuid.UUID(identifier)
            stmt = stmt.where(Service.id == val_uuid)
        except ValueError:
            stmt = stmt.where(Service.slug == identifier)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, service: Service) -> Service:
        self.session.add(service)
        await self.session.flush()
        return service


class TierRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_service_and_tier(
        self, service_id: uuid.UUID, tier: ServiceTierType
    ) -> ServiceTier | None:
        stmt = (
            select(ServiceTier)
            .where(
                ServiceTier.service_id == service_id,
                ServiceTier.tier == tier,
                ServiceTier.is_active == True,  # noqa: E712
            )
            .options(selectinload(ServiceTier.pricing_rules))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, tier: ServiceTier) -> ServiceTier:
        self.session.add(tier)
        await self.session.flush()
        return tier


class PricingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_effective_rule(
        self, tier_id: uuid.UUID, at_time: datetime | None = None
    ) -> PricingRule | None:
        """
        Retrieves the effective pricing rule for a tier at a given point in time.
        ADR-0003: Versioned, effective-dated catalog pricing.
        """
        target_time = at_time or datetime.now(timezone.utc)
        stmt = (
            select(PricingRule)
            .where(
                PricingRule.tier_id == tier_id,
                PricingRule.is_active == True,  # noqa: E712
                PricingRule.effective_from <= target_time,
                or_(
                    PricingRule.effective_to.is_(None),
                    PricingRule.effective_to >= target_time,
                ),
            )
            .order_by(PricingRule.effective_from.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create_rule(self, rule: PricingRule) -> PricingRule:
        self.session.add(rule)
        await self.session.flush()
        return rule


class AddOnRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_valid_add_ons(
        self, service_id: uuid.UUID, add_on_ids: list[uuid.UUID]
    ) -> list[ServiceAddOn]:
        """
        Retrieves add-ons matching the given IDs and verifies they belong to the service.
        """
        if not add_on_ids:
            return []

        stmt = select(ServiceAddOn).where(
            ServiceAddOn.id.in_(add_on_ids),
            ServiceAddOn.service_id == service_id,
            ServiceAddOn.is_active == True,  # noqa: E712
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, add_on: ServiceAddOn) -> ServiceAddOn:
        self.session.add(add_on)
        await self.session.flush()
        return add_on


class DiscountRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_valid_discount(
        self, code: str, order_amount_paise: int, at_time: datetime | None = None
    ) -> DiscountRule | None:
        target_time = at_time or datetime.now(timezone.utc)
        stmt = select(DiscountRule).where(
            func.upper(DiscountRule.code) == code.strip().upper(),
            DiscountRule.is_active == True,  # noqa: E712
            DiscountRule.min_order_paise <= order_amount_paise,
            DiscountRule.valid_from <= target_time,
            or_(
                DiscountRule.valid_to.is_(None),
                DiscountRule.valid_to >= target_time,
            ),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, discount: DiscountRule) -> DiscountRule:
        self.session.add(discount)
        await self.session.flush()
        return discount
