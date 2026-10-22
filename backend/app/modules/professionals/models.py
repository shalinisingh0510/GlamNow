"""
Professional and availability domain ORM models.
"""

from __future__ import annotations

from datetime import datetime
import uuid

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.modules.catalog.enums import ServiceTierType
from app.modules.professionals.enums import DayOfWeek, SlotStatus, VerificationStatus


class ProfessionalProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Independent profile for service professionals / stylists / tailors.
    """

    __tablename__ = "professional_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    bio: Mapped[str] = mapped_column(Text, nullable=False, default="")
    experience_years: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    verification_status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus, name="verification_status_enum", native_enum=False),
        default=VerificationStatus.PENDING,
        nullable=False,
        index=True,
    )
    rating: Mapped[float] = mapped_column(Float, default=5.0, nullable=False)
    review_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_accepting_instant_bookings: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, default=12.9352, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, default=77.6245, nullable=False)
    service_radius_km: Mapped[float] = mapped_column(Float, default=15.0, nullable=False)
    base_zone_name: Mapped[str] = mapped_column(String(100), default="Koramangala, Bengaluru", nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])  # type: ignore # noqa: F821
    skills: Mapped[list[ProfessionalSkill]] = relationship(
        "ProfessionalSkill", back_populates="professional", cascade="all, delete-orphan"
    )
    service_offerings: Mapped[list[ProfessionalServiceOffering]] = relationship(
        "ProfessionalServiceOffering", back_populates="professional", cascade="all, delete-orphan"
    )
    portfolios: Mapped[list[ProfessionalPortfolio]] = relationship(
        "ProfessionalPortfolio", back_populates="professional", cascade="all, delete-orphan"
    )
    working_hours: Mapped[list[ProfessionalWorkingHours]] = relationship(
        "ProfessionalWorkingHours", back_populates="professional", cascade="all, delete-orphan"
    )
    blocked_dates: Mapped[list[ProfessionalBlockedDate]] = relationship(
        "ProfessionalBlockedDate", back_populates="professional", cascade="all, delete-orphan"
    )
    appointment_slots: Mapped[list[AppointmentSlot]] = relationship(
        "AppointmentSlot", back_populates="professional", cascade="all, delete-orphan"
    )


class ProfessionalSkill(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Specific verified skills / specialities (e.g. 'Bridal Makeup', 'Silk Saree Draping').
    """

    __tablename__ = "professional_skills"

    professional_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("professional_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Relationships
    professional: Mapped[ProfessionalProfile] = relationship(
        "ProfessionalProfile", back_populates="skills"
    )


class ProfessionalServiceOffering(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Tier-specific service eligibility and optional price overrides.

    Allows separating professional service eligibility from general catalog eligibility,
    and supports independent pricing per professional tier.
    """

    __tablename__ = "professional_service_offerings"

    professional_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("professional_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("services.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tier_type: Mapped[ServiceTierType] = mapped_column(
        Enum(ServiceTierType, name="service_tier_type_enum", native_enum=False),
        nullable=False,
    )
    custom_price_paise: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "professional_id",
            "service_id",
            "tier_type",
            name="uq_prof_service_tier",
        ),
    )

    # Relationships
    professional: Mapped[ProfessionalProfile] = relationship(
        "ProfessionalProfile", back_populates="service_offerings"
    )
    service: Mapped["Service"] = relationship("Service", foreign_keys=[service_id])  # type: ignore # noqa: F821


class ProfessionalPortfolio(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Authentic portfolio images showcasing past client styling or tailoring work.
    """

    __tablename__ = "professional_portfolios"

    professional_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("professional_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    service_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("services.id", ondelete="SET NULL"), nullable=True
    )
    is_verified: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    professional: Mapped[ProfessionalProfile] = relationship(
        "ProfessionalProfile", back_populates="portfolios"
    )


class ProfessionalWorkingHours(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Weekly working schedule with shift hours and meal/commute breaks.
    """

    __tablename__ = "professional_working_hours"

    professional_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("professional_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    day_of_week: Mapped[DayOfWeek] = mapped_column(
        Enum(DayOfWeek, name="day_of_week_enum", native_enum=False),
        nullable=False,
    )
    start_time: Mapped[str] = mapped_column(String(5), default="09:00", nullable=False)  # "HH:MM"
    end_time: Mapped[str] = mapped_column(String(5), default="19:00", nullable=False)    # "HH:MM"
    break_start_time: Mapped[str | None] = mapped_column(String(5), default="13:00", nullable=True)
    break_end_time: Mapped[str | None] = mapped_column(String(5), default="14:00", nullable=True)
    is_working: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("professional_id", "day_of_week", name="uq_prof_day_working_hours"),
    )

    # Relationships
    professional: Mapped[ProfessionalProfile] = relationship(
        "ProfessionalProfile", back_populates="working_hours"
    )


class ProfessionalBlockedDate(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Blocked dates or times for holidays, illness, or emergency leave.
    """

    __tablename__ = "professional_blocked_dates"

    professional_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("professional_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    start_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reason: Mapped[str] = mapped_column(String(200), default="Personal Time Off", nullable=False)

    # Relationships
    professional: Mapped[ProfessionalProfile] = relationship(
        "ProfessionalProfile", back_populates="blocked_dates"
    )


class AppointmentSlot(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Concrete appointment time slot for booking.

    Double-booking prevention is strictly enforced via database constraint
    on (professional_id, start_time) and atomic reservation transactions.
    """

    __tablename__ = "appointment_slots"

    professional_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("professional_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[SlotStatus] = mapped_column(
        Enum(SlotStatus, name="slot_status_enum", native_enum=False),
        default=SlotStatus.AVAILABLE,
        nullable=False,
        index=True,
    )
    reserved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reservation_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    service_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("services.id", ondelete="SET NULL"), nullable=True
    )

    __table_args__ = (
        UniqueConstraint("professional_id", "start_time", name="uq_professional_slot_start"),
        Index("ix_slot_prof_status_start", "professional_id", "status", "start_time"),
    )

    # Relationships
    professional: Mapped[ProfessionalProfile] = relationship(
        "ProfessionalProfile", back_populates="appointment_slots"
    )
