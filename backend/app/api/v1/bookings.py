"""
Booking management, quick dispatch, and payment endpoints.
"""

from __future__ import annotations

from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_db_session
from app.modules.bookings.models import Booking
from app.modules.bookings.schemas import (
    BookingCreateRequest,
    BookingDetailResponse,
    BookingItemSchema,
    BookingPriceSnapshotSchema,
    BookingStatusHistoryItem,
    CancelBookingRequest,
    PaymentConfirmRequest,
    PaymentConfirmResponse,
    PaymentInitiateResponse,
    ProfessionalResponseAction,
    RescheduleBookingRequest,
    VerifyOtpRequest,
)
from app.modules.bookings.service import BookingService
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User

router = APIRouter(prefix="/bookings", tags=["bookings"])


def get_booking_service(session: AsyncSession = Depends(get_db_session)) -> BookingService:
    return BookingService(session)


def _to_detail_response(booking: Booking) -> BookingDetailResponse:
    assigned_name = None
    if booking.assigned_professional and booking.assigned_professional.user:
        assigned_name = booking.assigned_professional.user.full_name

    price_snap = BookingPriceSnapshotSchema(
        base_rate_paise=booking.price_snapshot.base_rate_paise,
        add_ons_total_paise=booking.price_snapshot.add_ons_total_paise,
        travel_fee_paise=booking.price_snapshot.travel_fee_paise,
        discount_applied_paise=booking.price_snapshot.discount_applied_paise,
        taxable_amount_paise=booking.price_snapshot.taxable_amount_paise,
        cgst_paise=booking.price_snapshot.cgst_paise,
        sgst_paise=booking.price_snapshot.sgst_paise,
        total_payable_paise=booking.price_snapshot.total_payable_paise,
        snapshot_hash=booking.price_snapshot.snapshot_hash,
    )

    items = [
        BookingItemSchema(
            name=it.name,
            item_type=it.item_type,
            price_paise=it.price_paise,
            quantity=it.quantity,
        )
        for it in booking.items
    ]

    history = [
        BookingStatusHistoryItem(
            from_status=h.from_status,
            to_status=h.to_status,
            actor_role=h.actor_role,
            reason=h.reason,
            created_at=h.created_at,
        )
        for h in booking.status_history
    ]

    return BookingDetailResponse(
        id=booking.id,
        booking_number=booking.booking_number,
        customer_id=booking.customer_id,
        assigned_professional_id=booking.assigned_professional_id,
        assigned_professional_name=assigned_name,
        service_id=booking.service_id,
        service_name=booking.service.name if booking.service else "Service",
        tier_type=booking.tier_type,
        booking_type=booking.booking_type,
        status=booking.status,
        address_snapshot=booking.address_snapshot,
        scheduled_start_time=booking.scheduled_start_time,
        scheduled_end_time=booking.scheduled_end_time,
        hold_expires_at=booking.hold_expires_at,
        start_otp=booking.start_otp,
        completion_otp=booking.completion_otp,
        eta_minutes=booking.eta_minutes,
        is_fallback_location=booking.is_fallback_location,
        cancellation_fee_paise=booking.cancellation_fee_paise,
        price_snapshot=price_snap,
        items=items,
        history=history,
    )


@router.post(
    "",
    response_model=BookingDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create booking hold (10 min TTL) with immutable quote snapshot",
)
async def create_booking(
    data: BookingCreateRequest,
    current_user: User = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service),
) -> BookingDetailResponse:
    booking = await service.create_booking_hold(customer=current_user, data=data)
    return _to_detail_response(booking)


@router.get(
    "/my",
    response_model=list[BookingDetailResponse],
    summary="List customer's own bookings",
)
async def list_my_bookings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[BookingDetailResponse]:
    stmt = (
        select(Booking)
        .where(Booking.customer_id == current_user.id)
        .options(
            selectinload(Booking.customer),
            selectinload(Booking.assigned_professional).selectinload(ProfessionalProfile.user),
            selectinload(Booking.service),
            selectinload(Booking.items),
            selectinload(Booking.price_snapshot),
            selectinload(Booking.status_history),
        )
        .order_by(Booking.created_at.desc())
    )
    bookings = (await db.execute(stmt)).scalars().all()
    return [_to_detail_response(b) for b in bookings]


