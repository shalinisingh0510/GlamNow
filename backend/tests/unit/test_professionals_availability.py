"""
Unit tests for professional availability, slot generation, double-booking prevention,
and geocoding fallback handling.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, ValidationError
from app.integrations.geo import (
    Coordinates,
    HaversineFallbackGeoAdapter,
    MockGoogleMapsAdapter,
    haversine_distance_km,
)
from app.modules.catalog.enums import ServiceTierType, WorkflowType
from app.modules.catalog.models import PricingRule, Service, ServiceCategory, ServiceTier
from app.modules.identity.enums import UserRole
from app.modules.identity.models import User
from app.modules.identity.security import hash_password
from app.modules.professionals.enums import DayOfWeek, SlotStatus, VerificationStatus
from app.modules.professionals.models import (
    AppointmentSlot,
    ProfessionalBlockedDate,
    ProfessionalProfile,
    ProfessionalWorkingHours,
)
from app.modules.professionals.schemas import (
    BlockedDateCreate,
    ProfessionalProfileCreate,
    SlotReservationRequest,
    WorkingHoursItem,
)
from app.modules.professionals.service import ProfessionalService


@pytest.mark.asyncio
async def test_haversine_distance_and_geo_fallback():
    """Verify distance calculation and explicit fallback message when provider fails."""
    # Bengaluru Koramangala to Indiranagar (~5-6 km)
    koramangala = Coordinates(latitude=12.9352, longitude=77.6245)
    indiranagar = Coordinates(latitude=12.9784, longitude=77.6408)

    dist = haversine_distance_km(koramangala, indiranagar)
    assert 4.5 < dist < 6.5

    # Test Live Adapter
    live_adapter = MockGoogleMapsAdapter(simulate_outage=False)
    estimate = await live_adapter.calculate_travel_estimate(koramangala, indiranagar)
    assert not estimate.is_fallback
    assert estimate.distance_km > dist
    assert estimate.duration_minutes >= 15
    assert estimate.fallback_message is None

    # Test Outage Fallback Mode
    outage_adapter = MockGoogleMapsAdapter(simulate_outage=True)
    fallback_estimate = await outage_adapter.calculate_travel_estimate(koramangala, indiranagar)
    assert fallback_estimate.is_fallback
    assert "unreachable" in fallback_estimate.fallback_message or "fallback" in fallback_estimate.fallback_message


@pytest.mark.asyncio
async def test_slot_generation_with_breaks_and_blocked_dates(session: AsyncSession):
    """
    Verify appointment slots are correctly generated based on working hours,
    with lunch break and personal leaves flagged as BLOCKED.
    """
    # Create professional user
    pro_user = User(
        phone="+919876543201",
        email="pro.stylist@example.com",
        full_name="Pooja Sharma",
        role=UserRole.PROFESSIONAL,
        password_hash=hash_password("ProPassword123!"),
        is_active=True,
    )
    session.add(pro_user)
    await session.flush()

    service = ProfessionalService(session)
    profile = await service.create_profile(
        user_id=pro_user.id,
        data=ProfessionalProfileCreate(
            bio="Senior bridal and hair stylist",
            experience_years=8,
            base_zone_name="Koramangala",
            skills=["Bridal Makeup", "Saree Draping"],
        ),
    )

    # Tuesday: 09:00 to 14:00, lunch break 12:00 to 13:00
    await service.set_working_hours(
        professional_id=profile.id,
        hours=[
            WorkingHoursItem(
                day_of_week=DayOfWeek.TUESDAY,
                start_time="09:00",
                end_time="14:00",
                break_start_time="12:00",
                break_end_time="13:00",
                is_working=True,
            )
        ],
        actor_id=pro_user.id,
    )

    # Next Tuesday date
    today = date.today()
    days_ahead = (1 - today.weekday() + 7) % 7
    if days_ahead == 0:
        days_ahead = 7
    target_tuesday = today + timedelta(days=days_ahead)

    # Generate slots (60 mins duration)
    slots = await service.get_or_generate_slots_for_date(
        professional_id=profile.id,
        target_date=target_tuesday,
        slot_duration_minutes=60,
    )

    # Slots: 09:00, 10:00, 11:00, 12:00 (lunch break), 13:00
    assert len(slots) == 5

    # Check that 12:00-13:00 is marked BLOCKED due to lunch break
    lunch_slot = next(s for s in slots if s.start_time.hour == 12)
    assert lunch_slot.status == SlotStatus.BLOCKED

    # Check that 09:00-10:00 is AVAILABLE
    morning_slot = next(s for s in slots if s.start_time.hour == 9)
    assert morning_slot.status == SlotStatus.AVAILABLE


@pytest.mark.asyncio
async def test_double_booking_prevention_and_lock(session: AsyncSession):
    """
    Verify that concurrent or duplicate slot reservation requests are rejected
    with a ConflictError to prevent double booking.
    """
    pro_user = User(
        phone="+919876543202",
        full_name="Anita Tailor",
        role=UserRole.PROFESSIONAL,
        password_hash=hash_password("ProPassword123!"),
    )
    cust1 = User(
        phone="+919876543203",
        full_name="Customer One",
        role=UserRole.CUSTOMER,
        password_hash=hash_password("CustPassword123!"),
    )
    cust2 = User(
        phone="+919876543204",
        full_name="Customer Two",
        role=UserRole.CUSTOMER,
        password_hash=hash_password("CustPassword123!"),
    )
    session.add_all([pro_user, cust1, cust2])
    await session.flush()

    service = ProfessionalService(session)
    profile = await service.create_profile(
        user_id=pro_user.id,
        data=ProfessionalProfileCreate(bio="Master Tailor", experience_years=10),
    )

    # Generate a slot
    now = datetime.now(timezone.utc)
    slot = AppointmentSlot(
        professional_id=profile.id,
        start_time=now + timedelta(days=1),
        end_time=now + timedelta(days=1, hours=1),
        status=SlotStatus.AVAILABLE,
    )
    session.add(slot)
    await session.commit()
    await session.refresh(slot)

    # Customer 1 reserves slot
    res1 = await service.reserve_slot(
        slot_id=slot.id,
        user_id=cust1.id,
        hold_duration_minutes=15,
    )
    assert res1.status == SlotStatus.RESERVED

    # Customer 2 attempts to reserve same slot -> must fail with ConflictError!
    with pytest.raises(ConflictError) as exc_info:
        await service.reserve_slot(
            slot_id=slot.id,
            user_id=cust2.id,
            hold_duration_minutes=15,
        )
    assert "held by another client" in str(exc_info.value.detail.message)


@pytest.mark.asyncio
async def test_expired_reservation_reclaimed(session: AsyncSession):
    """
    Verify that if a client's hold reservation expires, another client
    can safely reserve the slot.
    """
    pro_user = User(
        phone="+919876543205",
        full_name="Rohan Barber",
        role=UserRole.PROFESSIONAL,
        password_hash=hash_password("ProPassword123!"),
    )
    cust1 = User(
        phone="+919876543206",
        full_name="Customer First",
        role=UserRole.CUSTOMER,
        password_hash=hash_password("CustPassword123!"),
    )
    cust2 = User(
        phone="+919876543207",
        full_name="Customer Second",
        role=UserRole.CUSTOMER,
        password_hash=hash_password("CustPassword123!"),
    )
    session.add_all([pro_user, cust1, cust2])
    await session.flush()

    service = ProfessionalService(session)
    profile = await service.create_profile(
        user_id=pro_user.id,
        data=ProfessionalProfileCreate(bio="Men's Grooming Expert"),
    )

    # Create slot with expired reservation
    now = datetime.now(timezone.utc)
    slot = AppointmentSlot(
        professional_id=profile.id,
        start_time=now + timedelta(days=2),
        end_time=now + timedelta(days=2, hours=1),
        status=SlotStatus.RESERVED,
        reserved_by_user_id=cust1.id,
        reservation_expires_at=now - timedelta(minutes=5),  # expired 5 mins ago
    )
    session.add(slot)
    await session.commit()
    await session.refresh(slot)

    # Customer 2 should successfully acquire the expired slot
    res2 = await service.reserve_slot(
        slot_id=slot.id,
        user_id=cust2.id,
        hold_duration_minutes=15,
    )
    assert res2.status == SlotStatus.RESERVED
    assert slot.reserved_by_user_id == cust2.id
