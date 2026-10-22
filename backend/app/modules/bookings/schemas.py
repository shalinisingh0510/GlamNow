"""
Pydantic schemas for bookings, quotes, checkout, payment confirmation, and status history.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.modules.bookings.enums import (
    BookingStatus,
    BookingType,
    PaymentMethod,
    PaymentStatus,
)
from app.modules.catalog.enums import ServiceTierType


class BookingItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    item_type: str
    price_paise: int
    quantity: int = 1


class BookingPriceSnapshotSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    base_rate_paise: int
    add_ons_total_paise: int
    travel_fee_paise: int
    discount_applied_paise: int
    taxable_amount_paise: int
    cgst_paise: int
    sgst_paise: int
    total_payable_paise: int
    snapshot_hash: str


class BookingStatusHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    from_status: BookingStatus | None
    to_status: BookingStatus
    actor_role: str
    reason: str | None = None
    created_at: datetime


class BookingCreateRequest(BaseModel):
    """Customer request to reserve and hold a booking."""
    service_id: uuid.UUID
    tier_type: ServiceTierType
    booking_type: BookingType = BookingType.INSTANT
    address_id: uuid.UUID
    preferred_professional_id: uuid.UUID | None = None
    slot_id: uuid.UUID | None = None
    add_on_ids: list[uuid.UUID] = Field(default_factory=list)
    coupon_code: str | None = None
    idempotency_key: str = Field(..., max_length=100)


class BookingDetailResponse(BaseModel):
    """Full detail of a customer booking."""
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    booking_number: str
    customer_id: uuid.UUID
    assigned_professional_id: uuid.UUID | None
    assigned_professional_name: str | None = None
    service_id: uuid.UUID
    service_name: str
    tier_type: ServiceTierType
    booking_type: BookingType
    status: BookingStatus
    address_snapshot: dict[str, Any]
    scheduled_start_time: datetime | None = None
    scheduled_end_time: datetime | None = None
    hold_expires_at: datetime
    start_otp: str
    completion_otp: str | None = None
    eta_minutes: int | None = None
    is_fallback_location: bool = False
    cancellation_fee_paise: int = 0
    price_snapshot: BookingPriceSnapshotSchema
    items: list[BookingItemSchema] = Field(default_factory=list)
    history: list[BookingStatusHistoryItem] = Field(default_factory=list)


class PaymentInitiateResponse(BaseModel):
    """Sandbox payment checkout payload."""
    booking_id: uuid.UUID
    booking_number: str
    gateway_order_id: str
    amount_paise: int
    currency: str = "INR"
    hold_expires_at: datetime


class PaymentConfirmRequest(BaseModel):
    """Cryptographic payment verification payload."""
    gateway_order_id: str
    gateway_payment_id: str
    signature: str
    idempotency_key: str = Field(..., max_length=100)
    payment_method: PaymentMethod = PaymentMethod.ONLINE_UPI


class PaymentConfirmResponse(BaseModel):
    ok: bool
    booking_id: uuid.UUID
    booking_status: BookingStatus
    payment_status: PaymentStatus
    message: str


class ProfessionalResponseAction(BaseModel):
    action: str = Field(..., pattern=r"^(accept|decline)$")
    decline_reason: str | None = Field(None, max_length=200)


class VerifyOtpRequest(BaseModel):
    otp: str = Field(..., min_length=4, max_length=4, pattern=r"^\d{4}$")


class CancelBookingRequest(BaseModel):
    reason: str = Field(..., max_length=255)


class RescheduleBookingRequest(BaseModel):
    new_slot_id: uuid.UUID