@router.get(
    "/{id}",
    response_model=BookingDetailResponse,
    summary="Get full booking details and audit history",
)
async def get_booking(
    id: uuid.UUID,
    service: BookingService = Depends(get_booking_service),
) -> BookingDetailResponse:
    booking = await service.get_booking_by_id(id)
    return _to_detail_response(booking)


@router.post(
    "/{id}/pay",
    response_model=PaymentInitiateResponse,
    summary="Initiate payment order for active booking hold",
)
async def initiate_payment(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service),
) -> PaymentInitiateResponse:
    return await service.initiate_payment(booking_id=id, customer=current_user)


@router.post(
    "/{id}/confirm-payment",
    response_model=PaymentConfirmResponse,
    summary="Cryptographically verify payment and confirm booking with automated dispatch",
)
async def confirm_payment(
    id: uuid.UUID,
    data: PaymentConfirmRequest,
    current_user: User = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service),
) -> PaymentConfirmResponse:
    return await service.confirm_payment(
        booking_id=id, customer=current_user, data=data
    )


@router.post(
    "/{id}/dispatch-response",
    response_model=BookingDetailResponse,
    summary="Professional accepts or declines dispatch assignment",
)
async def respond_to_dispatch(
    id: uuid.UUID,
    data: ProfessionalResponseAction,
    current_user: User = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service),
) -> BookingDetailResponse:
    booking = await service.respond_to_dispatch(
        booking_id=id, pro_user=current_user, data=data
    )
    return _to_detail_response(booking)


@router.post(
    "/{id}/mark-arrived",
    response_model=BookingDetailResponse,
    summary="Professional marks arrival at customer doorstep",
)
async def mark_arrived(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service),
) -> BookingDetailResponse:
    booking = await service.mark_partner_arrived(booking_id=id, pro_user=current_user)
    return _to_detail_response(booking)


@router.post(
    "/{id}/verify-start",
    response_model=BookingDetailResponse,
    summary="Verify customer's 4-digit start OTP to begin service",
)
async def verify_start_otp(
    id: uuid.UUID,
    data: VerifyOtpRequest,
    current_user: User = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service),
) -> BookingDetailResponse:
    booking = await service.verify_start_otp(
        booking_id=id, pro_user=current_user, data=data
    )
    return _to_detail_response(booking)


@router.post(
    "/{id}/complete",
    response_model=BookingDetailResponse,
    summary="Complete service with customer completion OTP",
)
async def complete_service(
    id: uuid.UUID,
    data: VerifyOtpRequest,
    current_user: User = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service),
) -> BookingDetailResponse:
    booking = await service.complete_service(
        booking_id=id, pro_user=current_user, data=data
    )
    return _to_detail_response(booking)


@router.post(
    "/{id}/cancel",
    response_model=BookingDetailResponse,
    summary="Cancel booking according to SLA rules",
)
async def cancel_booking(
    id: uuid.UUID,
    data: CancelBookingRequest,
    current_user: User = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service),
) -> BookingDetailResponse:
    booking = await service.cancel_booking(
        booking_id=id, actor=current_user, data=data
    )
    return _to_detail_response(booking)


@router.post(
    "/{id}/reschedule",
    response_model=BookingDetailResponse,
    summary="Reschedule booking slot (>2 hours notice required)",
)
async def reschedule_booking(
    id: uuid.UUID,
    data: RescheduleBookingRequest,
    current_user: User = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service),
) -> BookingDetailResponse:
    booking = await service.reschedule_booking(
        booking_id=id, customer=current_user, data=data
    )
    return _to_detail_response(booking)
