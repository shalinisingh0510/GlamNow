"""
Professionals discovery, profiles, working schedules, and slot reservation endpoints.
"""

from __future__ import annotations

from datetime import date
from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db_session
from app.modules.catalog.enums import ServiceTierType
from app.modules.identity.dependencies import get_current_user, require_role
from app.modules.identity.enums import UserRole
from app.modules.identity.models import User
from app.modules.professionals.enums import VerificationStatus
from app.modules.professionals.schemas import (
    AdminVerificationUpdate,
    AppointmentSlotResponse,
    BlockedDateCreate,
    BlockedDateResponse,
    PortfolioItemCreate,
    PortfolioItemResponse,
    ProfessionalCardResponse,
    ProfessionalDetailResponse,
    ProfessionalProfileCreate,
    ProfessionalProfileUpdate,
    ServiceOfferingCreate,
    ServiceOfferingResponse,
    SlotReservationRequest,
    SlotReservationResponse,
    WorkingHoursItem,
    WorkingHoursResponse,
)
from app.modules.professionals.service import ProfessionalService

router = APIRouter(prefix="/professionals", tags=["professionals"])


def get_professional_service(
    session: AsyncSession = Depends(get_db_session),
) -> ProfessionalService:
    return ProfessionalService(session)


def _to_detail_response(profile) -> ProfessionalDetailResponse:
    return ProfessionalDetailResponse(
        id=profile.id,
        user_id=profile.user_id,
        full_name=profile.user.full_name if profile.user else "Professional Partner",
        phone=profile.user.phone if profile.user else "",
        bio=profile.bio,
        experience_years=profile.experience_years,
        verification_status=profile.verification_status,
        rating=profile.rating,
        review_count=profile.review_count,
        is_active=profile.is_active,
        is_accepting_instant_bookings=profile.is_accepting_instant_bookings,
        latitude=profile.latitude,
        longitude=profile.longitude,
        service_radius_km=profile.service_radius_km,
        base_zone_name=profile.base_zone_name,
        skills=[s.name for s in profile.skills],
        service_offerings=[
            ServiceOfferingResponse(
                id=o.id,
                service_id=o.service_id,
                tier_type=o.tier_type,
                custom_price_paise=o.custom_price_paise,
                is_active=o.is_active,
            )
            for o in profile.service_offerings
        ],
        portfolios=[
            PortfolioItemResponse(
                id=p.id,
                title=p.title,
                description=p.description,
                image_url=p.image_url,
                service_id=p.service_id,
                is_verified=p.is_verified,
            )
            for p in profile.portfolios
        ],
        working_hours=[
            WorkingHoursResponse(
                id=h.id,
                day_of_week=h.day_of_week,
                start_time=h.start_time,
                end_time=h.end_time,
                break_start_time=h.break_start_time,
                break_end_time=h.break_end_time,
                is_working=h.is_working,
            )
            for h in profile.working_hours
        ],
    )


# ── Discovery & Public Endpoints ─────────────────────────────────────────────

@router.get(
    "/search",
    response_model=list[ProfessionalCardResponse],
    summary="Discover professionals with filters and arrival estimates",
)
async def search_professionals(
    category_slug: Annotated[str | None, Query(description="Category filter")] = None,
    service_id: Annotated[uuid.UUID | None, Query(description="Service filter")] = None,
    tier_type: Annotated[ServiceTierType | None, Query(description="Tier type filter")] = None,
    skill: Annotated[str | None, Query(description="Skill keyword")] = None,
    min_rating: Annotated[float | None, Query(ge=0.0, le=5.0)] = None,
    max_price_paise: Annotated[int | None, Query(ge=0)] = None,
    customer_lat: Annotated[float | None, Query(ge=-90.0, le=90.0)] = None,
    customer_lng: Annotated[float | None, Query(ge=-180.0, le=180.0)] = None,
    instant_only: Annotated[bool, Query()] = False,
    target_date: Annotated[date | None, Query()] = None,
    service: ProfessionalService = Depends(get_professional_service),
) -> list[ProfessionalCardResponse]:
    return await service.discover_professionals(
        category_slug=category_slug,
        service_id=service_id,
        tier_type=tier_type,
        skill=skill,
        min_rating=min_rating,
        max_price_paise=max_price_paise,
        customer_lat=customer_lat,
        customer_lng=customer_lng,
        instant_only=instant_only,
        target_date=target_date,
    )


@router.get(
    "/{id}",
    response_model=ProfessionalDetailResponse,
    summary="Get comprehensive professional profile with portfolio and offerings",
)
async def get_professional_profile(
    id: uuid.UUID,
    service: ProfessionalService = Depends(get_professional_service),
) -> ProfessionalDetailResponse:
    profile = await service.get_profile_by_id(id)
    return _to_detail_response(profile)


