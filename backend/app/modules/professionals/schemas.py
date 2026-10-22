"""
Pydantic schemas for professional onboarding, discovery, portfolios, and slot availability.
"""

from __future__ import annotations

from datetime import date, datetime
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.modules.catalog.enums import ServiceTierType
from app.modules.professionals.enums import DayOfWeek, SlotStatus, VerificationStatus


class SkillSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str = Field(..., max_length=100)


class ServiceOfferingCreate(BaseModel):
    service_id: uuid.UUID
    tier_type: ServiceTierType
    custom_price_paise: int | None = Field(None, ge=0)
    is_active: bool = True


class ServiceOfferingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    service_id: uuid.UUID
    tier_type: ServiceTierType
    custom_price_paise: int | None
    is_active: bool


class PortfolioItemCreate(BaseModel):
    title: str = Field(..., max_length=150)
    description: str | None = None
    image_url: str = Field(..., max_length=500)
    service_id: uuid.UUID | None = None


class PortfolioItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    description: str | None
    image_url: str
    service_id: uuid.UUID | None
    is_verified: bool


class WorkingHoursItem(BaseModel):
    day_of_week: DayOfWeek
    start_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    end_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    break_start_time: str | None = Field(None, pattern=r"^\d{2}:\d{2}$")
    break_end_time: str | None = Field(None, pattern=r"^\d{2}:\d{2}$")
    is_working: bool = True


class WorkingHoursResponse(WorkingHoursItem):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


class BlockedDateCreate(BaseModel):
    start_datetime: datetime
    end_datetime: datetime
    reason: str = Field("Personal Leave", max_length=200)


class BlockedDateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    start_datetime: datetime
    end_datetime: datetime
    reason: str


class AppointmentSlotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    professional_id: uuid.UUID
    start_time: datetime
    end_time: datetime
    status: SlotStatus
    reservation_expires_at: datetime | None = None


class ProfessionalProfileCreate(BaseModel):
    bio: str = Field("", max_length=2000)
    experience_years: int = Field(1, ge=0, le=50)
    base_zone_name: str = Field("Koramangala, Bengaluru", max_length=100)
    latitude: float = Field(12.9352, ge=-90.0, le=90.0)
    longitude: float = Field(77.6245, ge=-180.0, le=180.0)
    service_radius_km: float = Field(15.0, gt=0, le=100)
    is_accepting_instant_bookings: bool = True
    skills: list[str] = Field(default_factory=list)


class ProfessionalProfileUpdate(BaseModel):
    bio: str | None = Field(None, max_length=2000)
    experience_years: int | None = Field(None, ge=0, le=50)
    base_zone_name: str | None = Field(None, max_length=100)
    latitude: float | None = Field(None, ge=-90.0, le=90.0)
    longitude: float | None = Field(None, ge=-180.0, le=180.0)
    service_radius_km: float | None = Field(None, gt=0, le=100)
    is_accepting_instant_bookings: bool | None = None


class ProfessionalDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    user_id: uuid.UUID
    full_name: str
    phone: str
    bio: str
    experience_years: int
    verification_status: VerificationStatus
    rating: float
    review_count: int
    is_active: bool
    is_accepting_instant_bookings: bool
    latitude: float
    longitude: float
    service_radius_km: float
    base_zone_name: str
    skills: list[str] = Field(default_factory=list)
    service_offerings: list[ServiceOfferingResponse] = Field(default_factory=list)
    portfolios: list[PortfolioItemResponse] = Field(default_factory=list)
    working_hours: list[WorkingHoursResponse] = Field(default_factory=list)


class ProfessionalCardResponse(BaseModel):
    """Card item displayed in professional discovery & booking picker."""
    id: uuid.UUID
    user_id: uuid.UUID
    full_name: str
    bio: str
    experience_years: int
    verification_status: VerificationStatus
    rating: float
    review_count: int
    is_accepting_instant_bookings: bool
    base_zone_name: str
    distance_km: float | None = None
    estimated_arrival_minutes: int | None = None
    is_fallback_location: bool = False
    fallback_message: str | None = None
    skills: list[str] = Field(default_factory=list)
    tier_prices: dict[str, int] = Field(default_factory=dict)  # {"BASIC": 79900, "STANDARD": 129900, ...}
    portfolio_samples: list[str] = Field(default_factory=list)
    available_slots_count: int = 0


class SlotReservationRequest(BaseModel):
    service_id: uuid.UUID | None = None
    hold_duration_minutes: int = Field(15, ge=5, le=30)


class SlotReservationResponse(BaseModel):
    slot_id: uuid.UUID
    professional_id: uuid.UUID
    start_time: datetime
    end_time: datetime
    status: SlotStatus
    reservation_expires_at: datetime
    message: str


class AdminVerificationUpdate(BaseModel):
    verification_status: VerificationStatus
