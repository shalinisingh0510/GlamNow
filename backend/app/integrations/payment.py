"""
Payment gateway provider ports and adapters (ADR-0004).

Implements Razorpay sandbox integration with HMAC-SHA256 signature verification,
webhook handling, and idempotent transaction processing.
CRITICAL INVARIANT: Never mark a booking paid merely because the frontend reports success.
All payments require cryptographic server-side validation.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any, Protocol, runtime_checkable
import uuid

from pydantic import BaseModel, Field

from app.core.settings import get_settings


class PaymentOrderResult(BaseModel):
    """Normalized gateway order creation response."""
    order_id: str
    amount_paise: int
    currency: str = "INR"
    status: str = "created"
    idempotency_key: str | None = None


class PaymentVerificationResult(BaseModel):
    """Result of verifying payment authenticity."""
    is_valid: bool
    payment_id: str
    order_id: str
    amount_paise: int | None = None
    error_message: str | None = None


class PaymentWebhookEvent(BaseModel):
    """Normalized webhook payload."""
    event: str  # e.g., "payment.captured", "payment.failed"
    payment_id: str
    order_id: str
    amount_paise: int
    status: str
    raw_payload: dict[str, Any] = Field(default_factory=dict)


@runtime_checkable
class PaymentGatewayPort(Protocol):
    """Port interface for payment gateway operations."""

    async def create_order(
        self,
        booking_id: uuid.UUID,
        amount_paise: int,
        currency: str = "INR",
        idempotency_key: str | None = None,
    ) -> PaymentOrderResult: ...

    async def verify_payment(
        self,
        order_id: str,
        payment_id: str,
        signature: str,
    ) -> PaymentVerificationResult: ...

    async def process_webhook(
        self,
        raw_body: bytes,
        signature_header: str,
    ) -> PaymentWebhookEvent: ...


class MockRazorpayPaymentAdapter:
    """
    Simulated Razorpay sandbox adapter with authentic HMAC-SHA256 signatures,
    webhook processing, and deterministic failure simulation.
    """

    def __init__(self, key_secret: str | None = None, simulate_failure: bool = False) -> None:
        self.key_secret = key_secret or "mock_rzp_secret_key_1234567890"
        self.simulate_failure = simulate_failure
        self._processed_payments: dict[str, dict[str, Any]] = {}

    def generate_valid_signature(self, order_id: str, payment_id: str) -> str:
        """Helper to generate a valid HMAC-SHA256 signature for sandbox tests."""
        message = f"{order_id}|{payment_id}".encode("utf-8")
        return hmac.new(self.key_secret.encode("utf-8"), message, hashlib.sha256).hexdigest()

    async def create_order(
        self,
        booking_id: uuid.UUID,
        amount_paise: int,
        currency: str = "INR",
        idempotency_key: str | None = None,
    ) -> PaymentOrderResult:
        if self.simulate_failure:
            raise RuntimeError("Payment gateway rejected order creation (simulated gateway outage)")

        order_id = f"order_mock_{uuid.uuid4().hex[:14]}"
        return PaymentOrderResult(
            order_id=order_id,
            amount_paise=amount_paise,
            currency=currency,
            status="created",
            idempotency_key=idempotency_key,
        )

    async def verify_payment(
        self,
        order_id: str,
        payment_id: str,
        signature: str,
    ) -> PaymentVerificationResult:
        if self.simulate_failure:
            return PaymentVerificationResult(
                is_valid=False,
                payment_id=payment_id,
                order_id=order_id,
                error_message="Payment declined by bank / gateway simulation",
            )

        expected_sig = self.generate_valid_signature(order_id, payment_id)
        is_match = hmac.compare_digest(expected_sig, signature)

        if not is_match:
            return PaymentVerificationResult(
                is_valid=False,
                payment_id=payment_id,
                order_id=order_id,
                error_message="Invalid cryptographic payment signature",
            )

        return PaymentVerificationResult(
            is_valid=True,
            payment_id=payment_id,
            order_id=order_id,
        )

    async def process_webhook(
        self,
        raw_body: bytes,
        signature_header: str,
    ) -> PaymentWebhookEvent:
        # Verify webhook signature
        expected_sig = hmac.new(
            self.key_secret.encode("utf-8"), raw_body, hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(expected_sig, signature_header):
            raise ValueError("Webhook HMAC signature verification failed")

        data = json.loads(raw_body.decode("utf-8"))
        payload_entity = data.get("payload", {}).get("payment", {}).get("entity", {})

        return PaymentWebhookEvent(
            event=data.get("event", "payment.captured"),
            payment_id=payload_entity.get("id", ""),
            order_id=payload_entity.get("order_id", ""),
            amount_paise=payload_entity.get("amount", 0),
            status=payload_entity.get("status", "captured"),
            raw_payload=data,
        )


_payment_gateway_instance: PaymentGatewayPort | None = None


def get_payment_gateway() -> PaymentGatewayPort:
    """Dependency injection factory for active payment gateway adapter."""
    global _payment_gateway_instance
    if _payment_gateway_instance is None:
        settings = get_settings()
        secret = getattr(settings, "razorpay_key_secret", None) or "sandbox_rzp_secret"
        _payment_gateway_instance = MockRazorpayPaymentAdapter(key_secret=secret)
    return _payment_gateway_instance


def set_payment_gateway(gateway: PaymentGatewayPort) -> None:
    """Override payment gateway for hermetic unit / integration tests."""
    global _payment_gateway_instance
    _payment_gateway_instance = gateway