@router.get(
    "/{id}/slots",
    response_model=list[AppointmentSlotResponse],
    summary="Get bookable appointment slots for date with schedule & break synchronization",
)
async def get_professional_slots(
    id: uuid.UUID,
    target_date: Annotated[date | None, Query(description="Date to check availability")] = None,
    duration_minutes: Annotated[int, Query(ge=15, le=180)] = 60,
    service: ProfessionalService = Depends(get_professional_service),
) -> list[AppointmentSlotResponse]:
    check_date = target_date or date.today()
    slots = await service.get_or_generate_slots_for_date(
        professional_id=id,
        target_date=check_date,
        slot_duration_minutes=duration_minutes,
    )
    return [
        AppointmentSlotResponse(
            id=s.id,
            professional_id=s.professional_id,
            start_time=s.start_time,
            end_time=s.end_time,
            status=s.status,
            reservation_expires_at=s.reservation_expires_at,
        )
        for s in slots
    ]


# ── Slot Reservation (Transaction-Safe) ──────────────────────────────────────

@router.post(
    "/reserve-slot/{slot_id}",
    response_model=SlotReservationResponse,
    summary="Transaction-safe atomic slot reservation to prevent double booking",
)
async def reserve_slot(
    slot_id: uuid.UUID,
    data: SlotReservationRequest,
    current_user: User = Depends(get_current_user),
    service: ProfessionalService = Depends(get_professional_service),
) -> SlotReservationResponse:
    return await service.reserve_slot(
        slot_id=slot_id,
        user_id=current_user.id,
        service_id=data.service_id,
        hold_duration_minutes=data.hold_duration_minutes,
    )


@router.post(
    "/release-slot/{slot_id}",
    summary="Release previously held slot",
)
async def release_slot(
    slot_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ProfessionalService = Depends(get_professional_service),
) -> dict[str, bool]:
    released = await service.release_slot(slot_id=slot_id, user_id=current_user.id)
    return {"released": released}


# ── Profile Management & Onboarding ──────────────────────────────────────────

@router.post(
    "/profile",
    response_model=ProfessionalDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create professional profile (Onboarding for professionals)",
)
async def create_profile(
    data: ProfessionalProfileCreate,
    current_user: User = Depends(get_current_user),
    service: ProfessionalService = Depends(get_professional_service),
) -> ProfessionalDetailResponse:
    profile = await service.create_profile(user_id=current_user.id, data=data)
    return _to_detail_response(profile)


@router.patch(
    "/{id}/profile",
    response_model=ProfessionalDetailResponse,
    summary="Update professional profile details",
)
async def update_profile(
    id: uuid.UUID,
    data: ProfessionalProfileUpdate,
    current_user: User = Depends(get_current_user),
    service: ProfessionalService = Depends(get_professional_service),
) -> ProfessionalDetailResponse:
    profile = await service.update_profile(
        professional_id=id, actor_id=current_user.id, data=data
    )
    return _to_detail_response(profile)


@router.put(
    "/{id}/schedule",
    response_model=list[WorkingHoursResponse],
    summary="Update weekly working hours and daily shift breaks",
)
async def update_schedule(
    id: uuid.UUID,
    hours: list[WorkingHoursItem],
    current_user: User = Depends(get_current_user),
    service: ProfessionalService = Depends(get_professional_service),
) -> list[WorkingHoursResponse]:
    result = await service.set_working_hours(
        professional_id=id, hours=hours, actor_id=current_user.id
    )
    return [WorkingHoursResponse.model_validate(r) for r in result]


@router.post(
    "/{id}/blocked-dates",
    response_model=BlockedDateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add time off or blocked appointment dates",
)
async def add_blocked_date(
    id: uuid.UUID,
    data: BlockedDateCreate,
    current_user: User = Depends(get_current_user),
    service: ProfessionalService = Depends(get_professional_service),
) -> BlockedDateResponse:
    blocked = await service.add_blocked_date(
        professional_id=id, data=data, actor_id=current_user.id
    )
    return BlockedDateResponse.model_validate(blocked)


@router.post(
    "/{id}/offerings",
    response_model=ServiceOfferingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Configure tier-specific price offering for a catalog service",
)
async def add_service_offering(
    id: uuid.UUID,
    offering: ServiceOfferingCreate,
    current_user: User = Depends(get_current_user),
    service: ProfessionalService = Depends(get_professional_service),
) -> ServiceOfferingResponse:
    result = await service.set_service_offering(
        professional_id=id, offering=offering, actor_id=current_user.id
    )
    return ServiceOfferingResponse.model_validate(result)


@router.post(
    "/{id}/portfolio",
    response_model=PortfolioItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add authentic portfolio photo to showcase past work",
)
async def add_portfolio(
    id: uuid.UUID,
    item: PortfolioItemCreate,
    current_user: User = Depends(get_current_user),
    service: ProfessionalService = Depends(get_professional_service),
) -> PortfolioItemResponse:
    portfolio = await service.add_portfolio_item(
        professional_id=id, item=item, actor_id=current_user.id
    )
    return PortfolioItemResponse.model_validate(portfolio)


@router.patch(
    "/{id}/verification",
    response_model=ProfessionalDetailResponse,
    summary="Admin only: Update verification status of a professional",
)
async def update_verification(
    id: uuid.UUID,
    data: AdminVerificationUpdate,
    admin_user: User = Depends(require_role(UserRole.ADMIN)),
    service: ProfessionalService = Depends(get_professional_service),
) -> ProfessionalDetailResponse:
    profile = await service.update_verification_status(
        professional_id=id, status=data.verification_status, admin_user=admin_user
    )
    return _to_detail_response(profile)
