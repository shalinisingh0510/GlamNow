"""
Booking domain ORM models with immutable price snapshots, state machine history,
idempotency tracking, and dispatch offers.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import uuid

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.modules.bookings.enums import (
    BookingStatus,
    BookingType,
    DispatchOfferStatus,
    PaymentMethod,
    PaymentStatus,
)
from app.modules.catalog.enums import ServiceTierType


class Booking(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Core order entity for home visits and appointments.
    """

    __tablename__ = "bookings"

    booking_number: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    assigned_professional_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("professional_profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("services.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    tier_type: Mapped[ServiceTierType] = mapped_column(
        Enum(ServiceTierType, name="service_tier_type_enum", native_enum=False),
        nullable=False,
    )
    booking_type: Mapped[BookingType] = mapped_column(
        Enum(BookingType, name="booking_type_enum", native_enum=False),
        default=BookingType.INSTANT,
        nullable=False,
    )
    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus, name="booking_status_enum", native_enum=False),
        default=BookingStatus.HOLD_RESERVED,
        nullable=False,
        index=True,
    )
    idempotency_key: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    address_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("saved_addresses.id", ondelete="SET NULL"), nullable=True
    )
    address_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    scheduled_start_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    scheduled_end_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    slot_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("appointment_slots.id", ondelete="SET NULL"), nullable=True
    )
    hold_expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    start_otp: Mapped[str] = mapped_column(String(4), nullable=False)
    completion_otp: Mapped[str] = mapped_column(String(4), nullable=False)
    cancellation_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cancellation_fee_paise: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    eta_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_fallback_location: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    customer: Mapped["User"] = relationship("User", foreign_keys=[customer_id])  # type: ignore # noqa: F821
    assigned_professional: Mapped["ProfessionalProfile"] = relationship(  # type: ignore # noqa: F821
        "ProfessionalProfile", foreign_keys=[assigned_professional_id]
    )
    service: Mapped["Service"] = relationship("Service", foreign_keys=[service_id])  # type: ignore # noqa: F821
    items: Mapped[list[BookingItem]] = relationship(
        "BookingItem", back_populates="booking", cascade="all, delete-orphan"
    )
    price_snapshot: Mapped[BookingPriceSnapshot] = relationship(
        "BookingPriceSnapshot", back_populates="booking", uselist=False, cascade="all, delete-orphan"
    )
    status_history: Mapped[list[BookingStatusHistory]] = relationship(
        "BookingStatusHistory", back_populates="booking", cascade="all, delete-orphan", order_by="BookingStatusHistory.created_at"
    )
    payment_transactions: Mapped[list[PaymentTransaction]] = relationship(
        "PaymentTransaction", back_populates="booking", cascade="all, delete-orphan"
    )
    dispatch_offers: Mapped[list[DispatchOffer]] = relationship(
        "DispatchOffer", back_populates="booking", cascade="all, delete-orphan"
    )


class BookingItem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Line items for service tier and add-ons."""

    __tablename__ = "booking_items"

    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    item_type: Mapped[str] = mapped_column(String(30), nullable=False)  # SERVICE_TIER | ADD_ON
    price_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Relationships
    booking: Mapped[Booking] = relationship("Booking", back_populates="items")


class BookingPriceSnapshot(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Immutable pricing record captured at reservation time with cryptographic hash.
    ADR-0003 & Target Architecture Section 3.1.
    """

    __tablename__ = "booking_price_snapshots"

    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    base_rate_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    add_ons_total_paise: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    travel_fee_paise: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    discount_applied_paise: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    taxable_amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    cgst_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    sgst_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    total_payable_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    snapshot_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    # Relationships
    booking: Mapped[Booking] = relationship("Booking", back_populates="price_snapshot")

    @classmethod
    def compute_hash(cls, payload: dict) -> str:
        """Computes deterministic SHA-256 hash of canonical snapshot payload."""
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class BookingStatusHistory(Base, UUIDPrimaryKeyMixin):
    """
    Append-only auditable log of booking state transitions.
    """

    __tablename__ = "booking_status_history"

    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    from_status: Mapped[BookingStatus | None] = mapped_column(
        Enum(BookingStatus, name="booking_status_enum", native_enum=False),
        nullable=True,
    )
    to_status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus, name="booking_status_enum", native_enum=False),
        nullable=False,
    )
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    actor_role: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    booking: Mapped[Booking] = relationship("Booking", back_populates="status_history")


class PaymentTransaction(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Gateway payment transaction record with idempotency and signature audit.
    """

    __tablename__ = "payment_transactions"

    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    idempotency_key: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    gateway_order_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    gateway_payment_id: Mapped[str | None] = mapped_column(String(100), unique=True, index=True, nullable=True)
    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    payment_method: Mapped[PaymentMethod] = mapped_column(
        Enum(PaymentMethod, name="payment_method_enum", native_enum=False),
        default=PaymentMethod.ONLINE_UPI,
        nullable=False,
    )
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status_enum", native_enum=False),
        default=PaymentStatus.PENDING,
        nullable=False,
        index=True,
    )
    signature: Mapped[str | None] = mapped_column(String(255), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    raw_response: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Relationships
    booking: Mapped[Booking] = relationship("Booking", back_populates="payment_transactions")


class DispatchOffer(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Dispatch offer sent to a candidate nearby professional during auto-dispatch.
    """

    __tablename__ = "dispatch_offers"

    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    professional_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("professional_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[DispatchOfferStatus] = mapped_column(
        Enum(DispatchOfferStatus, name="dispatch_offer_status_enum", native_enum=False),
        default=DispatchOfferStatus.OFFERED,
        nullable=False,
    )
    offered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decline_reason: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Relationships
    booking: Mapped[Booking] = relationship("Booking", back_populates="dispatch_offers")
    professional: Mapped["ProfessionalProfile"] = relationship(  # type: ignore # noqa: F821
        "ProfessionalProfile", foreign_keys=[professional_id]
    )
