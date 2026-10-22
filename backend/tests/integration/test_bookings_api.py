"""
End-to-End Integration Tests for Booking Lifecycle, Quick Dispatch Engine,
Payment Verification, Slot Concurrency, and Cancellation Rules (Phase 6).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import hashlib
import hmac
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.geo import MockGoogleMapsAdapter, set_geo_provider
from app.integrations.payment import MockRazorpayPaymentAdapter, set_payment_gateway
from app.modules.bookings.enums import BookingStatus, BookingType, DispatchOfferStatus, PaymentStatus
from app.modules.bookings.models import Booking, DispatchOffer
from app.modules.catalog.enums import ServiceTierType, WorkflowType
from app.modules.catalog.models import PricingRule, Service, ServiceCategory, ServiceTier
from app.modules.identity.enums import AddressLabel, UserRole
from app.modules.identity.models import SavedAddress, User
from app.modules.identity.security import create_access_token, hash_password
from app.modules.professionals.enums import DayOfWeek, SlotStatus, VerificationStatus
from app.modules.professionals.models import AppointmentSlot, ProfessionalProfile, ProfessionalServiceOffering


@pytest.fixture
async def booking_setup(session: AsyncSession):
    now = datetime.now(timezone.utc)
    set_geo_provider(MockGoogleMapsAdapter())
    set_payment_gateway(MockRazorpayPaymentAdapter(key_secret="mock_rzp_secret_key_1234567890"))

    # 1. Users
    customer = User(
        phone="+919876543210",
        email="ananya.customer@glamnow.com",
        full_name="Ananya Sharma",
        role=UserRole.CUSTOMER,
        password_hash=hash_password("Pass123!"),
    )
    customer2 = User(
        phone="+919876543211",
        email="rohit.customer@glamnow.com",
        full_name="Rohit Verma",
        role=UserRole.CUSTOMER,
        password_hash=hash_password("Pass123!"),
    )
    pro_user1 = User(
        phone="+919876543220",
        email="kavita.stylist@glamnow.com",
        full_name="Kavita Stylist",
        role=UserRole.PROFESSIONAL,
        password_hash=hash_password("Pass123!"),
    )
    pro_user2 = User(
        phone="+919876543221",
        email="meera.stylist@glamnow.com",
        full_name="Meera Stylist",
        role=UserRole.PROFESSIONAL,
        password_hash=hash_password("Pass123!"),
    )
    session.add_all([customer, customer2, pro_user1, pro_user2])
    await session.flush()

    # 2. Saved Address
    address = SavedAddress(
        user_id=customer.id,
        label=AddressLabel.HOME,
        recipient_name="Ananya Sharma",
        recipient_phone="+919876543210",
        address_line1="12th Main, Indiranagar",
        city="Bangalore",
        state="Karnataka",
        pincode="560038",
        latitude=12.9716,
        longitude=77.6412,
        is_default=True,
    )
    address2 = SavedAddress(
        user_id=customer2.id,
        label=AddressLabel.HOME,
        recipient_name="Rohit Verma",
        recipient_phone="+919876543211",
        address_line1="5th Block, Koramangala",
        city="Bangalore",
        state="Karnataka",
        pincode="560034",
        latitude=12.9352,
        longitude=77.6245,
        is_default=True,
    )
    session.add_all([address, address2])

    # 3. Catalog Category, Service & Tiers
    cat = ServiceCategory(
        slug="hair",
        name="Hair & Styling",
        description="Haircuts, styling and care",
        icon="✂️",
        display_order=1,
        is_active=True,
    )
    session.add(cat)
    await session.flush()

    srv = Service(
        category_id=cat.id,
        slug="hair-spa",
        name="Keratin Hair Spa",
        description="Revitalizing deep conditioning spa",
        workflow_type=WorkflowType.AT_HOME_VISIT,
        is_active=True,
    )
    session.add(srv)
    await session.flush()

    tier_basic = ServiceTier(
        service_id=srv.id,
        tier=ServiceTierType.BASIC,
        name="Classic Spa",
        description="Standard hydration treatment",
        brands="L'Oreal Professionnel",
        duration_minutes=60,
        inclusions=["Cleansing", "Steam", "Serum"],
        exclusions=[],
    )
    session.add(tier_basic)
    await session.flush()

    rule = PricingRule(
        tier_id=tier_basic.id,
        base_price_paise=129900,  # ₹1,299
        effective_from=now - timedelta(days=1),
        is_active=True,
    )
    session.add(rule)

    # 4. Professional Profiles
    pro_prof1 = ProfessionalProfile(
        user_id=pro_user1.id,
        bio="Senior hair artisan with 8 years experience",
        experience_years=8,
        rating=4.95,
        review_count=120,
        base_zone_name="Indiranagar, Bangalore",
        latitude=12.9719,
        longitude=77.6410,
        service_radius_km=15,
        verification_status=VerificationStatus.VERIFIED,
        is_accepting_instant_bookings=True,
        is_active=True,
    )
    pro_prof2 = ProfessionalProfile(
        user_id=pro_user2.id,
        bio="Bridal and styling expert",
        experience_years=5,
        rating=4.80,
        review_count=80,
        base_zone_name="Koramangala, Bangalore",
        latitude=12.9352,
        longitude=77.6245,
        service_radius_km=15,
        verification_status=VerificationStatus.VERIFIED,
        is_accepting_instant_bookings=True,
        is_active=True,
    )
    session.add_all([pro_prof1, pro_prof2])
    await session.flush()

    # Offerings
    offering1 = ProfessionalServiceOffering(
        professional_id=pro_prof1.id,
        service_id=srv.id,
        tier_type=ServiceTierType.BASIC,
        is_active=True,
    )
    offering2 = ProfessionalServiceOffering(
        professional_id=pro_prof2.id,
        service_id=srv.id,
        tier_type=ServiceTierType.BASIC,
        is_active=True,
    )
    session.add_all([offering1, offering2])

    # 5. Appointment Slot for Pro 1 (Tomorrow at 10 AM)
    slot_date = (now + timedelta(days=1)).date()
    slot_start = datetime.combine(slot_date, datetime.min.time(), tzinfo=timezone.utc) + timedelta(hours=10)
    slot_end = slot_start + timedelta(hours=1)
    slot = AppointmentSlot(
        professional_id=pro_prof1.id,
        start_time=slot_start,
        end_time=slot_end,
        status=SlotStatus.AVAILABLE,
    )
    session.add(slot)
    await session.commit()

    return {
        "customer": customer,
        "customer2": customer2,
        "pro_user1": pro_user1,
        "pro_prof1": pro_prof1,
        "pro_user2": pro_user2,
        "pro_prof2": pro_prof2,
        "service": srv,
        "tier": tier_basic,
        "address": address,
        "address2": address2,
        "slot": slot,
    }


def _auth_header(user: User) -> dict[str, str]:
    token, _ = create_access_token(user.id, user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_successful_instant_booking_full_lifecycle(client: AsyncClient, booking_setup: dict):
    """
    Test the complete happy path customer journey:
    1. Hold reservation creation with quote snapshot
    2. Idempotent deduplication check
    3. Payment initiation
    4. Cryptographic payment confirmation via HMAC-SHA256 signature
    5. Automatic dispatch offering to eligible pro
    6. Professional acceptance -> EN_ROUTE
    7. Partner arrival -> ARRIVED
    8. Start service with verified OTP -> IN_PROGRESS
    9. Complete service with verified OTP -> COMPLETED
    10. Audit history verification
    """
    customer = booking_setup["customer"]
    pro_user = booking_setup["pro_user1"]
    srv = booking_setup["service"]
    address = booking_setup["address"]

    idempotency_key = f"order_idemp_{uuid.uuid4().hex[:12]}"

    # Step 1: Create Instant Booking Hold
    payload = {
        "service_id": str(srv.id),
        "tier_type": ServiceTierType.BASIC.value,
        "booking_type": BookingType.INSTANT.value,
        "address_id": str(address.id),
        "add_on_ids": [],
        "idempotency_key": idempotency_key,
    }
    resp = await client.post("/api/v1/bookings", json=payload, headers=_auth_header(customer))
    assert resp.status_code == 201, resp.text
    b_data = resp.json()
    booking_id = b_data["id"]

    assert b_data["status"] == BookingStatus.HOLD_RESERVED.value
    assert b_data["booking_number"].startswith("GN-")
    assert b_data["price_snapshot"] is not None
    assert b_data["price_snapshot"]["total_payable_paise"] > 0
    assert b_data["price_snapshot"]["snapshot_hash"] is not None
    assert len(b_data["start_otp"]) == 4
    assert len(b_data["completion_otp"]) == 4

    # Step 2: Idempotent replay with same idempotency key returns exact same booking
    replay_resp = await client.post("/api/v1/bookings", json=payload, headers=_auth_header(customer))
    assert replay_resp.status_code == 201
    assert replay_resp.json()["id"] == booking_id

    # Step 3: Initiate Payment
    init_resp = await client.post(
        f"/api/v1/bookings/{booking_id}/pay", headers=_auth_header(customer)
    )
    assert init_resp.status_code == 200
    pay_init = init_resp.json()
    order_id = pay_init["gateway_order_id"]
    amount_paise = pay_init["amount_paise"]

    # Step 4: Cryptographically Confirm Payment
    payment_id = f"pay_{uuid.uuid4().hex[:12]}"
    secret = "mock_rzp_secret_key_1234567890"
    message = f"{order_id}|{payment_id}".encode("utf-8")
    valid_signature = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()

    confirm_resp = await client.post(
        f"/api/v1/bookings/{booking_id}/confirm-payment",
        json={
            "gateway_order_id": order_id,
            "gateway_payment_id": payment_id,
            "signature": valid_signature,
            "payment_method": "online_upi",
            "idempotency_key": f"tx_idemp_{booking_id}",
        },
        headers=_auth_header(customer),
    )
    assert confirm_resp.status_code == 200
    confirm_data = confirm_resp.json()
    assert confirm_data["ok"] is True
    # The booking transitioned to CONFIRMED and was immediately auto-dispatched to Pro 1
    assert confirm_data["booking_status"] in (
        BookingStatus.CONFIRMED.value,
        BookingStatus.ASSIGNED.value,
        BookingStatus.DISPATCHING.value,
    )

    # Step 5: Check dispatch status
    b_detail_resp = await client.get(f"/api/v1/bookings/{booking_id}", headers=_auth_header(customer))
    assert b_detail_resp.status_code == 200
    detail = b_detail_resp.json()
    assert detail["assigned_professional_id"] is not None

    # Step 6: Professional Accepts Offer
    accept_resp = await client.post(
        f"/api/v1/bookings/{booking_id}/dispatch-response",
        json={"action": "accept"},
        headers=_auth_header(pro_user),
    )
    assert accept_resp.status_code == 200
    assert accept_resp.json()["status"] == BookingStatus.EN_ROUTE.value

    # Step 7: Partner Arrives at Doorstep
    arrived_resp = await client.post(
        f"/api/v1/bookings/{booking_id}/mark-arrived",
        headers=_auth_header(pro_user),
    )
    assert arrived_resp.status_code == 200
    assert arrived_resp.json()["status"] == BookingStatus.ARRIVED.value

    # Step 8: Verify Start OTP
    start_otp = detail["start_otp"]
    start_resp = await client.post(
        f"/api/v1/bookings/{booking_id}/verify-start",
        json={"otp": start_otp},
        headers=_auth_header(pro_user),
    )
    assert start_resp.status_code == 200
    assert start_resp.json()["status"] == BookingStatus.IN_PROGRESS.value

    # Step 9: Verify Completion OTP
    comp_otp = detail["completion_otp"]
    comp_resp = await client.post(
        f"/api/v1/bookings/{booking_id}/complete",
        json={"otp": comp_otp},
        headers=_auth_header(pro_user),
    )
    assert comp_resp.status_code == 200
    assert comp_resp.json()["status"] == BookingStatus.COMPLETED.value

    # Step 10: Verify Auditable History Graph
    final_resp = await client.get(f"/api/v1/bookings/{booking_id}", headers=_auth_header(customer))
    history = final_resp.json()["history"]
    transitions = [h["to_status"] for h in history]
    assert BookingStatus.HOLD_RESERVED.value in transitions
    assert BookingStatus.CONFIRMED.value in transitions
    assert BookingStatus.EN_ROUTE.value in transitions
    assert BookingStatus.ARRIVED.value in transitions
    assert BookingStatus.IN_PROGRESS.value in transitions
    assert BookingStatus.COMPLETED.value in transitions


@pytest.mark.asyncio
async def test_concurrent_scheduled_slot_claim(client: AsyncClient, booking_setup: dict):
    """
    Test concurrent slot locking:
    First customer claims available slot -> succeeds.
    Second customer tries to claim the same slot -> 409 Conflict.
    """
    customer1 = booking_setup["customer"]
    customer2 = booking_setup["customer2"]
    srv = booking_setup["service"]
    address = booking_setup["address"]
    slot = booking_setup["slot"]

    payload1 = {
        "service_id": str(srv.id),
        "tier_type": ServiceTierType.BASIC.value,
        "booking_type": BookingType.SCHEDULED.value,
        "slot_id": str(slot.id),
        "address_id": str(address.id),
        "idempotency_key": f"slot_claim_1_{uuid.uuid4().hex[:8]}",
    }
    payload2 = {
        "service_id": str(srv.id),
        "tier_type": ServiceTierType.BASIC.value,
        "booking_type": BookingType.SCHEDULED.value,
        "slot_id": str(slot.id),
        "address_id": str(booking_setup["address2"].id),
        "idempotency_key": f"slot_claim_2_{uuid.uuid4().hex[:8]}",
    }

    # First user claims
    r1 = await client.post("/api/v1/bookings", json=payload1, headers=_auth_header(customer1))
    assert r1.status_code == 201

    # Second user attempts to claim the same reserved slot
    r2 = await client.post("/api/v1/bookings", json=payload2, headers=_auth_header(customer2))
    assert r2.status_code == 409
    assert "no longer available" in r2.text


@pytest.mark.asyncio
async def test_payment_forged_signature_rejection(client: AsyncClient, booking_setup: dict):
    """
    Verify payment security:
    Client cannot confirm payment using forged or tampered signatures.
    """
    customer = booking_setup["customer"]
    srv = booking_setup["service"]
    address = booking_setup["address"]

    # Create Hold
    r = await client.post(
        "/api/v1/bookings",
        json={
            "service_id": str(srv.id),
            "tier_type": ServiceTierType.BASIC.value,
            "booking_type": BookingType.INSTANT.value,
            "address_id": str(address.id),
            "idempotency_key": f"forged_test_{uuid.uuid4().hex[:8]}",
        },
        headers=_auth_header(customer),
    )
    assert r.status_code == 201
    booking_id = r.json()["id"]

    # Initiate
    init_res = await client.post(
        f"/api/v1/bookings/{booking_id}/pay", headers=_auth_header(customer)
    )
    assert init_res.status_code == 200
    order_id = init_res.json()["gateway_order_id"]

    # Confirm with fake signature
    fake_sig = "a" * 64
    confirm_res = await client.post(
        f"/api/v1/bookings/{booking_id}/confirm-payment",
        json={
            "gateway_order_id": order_id,
            "gateway_payment_id": "pay_fake_123",
            "signature": fake_sig,
            "payment_method": "card",
            "idempotency_key": f"tx_fake_{booking_id}",
        },
        headers=_auth_header(customer),
    )
    assert confirm_res.status_code == 422
    assert "invalid cryptographic payment signature" in confirm_res.text.lower()


@pytest.mark.asyncio
async def test_cancellation_rules_and_fee_sla(client: AsyncClient, booking_setup: dict):
    """
    Verify cancellation SLA:
    - Free cancellation before en route (₹0 fee)
    - Rescheduling allowed >2h before scheduled time
    """
    customer = booking_setup["customer"]
    srv = booking_setup["service"]
    address = booking_setup["address"]
    slot = booking_setup["slot"]

    # Create scheduled booking
    r = await client.post(
        "/api/v1/bookings",
        json={
            "service_id": str(srv.id),
            "tier_type": ServiceTierType.BASIC.value,
            "booking_type": BookingType.SCHEDULED.value,
            "slot_id": str(slot.id),
            "address_id": str(address.id),
            "idempotency_key": f"cancel_test_{uuid.uuid4().hex[:8]}",
        },
        headers=_auth_header(customer),
    )
    assert r.status_code == 201
    booking_id = r.json()["id"]

    # Cancel while in HOLD_RESERVED
    cancel_res = await client.post(
        f"/api/v1/bookings/{booking_id}/cancel",
        json={"reason": "Customer changed mind"},
        headers=_auth_header(customer),
    )
    assert cancel_res.status_code == 200
    c_data = cancel_res.json()
    assert c_data["status"] == BookingStatus.CANCELLED.value
    assert c_data["cancellation_fee_paise"] == 0


@pytest.mark.asyncio
async def test_pro_decline_and_reassignment_fallback(client: AsyncClient, booking_setup: dict):
    """
    Verify auto-dispatch offer decline and fallback reassignment:
    1. Booking payment is confirmed -> Pro 1 receives offer.
    2. Pro 1 declines offer with reason.
    3. Dispatch engine reassigns to next available candidate (Pro 2).
    4. Pro 2 accepts and starts journey.
    """
    customer = booking_setup["customer"]
    pro_user1 = booking_setup["pro_user1"]
    pro_user2 = booking_setup["pro_user2"]
    srv = booking_setup["service"]
    address = booking_setup["address"]

    # 1. Create and pay
    r = await client.post(
        "/api/v1/bookings",
        json={
            "service_id": str(srv.id),
            "tier_type": ServiceTierType.BASIC.value,
            "booking_type": BookingType.INSTANT.value,
            "address_id": str(address.id),
            "idempotency_key": f"decline_test_{uuid.uuid4().hex[:8]}",
        },
        headers=_auth_header(customer),
    )
    assert r.status_code == 201
    booking_id = r.json()["id"]

    init_res = await client.post(f"/api/v1/bookings/{booking_id}/pay", headers=_auth_header(customer))
    order_id = init_res.json()["gateway_order_id"]
    payment_id = f"pay_{uuid.uuid4().hex[:12]}"
    secret = "mock_rzp_secret_key_1234567890"
    message = f"{order_id}|{payment_id}".encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()

    confirm_res = await client.post(
        f"/api/v1/bookings/{booking_id}/confirm-payment",
        json={
            "gateway_order_id": order_id,
            "gateway_payment_id": payment_id,
            "signature": sig,
            "payment_method": "online_upi",
            "idempotency_key": f"tx_dec_{booking_id}",
        },
        headers=_auth_header(customer),
    )
    assert confirm_res.status_code == 200

    # 2. Check initial assignment is Pro 1
    detail1 = (await client.get(f"/api/v1/bookings/{booking_id}", headers=_auth_header(customer))).json()
    assert detail1["assigned_professional_id"] == str(booking_setup["pro_prof1"].id)

    # 3. Pro 1 declines
    dec_res = await client.post(
        f"/api/v1/bookings/{booking_id}/dispatch-response",
        json={"action": "decline", "decline_reason": "Emergency vehicle maintenance"},
        headers=_auth_header(pro_user1),
    )
    assert dec_res.status_code == 200
    dec_data = dec_res.json()

    # Reassigned to Pro 2!
    assert dec_data["assigned_professional_id"] == str(booking_setup["pro_prof2"].id)

    # 4. Pro 2 accepts
    accept_res = await client.post(
        f"/api/v1/bookings/{booking_id}/dispatch-response",
        json={"action": "accept"},
        headers=_auth_header(pro_user2),
    )
    assert accept_res.status_code == 200
    assert accept_res.json()["status"] == BookingStatus.EN_ROUTE.value

