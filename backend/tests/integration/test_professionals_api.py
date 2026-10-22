"""
Integration tests for professionals discovery, onboarding, portfolio,
schedules, and transaction-safe slot reservation.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.geo import MockGoogleMapsAdapter, set_geo_provider
from app.modules.catalog.enums import ServiceTierType, WorkflowType
from app.modules.catalog.models import PricingRule, Service, ServiceCategory, ServiceTier
from app.modules.identity.enums import UserRole
from app.modules.identity.models import User
from app.modules.identity.security import create_access_token, hash_password
from app.modules.professionals.enums import DayOfWeek, SlotStatus, VerificationStatus


@pytest.fixture
async def setup_data(session: AsyncSession):
    now = datetime.now(timezone.utc)

    # 1. Admin User
    admin = User(
        phone="+919999900001",
        email="admin@glamnow.com",
        full_name="Admin Boss",
        role=UserRole.ADMIN,
        password_hash=hash_password("AdminPass123!"),
    )
    # 2. Professional User
    pro = User(
        phone="+919999900002",
        email="shreya.stylist@glamnow.com",
        full_name="Shreya Sen",
        role=UserRole.PROFESSIONAL,
        password_hash=hash_password("ProPass123!"),
    )
    # 3. Customer User
    customer = User(
        phone="+919999900003",
        email="priya.client@glamnow.com",
        full_name="Priya Client",
        role=UserRole.CUSTOMER,
        password_hash=hash_password("CustPass123!"),
    )
    # 4. Another Customer
    customer2 = User(
        phone="+919999900004",
        email="sneha.client@glamnow.com",
        full_name="Sneha Client",
        role=UserRole.CUSTOMER,
        password_hash=hash_password("CustPass123!"),
    )

    # Catalog Category & Service
    cat = ServiceCategory(
        slug="beauty",
        name="Beauty & Wellness",
        description="Grooming and facial treatments",
        icon="✨",
        display_order=1,
        is_active=True,
    )
    session.add_all([admin, pro, customer, customer2, cat])
    await session.flush()

    srv = Service(
        category_id=cat.id,
        slug="glow-facial",
        name="Glow Facial",
        description="Radiant organic facial",
        workflow_type=WorkflowType.AT_HOME_VISIT,
        is_active=True,
    )
    session.add(srv)
    await session.flush()

    tier_basic = ServiceTier(
        service_id=srv.id,
        tier=ServiceTierType.BASIC,
        name="Basic Glow",
        description="Cleanse & steam",
        brands="Lotus / Aroma Magic",
        duration_minutes=45,
        inclusions=["Cleansing", "Steam"],
        exclusions=["Eye mask"],
    )
    tier_premium = ServiceTier(
        service_id=srv.id,
        tier=ServiceTierType.PREMIUM,
        name="Luxury Gold Glow",
        description="24K gold serum facial",
        brands="Kama Ayurveda / Forest Essentials",
        duration_minutes=75,
        inclusions=["Gold facial", "Eye mask", "Head massage"],
        exclusions=[],
    )
    session.add_all([tier_basic, tier_premium])
    await session.flush()

    rule1 = PricingRule(
        tier_id=tier_basic.id,
        base_price_paise=79900,
        effective_from=now - timedelta(days=1),
        is_active=True,
    )
    rule2 = PricingRule(
        tier_id=tier_premium.id,
        base_price_paise=199900,
        effective_from=now - timedelta(days=1),
        is_active=True,
    )
    session.add_all([rule1, rule2])
    await session.commit()

    return {
        "admin": admin,
        "pro": pro,
        "customer": customer,
        "customer2": customer2,
        "service": srv,
        "tier_basic": tier_basic,
        "tier_premium": tier_premium,
    }


def auth_header(user: User) -> dict[str, str]:
    token, _ = create_access_token(user.id, user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_professional_onboarding_and_profile_flow(
    client: AsyncClient, setup_data: dict
):
    """Test creating professional profile, setting working hours, and portfolio."""
    pro = setup_data["pro"]
    headers = auth_header(pro)

    # 1. Onboarding: Create Profile
    res = await client.post(
        "/api/v1/professionals/profile",
        json={
            "bio": "Certified cosmetologist with 6 years experience in luxury skincare.",
            "experience_years": 6,
            "base_zone_name": "Indiranagar, Bengaluru",
            "latitude": 12.9784,
            "longitude": 77.6408,
            "service_radius_km": 12.0,
            "is_accepting_instant_bookings": True,
            "skills": ["Glow Facial", "Bridal Makeup", "Nail Art"],
        },
        headers=headers,
    )
    assert res.status_code == 201
    pro_data = res.json()
    prof_id = pro_data["id"]
    assert pro_data["experience_years"] == 6
    assert "Bridal Makeup" in pro_data["skills"]
    assert pro_data["verification_status"] == VerificationStatus.PENDING.value

    # 2. Add Portfolio Item
    res_port = await client.post(
        f"/api/v1/professionals/{prof_id}/portfolio",
        json={
            "title": "Bridal Golden Glow Transformation",
            "description": "Pre-wedding glowing skin treatment",
            "image_url": "https://images.unsplash.com/photo-1560066984-138dadb4c035",
            "service_id": str(setup_data["service"].id),
        },
        headers=headers,
    )
    assert res_port.status_code == 201
    assert res_port.json()["title"] == "Bridal Golden Glow Transformation"

    # 3. Add Custom Service Offering Price Override (e.g. ₹2199 instead of ₹1999)
    res_offer = await client.post(
        f"/api/v1/professionals/{prof_id}/offerings",
        json={
            "service_id": str(setup_data["service"].id),
            "tier_type": ServiceTierType.PREMIUM.value,
            "custom_price_paise": 219900,
            "is_active": True,
        },
        headers=headers,
    )
    assert res_offer.status_code == 201
    assert res_offer.json()["custom_price_paise"] == 219900

    # 4. Admin Verifies the Professional
    admin = setup_data["admin"]
    res_verify = await client.patch(
        f"/api/v1/professionals/{prof_id}/verification",
        json={"verification_status": VerificationStatus.VERIFIED.value},
        headers=auth_header(admin),
    )
    assert res_verify.status_code == 200
    assert res_verify.json()["verification_status"] == VerificationStatus.VERIFIED.value

    # 5. Non-admin attempting verification modification -> 403 Forbidden
    res_unauth = await client.patch(
        f"/api/v1/professionals/{prof_id}/verification",
        json={"verification_status": VerificationStatus.REJECTED.value},
        headers=auth_header(pro),
    )
    assert res_unauth.status_code == 403


@pytest.mark.asyncio
async def test_professional_discovery_with_filters_and_fallback(
    client: AsyncClient, setup_data: dict
):
    """Test searching professionals with skill, rating, price filters and ETA fallback."""
    pro = setup_data["pro"]
    headers = auth_header(pro)

    # Create profile
    res_create = await client.post(
        "/api/v1/professionals/profile",
        json={
            "bio": "Specialist in bridal facials and skincare.",
            "experience_years": 8,
            "base_zone_name": "Koramangala, Bengaluru",
            "latitude": 12.9352,
            "longitude": 77.6245,
            "service_radius_km": 15.0,
            "skills": ["Bridal Facial", "Saree Draping"],
        },
        headers=headers,
    )
    prof_id = res_create.json()["id"]

    # Link offering to service
    await client.post(
        f"/api/v1/professionals/{prof_id}/offerings",
        json={
            "service_id": str(setup_data["service"].id),
            "tier_type": ServiceTierType.BASIC.value,
            "custom_price_paise": 85000,
        },
        headers=headers,
    )

    # 1. Search with matching skill
    res_skill = await client.get("/api/v1/professionals/search?skill=Bridal")
    assert res_skill.status_code == 200
    results = res_skill.json()
    assert len(results) >= 1
    assert any(r["id"] == prof_id for r in results)

    # 2. Search with non-matching skill -> empty list
    res_none = await client.get("/api/v1/professionals/search?skill=NailExtensionSpecialist")
    assert res_none.status_code == 200
    assert len(res_none.json()) == 0

    # 3. Search with customer coordinates and normal map provider
    set_geo_provider(MockGoogleMapsAdapter(simulate_outage=False))
    res_geo = await client.get(
        "/api/v1/professionals/search?customer_lat=12.9300&customer_lng=77.6200"
    )
    assert res_geo.status_code == 200
    geo_results = res_geo.json()
    assert len(geo_results) >= 1
    matched = next(r for r in geo_results if r["id"] == prof_id)
    assert matched["distance_km"] is not None
    assert matched["estimated_arrival_minutes"] is not None
    assert not matched["is_fallback_location"]

    # 4. Search with customer coordinates during simulated map outage -> explicit fallback notice
    set_geo_provider(MockGoogleMapsAdapter(simulate_outage=True))
    res_outage = await client.get(
        "/api/v1/professionals/search?customer_lat=12.9300&customer_lng=77.6200"
    )
    assert res_outage.status_code == 200
    outage_results = res_outage.json()
    outage_matched = next(r for r in outage_results if r["id"] == prof_id)
    assert outage_matched["is_fallback_location"] is True
    assert "fallback" in outage_matched["fallback_message"].lower() or "unreachable" in outage_matched["fallback_message"].lower()

    # Reset geo provider
    set_geo_provider(MockGoogleMapsAdapter(simulate_outage=False))


@pytest.mark.asyncio
async def test_slot_fetching_and_atomic_reservation(
    client: AsyncClient, setup_data: dict
):
    """Test getting slots for date and concurrent reservation prevention."""
    pro = setup_data["pro"]
    cust1 = setup_data["customer"]
    cust2 = setup_data["customer2"]

    # Create profile
    res_create = await client.post(
        "/api/v1/professionals/profile",
        json={"bio": "Stylist", "experience_years": 5},
        headers=auth_header(pro),
    )
    prof_id = res_create.json()["id"]

    # Target date: next Monday
    today = date.today()
    days_ahead = (0 - today.weekday() + 7) % 7
    if days_ahead == 0:
        days_ahead = 7
    target_date = today + timedelta(days=days_ahead)

    # Get slots for target date
    res_slots = await client.get(
        f"/api/v1/professionals/{prof_id}/slots?target_date={target_date.isoformat()}"
    )
    assert res_slots.status_code == 200
    slots = res_slots.json()
    assert len(slots) > 0

    available_slot = next(s for s in slots if s["status"] == SlotStatus.AVAILABLE.value)
    slot_id = available_slot["id"]

    # Customer 1 reserves slot
    res_res1 = await client.post(
        f"/api/v1/professionals/reserve-slot/{slot_id}",
        json={"hold_duration_minutes": 15},
        headers=auth_header(cust1),
    )
    assert res_res1.status_code == 200
    assert res_res1.json()["status"] == SlotStatus.RESERVED.value

    # Customer 2 attempts to reserve same slot -> 409 Conflict
    res_res2 = await client.post(
        f"/api/v1/professionals/reserve-slot/{slot_id}",
        json={"hold_duration_minutes": 15},
        headers=auth_header(cust2),
    )
    assert res_res2.status_code == 409
    assert res_res2.json()["errors"][0]["code"] == "CONFLICT"

    # Customer 1 releases the slot
    res_rel = await client.post(
        f"/api/v1/professionals/release-slot/{slot_id}",
        headers=auth_header(cust1),
    )
    assert res_rel.status_code == 200
    assert res_rel.json()["released"] is True

    # Customer 2 now successfully reserves it
    res_res3 = await client.post(
        f"/api/v1/professionals/reserve-slot/{slot_id}",
        json={"hold_duration_minutes": 15},
        headers=auth_header(cust2),
    )
    assert res_res3.status_code == 200
    assert res_res3.json()["status"] == SlotStatus.RESERVED.value
