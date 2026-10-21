"""
Catalog and Pricing Engine Service.

Computes transparent, tamper-proof quotes with server-side validation
and generates immutable price snapshots per ADR-0003.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.modules.catalog.enums import DiscountType, WorkflowType
from app.modules.catalog.models import (
    DiscountRule,
    PricingRule,
    Service,
    ServiceAddOn,
    ServiceCategory,
    ServiceTier,
)
from app.modules.catalog.repository import (
    AddOnRepository,
    CategoryRepository,
    DiscountRepository,
    PricingRepository,
    ServiceRepository,
    TierRepository,
)
from app.modules.catalog.schemas import (
    AddOnCreateRequest,
    CategoryCreateRequest,
    CategoryResponse,
    DiscountCreateRequest,
    PricingRuleCreateRequest,
    QuoteItemAddOn,
    QuoteRequest,
    QuoteResponse,
    ServiceAddOnResponse,
    ServiceCreateRequest,
    ServiceDetailResponse,
    ServiceSummaryResponse,
    ServiceTierResponse,
    TierCreateRequest,
)

QUOTE_TTL_MINUTES = 15
TAX_RATE_PERCENT = 18  # 18% GST (9% CGST + 9% SGST) for salon and grooming services in India


class CatalogService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.category_repo = CategoryRepository(session)
        self.service_repo = ServiceRepository(session)
        self.tier_repo = TierRepository(session)
        self.pricing_repo = PricingRepository(session)
        self.add_on_repo = AddOnRepository(session)
        self.discount_repo = DiscountRepository(session)

    # ─── Public Browsing ─────────────────────────────────────────────────────

    async def list_categories(self) -> list[CategoryResponse]:
        categories = await self.category_repo.list_active()
        return [
            CategoryResponse(
                id=c.id,
                slug=c.slug,
                name=c.name,
                description=c.description,
                icon=c.icon,
                display_order=c.display_order,
                is_active=c.is_active,
                service_count=len(c.services),
            )
            for c in categories
        ]

    async def list_services(
        self,
        category_id: uuid.UUID | None = None,
        search: str | None = None,
    ) -> list[ServiceSummaryResponse]:
        services = await self.service_repo.list_services(category_id=category_id, search=search)
        results: list[ServiceSummaryResponse] = []
        now = datetime.now(timezone.utc)

        for s in services:
            # Find starting price among active tiers
            starting_price = 0
            duration = 0
            tier_types = []
            for t in s.tiers:
                if t.is_active:
                    tier_types.append(t.tier)
                    rule = await self.pricing_repo.get_effective_rule(t.id, at_time=now)
                    if rule and (starting_price == 0 or rule.base_price_paise < starting_price):
                        starting_price = rule.base_price_paise
                        duration = t.duration_minutes

            results.append(
                ServiceSummaryResponse(
                    id=s.id,
                    category_id=s.category_id,
                    category_name=s.category.name if s.category else None,
                    slug=s.slug,
                    name=s.name,
                    description=s.description,
                    icon=s.icon,
                    workflow_type=s.workflow_type,
                    starting_price_paise=starting_price,
                    duration_minutes=duration,
                    available_tiers=tier_types,
                )
            )
        return results

    async def get_service_detail(self, identifier: str) -> ServiceDetailResponse:
        service = await self.service_repo.get_by_id_or_slug(identifier)
        if service is None:
            raise NotFoundError(resource="Service", identifier=identifier)

        now = datetime.now(timezone.utc)
        tier_responses: list[ServiceTierResponse] = []
        for t in service.tiers:
            if t.is_active:
                rule = await self.pricing_repo.get_effective_rule(t.id, at_time=now)
                current_price = rule.base_price_paise if rule else 0
                tier_responses.append(
                    ServiceTierResponse(
                        id=t.id,
                        service_id=t.service_id,
                        tier=t.tier,
                        name=t.name,
                        description=t.description,
                        brands=t.brands,
                        duration_minutes=t.duration_minutes,
                        inclusions=t.inclusions,
                        exclusions=t.exclusions,
                        is_popular=t.is_popular,
                        is_active=t.is_active,
                        current_price_paise=current_price,
                    )
                )

        add_on_responses = [
            ServiceAddOnResponse(
                id=a.id,
                service_id=a.service_id,
                name=a.name,
                description=a.description,
                price_paise=a.price_paise,
                duration_minutes=a.duration_minutes,
                is_active=a.is_active,
            )
            for a in service.add_ons
            if a.is_active
        ]

        return ServiceDetailResponse(
            id=service.id,
            category_id=service.category_id,
            slug=service.slug,
            name=service.name,
            description=service.description,
            icon=service.icon,
            workflow_type=service.workflow_type,
            display_order=service.display_order,
            is_active=service.is_active,
            tiers=tier_responses,
            add_ons=add_on_responses,
        )

    # ─── Pricing Engine & Quote Calculation ──────────────────────────────────

    async def calculate_quote(
        self,
        request: QuoteRequest,
        at_time: datetime | None = None,
    ) -> QuoteResponse:
        """
        Calculates transparent, tamper-proof quote on the server.
        Enforces:
        - Active effective-dated pricing rule
        - Strict add-on validation belonging to the service
        - Mandatory GST (18%) computation
        - Discount validation and caps
        - Generation of immutable snapshot
        """
        calculation_time = at_time or datetime.now(timezone.utc)

        # 1. Fetch service
        service = await self.service_repo.get_by_id_or_slug(str(request.service_id))
        if service is None or not service.is_active:
            raise NotFoundError(resource="Service", identifier=str(request.service_id))

        # 2. Fetch tier
        tier = await self.tier_repo.get_by_service_and_tier(service.id, request.tier)
        if tier is None or not tier.is_active:
            raise NotFoundError(
                message=f"Tier '{request.tier.value}' is not configured or active for this service"
            )

        # 3. Resolve effective pricing rule
        pricing_rule = await self.pricing_repo.get_effective_rule(tier.id, at_time=calculation_time)
        if pricing_rule is None:
            raise ValidationError(
                message=f"No active pricing rule available for {tier.name} at the requested time"
            )

        base_price_paise = pricing_rule.base_price_paise
        # If a custom professional price is provided (e.g. Master Stylist), validate it cannot be less than base
        if request.professional_price_paise is not None:
            if request.professional_price_paise < base_price_paise:
                raise ValidationError(message="Professional price cannot be lower than the base tier price")
            base_price_paise = request.professional_price_paise

        # 4. Fetch and validate add-ons
        add_on_entities = await self.add_on_repo.get_valid_add_ons(service.id, request.add_on_ids)
        if len(add_on_entities) != len(request.add_on_ids):
            raise ValidationError(
                message="One or more selected add-ons do not belong to this service or are inactive"
            )

        quote_add_ons = [
            QuoteItemAddOn(
                id=a.id,
                name=a.name,
                price_paise=a.price_paise,
                duration_minutes=a.duration_minutes,
            )
            for a in add_on_entities
        ]
        add_ons_total_paise = sum(a.price_paise for a in quote_add_ons)
        total_duration = tier.duration_minutes + sum(a.duration_minutes for a in quote_add_ons)

        # 5. Fulfillment & Travel Fees
        travel_fee_paise = 0
        pickup_delivery_fee_paise = 0
        if service.workflow_type in (
            WorkflowType.TAILORING_CUSTOM,
            WorkflowType.TAILORING_ALTERATION,
            WorkflowType.SAREE_CARE,
        ):
            # Standard doorstep fabric collection & return fee in Bangalore
            pickup_delivery_fee_paise = 9900  # ₹99.00

        gross_subtotal_paise = (
            base_price_paise + add_ons_total_paise + travel_fee_paise + pickup_delivery_fee_paise
        )

        # 6. Apply Promotional Discount (if applicable)
        discount_paise = 0
        if request.discount_code:
            discount_rule = await self.discount_repo.get_valid_discount(
                request.discount_code, gross_subtotal_paise, at_time=calculation_time
            )
            if discount_rule is not None:
                if discount_rule.discount_type == DiscountType.PERCENTAGE:
                    computed_discount = round(gross_subtotal_paise * (discount_rule.value / 100.0))
                else:
                    computed_discount = discount_rule.value

                if discount_rule.max_discount_paise is not None:
                    computed_discount = min(computed_discount, discount_rule.max_discount_paise)

                discount_paise = min(computed_discount, gross_subtotal_paise)

        net_taxable_paise = max(0, gross_subtotal_paise - discount_paise)

        # 7. Indian GST Calculation (9% CGST + 9% SGST)
        tax_cgst_paise = round(net_taxable_paise * 0.09)
        tax_sgst_paise = round(net_taxable_paise * 0.09)
        total_paise = net_taxable_paise + tax_cgst_paise + tax_sgst_paise

        # 8. Quote Expiry (15-minute hold)
        quote_id = uuid.uuid4()
        expires_at = calculation_time + timedelta(minutes=QUOTE_TTL_MINUTES)

        # 9. Generate Immutable Price Snapshot (ADR-0003)
        immutable_snapshot: dict[str, Any] = {
            "quote_id": str(quote_id),
            "service_id": str(service.id),
            "service_name": service.name,
            "tier": tier.tier.value,
            "tier_name": tier.name,
            "pricing_rule_id": str(pricing_rule.id),
            "brands": tier.brands,
            "inclusions": tier.inclusions,
            "duration_minutes": total_duration,
            "base_price_paise": base_price_paise,
            "add_ons": [
                {"id": str(a.id), "name": a.name, "price_paise": a.price_paise}
                for a in quote_add_ons
            ],
            "travel_fee_paise": travel_fee_paise,
            "pickup_delivery_fee_paise": pickup_delivery_fee_paise,
            "gross_subtotal_paise": gross_subtotal_paise,
            "discount_paise": discount_paise,
            "discount_code": request.discount_code if discount_paise > 0 else None,
            "tax_breakdown": {
                "cgst_paise": tax_cgst_paise,
                "sgst_paise": tax_sgst_paise,
                "rate_percent": TAX_RATE_PERCENT,
            },
            "total_paise": total_paise,
            "currency": "INR",
            "snapshot_timestamp": calculation_time.isoformat(),
        }

        return QuoteResponse(
            quote_id=quote_id,
            service_id=service.id,
            service_name=service.name,
            tier=tier.tier,
            tier_name=tier.name,
            duration_minutes=total_duration,
            brands=tier.brands,
            inclusions=tier.inclusions,
            base_price_paise=base_price_paise,
            add_ons=quote_add_ons,
            travel_fee_paise=travel_fee_paise,
            pickup_delivery_fee_paise=pickup_delivery_fee_paise,
            subtotal_paise=net_taxable_paise,
            discount_paise=discount_paise,
            tax_cgst_paise=tax_cgst_paise,
            tax_sgst_paise=tax_sgst_paise,
            tax_rate_percent=TAX_RATE_PERCENT,
            total_paise=total_paise,
            expires_at=expires_at,
            immutable_price_snapshot=immutable_snapshot,
        )

    # ─── Admin Management Methods ────────────────────────────────────────────

    async def create_category(self, data: CategoryCreateRequest) -> ServiceCategory:
        existing = await self.category_repo.get_by_slug(data.slug)
        if existing is not None:
            raise ConflictError(message=f"Category with slug '{data.slug}' already exists")

        cat = ServiceCategory(
            slug=data.slug,
            name=data.name,
            description=data.description,
            icon=data.icon,
            display_order=data.display_order,
            is_active=data.is_active,
        )
        return await self.category_repo.create(cat)

    async def create_service(self, data: ServiceCreateRequest) -> Service:
        category = await self.category_repo.get_by_id(data.category_id)
        if category is None:
            raise NotFoundError(resource="Category", identifier=str(data.category_id))

        existing = await self.service_repo.get_by_id_or_slug(data.slug)
        if existing is not None:
            raise ConflictError(message=f"Service with slug '{data.slug}' already exists")

        srv = Service(
            category_id=data.category_id,
            slug=data.slug,
            name=data.name,
            description=data.description,
            icon=data.icon,
            workflow_type=data.workflow_type,
            display_order=data.display_order,
            is_active=data.is_active,
        )
        return await self.service_repo.create(srv)

    async def create_tier(self, data: TierCreateRequest) -> ServiceTier:
        service = await self.service_repo.get_by_id_or_slug(str(data.service_id))
        if service is None:
            raise NotFoundError(resource="Service", identifier=str(data.service_id))

        existing = await self.tier_repo.get_by_service_and_tier(service.id, data.tier)
        if existing is not None:
            raise ConflictError(
                message=f"Tier '{data.tier.value}' is already defined for this service"
            )

        tier = ServiceTier(
            service_id=data.service_id,
            tier=data.tier,
            name=data.name,
            description=data.description,
            brands=data.brands,
            duration_minutes=data.duration_minutes,
            inclusions=data.inclusions,
            exclusions=data.exclusions,
            is_popular=data.is_popular,
            is_active=True,
        )
        await self.tier_repo.create(tier)

        # Create initial effective pricing rule
        rule = PricingRule(
            tier_id=tier.id,
            base_price_paise=data.base_price_paise,
            effective_from=datetime.now(timezone.utc),
            effective_to=None,
            is_active=True,
        )
        await self.pricing_repo.create_rule(rule)
        return tier

    async def create_pricing_rule(self, data: PricingRuleCreateRequest) -> PricingRule:
        rule = PricingRule(
            tier_id=data.tier_id,
            base_price_paise=data.base_price_paise,
            effective_from=data.effective_from,
            effective_to=data.effective_to,
            is_active=True,
        )
        return await self.pricing_repo.create_rule(rule)

    async def create_add_on(self, data: AddOnCreateRequest) -> ServiceAddOn:
        addon = ServiceAddOn(
            service_id=data.service_id,
            name=data.name,
            description=data.description,
            price_paise=data.price_paise,
            duration_minutes=data.duration_minutes,
            is_active=True,
        )
        return await self.add_on_repo.create(addon)

    async def create_discount(self, data: DiscountCreateRequest) -> DiscountRule:
        existing = await self.discount_repo.get_valid_discount(data.code, 0)
        if existing is not None:
            raise ConflictError(message=f"Discount code '{data.code}' already exists")

        rule = DiscountRule(
            code=data.code.upper(),
            discount_type=data.discount_type,
            value=data.value,
            max_discount_paise=data.max_discount_paise,
            min_order_paise=data.min_order_paise,
            valid_from=data.valid_from,
            valid_to=data.valid_to,
            is_active=True,
        )
        return await self.discount_repo.create(rule)
