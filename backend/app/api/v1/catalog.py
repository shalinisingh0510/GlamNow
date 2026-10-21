"""
Catalog and pricing API routes (Public browsing & Admin configuration).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db_session
from app.modules.catalog.schemas import (
    AddOnCreateRequest,
    CategoryCreateRequest,
    CategoryResponse,
    DiscountCreateRequest,
    PricingRuleCreateRequest,
    QuoteRequest,
    QuoteResponse,
    ServiceAddOnResponse,
    ServiceCreateRequest,
    ServiceDetailResponse,
    ServiceSummaryResponse,
    ServiceTierResponse,
    TierCreateRequest,
)
from app.modules.catalog.service import CatalogService
from app.modules.identity.dependencies import require_role
from app.modules.identity.enums import UserRole
from app.modules.identity.models import User

router = APIRouter(prefix="/catalog", tags=["catalog"])


def get_catalog_service(session: AsyncSession = Depends(get_db_session)) -> CatalogService:
    return CatalogService(session)


# ─── Public Endpoints ────────────────────────────────────────────────────────

@router.get(
    "/categories",
    response_model=list[CategoryResponse],
    summary="List all active service categories",
)
async def list_categories(
    service: CatalogService = Depends(get_catalog_service),
) -> list[CategoryResponse]:
    return await service.list_categories()


@router.get(
    "/services",
    response_model=list[ServiceSummaryResponse],
    summary="List, search and filter services",
)
async def list_services(
    category_id: uuid.UUID | None = Query(None, description="Filter by category ID"),
    search: str | None = Query(None, description="Search term for service name or description"),
    service: CatalogService = Depends(get_catalog_service),
) -> list[ServiceSummaryResponse]:
    return await service.list_services(category_id=category_id, search=search)


@router.get(
    "/services/{identifier}",
    response_model=ServiceDetailResponse,
    summary="Get service details with all active tiers and add-ons",
)
async def get_service(
    identifier: str,
    service: CatalogService = Depends(get_catalog_service),
) -> ServiceDetailResponse:
    return await service.get_service_detail(identifier)


@router.post(
    "/quote",
    response_model=QuoteResponse,
    summary="Calculate transparent server-validated price quote and snapshot",
)
async def calculate_quote(
    request: QuoteRequest,
    service: CatalogService = Depends(get_catalog_service),
) -> QuoteResponse:
    return await service.calculate_quote(request)


# ─── Admin Endpoints (Privileged Catalog Mutation) ───────────────────────────

@router.post(
    "/admin/categories",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new service category (Admin / Operations only)",
)
async def create_category(
    data: CategoryCreateRequest,
    admin_user: User = Depends(require_role(UserRole.ADMIN, UserRole.OPERATIONS_STAFF)),
    service: CatalogService = Depends(get_catalog_service),
) -> CategoryResponse:
    cat = await service.create_category(data)
    return CategoryResponse(
        id=cat.id,
        slug=cat.slug,
        name=cat.name,
        description=cat.description,
        icon=cat.icon,
        display_order=cat.display_order,
        is_active=cat.is_active,
        service_count=0,
    )


@router.post(
    "/admin/services",
    response_model=ServiceSummaryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Publish a new catalog service (Admin / Operations only)",
)
async def create_service(
    data: ServiceCreateRequest,
    admin_user: User = Depends(require_role(UserRole.ADMIN, UserRole.OPERATIONS_STAFF)),
    service: CatalogService = Depends(get_catalog_service),
) -> ServiceSummaryResponse:
    srv = await service.create_service(data)
    return ServiceSummaryResponse(
        id=srv.id,
        category_id=srv.category_id,
        slug=srv.slug,
        name=srv.name,
        description=srv.description,
        icon=srv.icon,
        workflow_type=srv.workflow_type,
        starting_price_paise=0,
        duration_minutes=0,
        available_tiers=[],
    )


@router.post(
    "/admin/tiers",
    response_model=ServiceTierResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Define experience tier & initial price rule (Admin / Operations only)",
)
async def create_tier(
    data: TierCreateRequest,
    admin_user: User = Depends(require_role(UserRole.ADMIN, UserRole.OPERATIONS_STAFF)),
    service: CatalogService = Depends(get_catalog_service),
) -> ServiceTierResponse:
    tier = await service.create_tier(data)
    return ServiceTierResponse(
        id=tier.id,
        service_id=tier.service_id,
        tier=tier.tier,
        name=tier.name,
        description=tier.description,
        brands=tier.brands,
        duration_minutes=tier.duration_minutes,
        inclusions=tier.inclusions,
        exclusions=tier.exclusions,
        is_popular=tier.is_popular,
        is_active=tier.is_active,
        current_price_paise=data.base_price_paise,
    )


@router.post(
    "/admin/pricing-rules",
    status_code=status.HTTP_201_CREATED,
    summary="Create effective-dated price rule (Admin / Operations only)",
)
async def create_pricing_rule(
    data: PricingRuleCreateRequest,
    admin_user: User = Depends(require_role(UserRole.ADMIN, UserRole.OPERATIONS_STAFF)),
    service: CatalogService = Depends(get_catalog_service),
) -> dict[str, str]:
    rule = await service.create_pricing_rule(data)
    return {
        "status": "created",
        "pricing_rule_id": str(rule.id),
        "base_price_paise": str(rule.base_price_paise),
    }


@router.post(
    "/admin/add-ons",
    response_model=ServiceAddOnResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create service add-on attachment (Admin / Operations only)",
)
async def create_add_on(
    data: AddOnCreateRequest,
    admin_user: User = Depends(require_role(UserRole.ADMIN, UserRole.OPERATIONS_STAFF)),
    service: CatalogService = Depends(get_catalog_service),
) -> ServiceAddOnResponse:
    addon = await service.create_add_on(data)
    return ServiceAddOnResponse.model_validate(addon)


@router.post(
    "/admin/discounts",
    status_code=status.HTTP_201_CREATED,
    summary="Create discount coupon rule (Admin / Operations only)",
)
async def create_discount(
    data: DiscountCreateRequest,
    admin_user: User = Depends(require_role(UserRole.ADMIN, UserRole.OPERATIONS_STAFF)),
    service: CatalogService = Depends(get_catalog_service),
) -> dict[str, str]:
    rule = await service.create_discount(data)
    return {"status": "created", "discount_rule_id": str(rule.id), "code": rule.code}
