"""
Unit tests for Booking State Machine, Immutable Snapshot Verification,
Cryptographic Payment Validation, and Cancellation/Rescheduling Policies.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
import uuid
import pytest

from app.core.errors import ConflictError, ValidationError
from app.integrations.payment import MockRazorpayPaymentAdapter, PaymentGatewayPort
from app.modules.bookings.enums import BookingStatus, BookingType, PaymentStatus
from app.modules.bookings.models import Booking, BookingPriceSnapshot
from app.modules.bookings.service import VALID_TRANSITIONS, BookingService
from app.modules.catalog.enums import ServiceTierType


def test_state_machine_transition_graph_integrity():
    """Verify state machine graph guarantees per ADR-0003 and Target Architecture."""
    # Terminal states must have empty allowed transitions
    terminal_states = [
        BookingStatus.COMPLETED,
        BookingStatus.CANCELLED,
        BookingStatus.EXPIRED,
    ]
    for st in terminal_states:
        assert VALID_TRANSITIONS[st] == [], f"Terminal state {st} must have no outgoing transitions."

    # Failed assignment can either retry dispatching or cancel
    assert set(VALID_TRANSITIONS[BookingStatus.FAILED_ASSIGNMENT]) == {
        BookingStatus.DISPATCHING,
        BookingStatus.CANCELLED,
    }

    # Normal progression must exist
    assert BookingStatus.CONFIRMED in VALID_TRANSITIONS[BookingStatus.HOLD_RESERVED]
    assert BookingStatus.DISPATCHING in VALID_TRANSITIONS[BookingStatus.CONFIRMED]
    assert BookingStatus.ASSIGNED in VALID_TRANSITIONS[BookingStatus.DISPATCHING]
    assert BookingStatus.EN_ROUTE in VALID_TRANSITIONS[BookingStatus.ASSIGNED]
    assert BookingStatus.ARRIVED in VALID_TRANSITIONS[BookingStatus.EN_ROUTE]
    assert BookingStatus.IN_PROGRESS in VALID_TRANSITIONS[BookingStatus.ARRIVED]
    assert BookingStatus.COMPLETED in VALID_TRANSITIONS[BookingStatus.IN_PROGRESS]


def test_state_machine_illegal_transition_rejection():
    """Verify illegal transitions are rejected without mutating status."""
    service = BookingService(db=None)  # db is unused for pure transition validation check
    booking = Booking(
        id=uuid.uuid4(),
        booking_number="GN-TEST-001",
        customer_id=uuid.uuid4(),
        service_id=uuid.uuid4(),
        tier_type=ServiceTierType.BASIC,
        booking_type=BookingType.INSTANT,
        status=BookingStatus.HOLD_RESERVED,
        idempotency_key="key-1",
        address_id=uuid.uuid4(),
        address_snapshot={},
        hold_expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        start_otp="1234",
        completion_otp="5678",
        eta_minutes=25,
        is_fallback_location=False,
    )

    # Cannot jump directly from HOLD_RESERVED to IN_PROGRESS or COMPLETED
    with pytest.raises(ValidationError) as exc:
        service.validate_transition(booking.status, BookingStatus.IN_PROGRESS)
    assert "Invalid booking status transition" in str(exc.value)

    with pytest.raises(ValidationError):
        service.validate_transition(booking.status, BookingStatus.COMPLETED)


def test_immutable_price_snapshot_canonical_hashing():
    """Verify SHA-256 canonical hashing ensures tamper detection regardless of key ordering."""
    payload_a = {
        "booking_number": "GN-20261022-ABCDEF",
        "service_id": str(uuid.uuid4()),
        "tier": "basic",
        "base_rate_paise": 79900,
        "add_ons_total_paise": 15000,
        "travel_fee_paise": 0,
        "discount_applied_paise": 10000,
        "taxable_amount_paise": 84900,
        "cgst_paise": 7641,
        "sgst_paise": 7641,
        "total_payable_paise": 100182,
    }
    # Create copy with reversed key order
    payload_b = dict(reversed(list(payload_a.items())))

    hash_a = BookingPriceSnapshot.compute_hash(payload_a)
    hash_b = BookingPriceSnapshot.compute_hash(payload_b)
    assert hash_a == hash_b, "Hash must be identical regardless of JSON key serialization order."

    # Any single byte modification must completely alter the hash
    payload_tampered = dict(payload_a)
    payload_tampered["total_payable_paise"] = 100000
    hash_tampered = BookingPriceSnapshot.compute_hash(payload_tampered)
    assert hash_a != hash_tampered, "Tampered amount must yield completely different hash."


@pytest.mark.asyncio
async def test_cryptographic_payment_signature_verification():
    """Verify payment gateway validates HMAC-SHA256 signatures and rejects forged signatures."""
    gateway: PaymentGatewayPort = MockRazorpayPaymentAdapter(key_secret="test_secret_123")

    order_id = "order_glamnow_9999"
    payment_id = "pay_sandbox_8888"

    # Compute valid signature: HMAC-SHA256(order_id + "|" + payment_id, key_secret)
    import hmac
    message = f"{order_id}|{payment_id}".encode("utf-8")
    valid_signature = hmac.new("test_secret_123".encode("utf-8"), message, hashlib.sha256).hexdigest()

    # 1. Valid signature passes
    valid_res = await gateway.verify_payment(order_id, payment_id, valid_signature)
    assert valid_res.is_valid is True
    assert valid_res.order_id == order_id
    assert valid_res.payment_id == payment_id

    # 2. Tampered signature fails
    fake_signature = "deadbeef" * 8
    invalid_res = await gateway.verify_payment(order_id, payment_id, fake_signature)
    assert invalid_res.is_valid is False
    assert invalid_res.error_message is not None


def test_cancellation_fee_policy():
    """Verify cancellation fee SLA: ₹0 before EN_ROUTE, ₹150 (15000 paise) once EN_ROUTE."""
    service = BookingService(db=None)
    total_paid_paise = 100000  # ₹1,000

    # Before EN_ROUTE (e.g. CONFIRMED, DISPATCHING, ASSIGNED)
    fee_assigned, refund_assigned = service.calculate_cancellation_refund(
        current_status=BookingStatus.ASSIGNED, total_paid_paise=total_paid_paise
    )
    assert fee_assigned == 0
    assert refund_assigned == 100000

    # Once EN_ROUTE, late fee of 15000 paise applies
    fee_en_route, refund_en_route = service.calculate_cancellation_refund(
        current_status=BookingStatus.EN_ROUTE, total_paid_paise=total_paid_paise
    )
    assert fee_en_route == 15000
    assert refund_en_route == 85000

    # Small order where total paid < late fee
    small_paid = 10000  # ₹100
    fee_small, refund_small = service.calculate_cancellation_refund(
        current_status=BookingStatus.EN_ROUTE, total_paid_paise=small_paid
    )
    assert fee_small == 10000
    assert refund_small == 0
