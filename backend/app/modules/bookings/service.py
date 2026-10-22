"""
Booking service layer: state machine transitions, immutable price snapshots,
cryptographic payment confirmation, and intelligent quick-dispatch engine.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import secrets
from typing import Any
import uuid

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.integrations.geo import Coordinates, GeoRoutingPort, get_geo_provider
from app.integrations.notifications import NotificationPort, get_notification_service
from app.integrations.payment import PaymentGatewayPort, get_payment_gateway
from app.modules.bookings.enums import (
    BookingStatus,
    BookingType,
    DispatchOfferStatus,
    PaymentMethod,
    PaymentStatus,
)
from app.modules.bookings.models import (
    Booking,
    BookingItem,
    BookingPriceSnapshot,
    BookingStatusHistory,
    DispatchOffer,
    PaymentTransaction,
)
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
from app.modules.catalog.enums import ServiceTierType
from app.modules.catalog.models import Service, ServiceAddOn, ServiceTier
from app.modules.catalog.schemas import QuoteRequest
from app.modules.catalog.service import CatalogService
from app.modules.identity.enums import UserRole
from app.modules.identity.models import SavedAddress, User
from app.modules.professionals.enums import SlotStatus, VerificationStatus
from app.modules.professionals.models import AppointmentSlot, ProfessionalProfile, ProfessionalServiceOffering


# State Machine Valid Transitions Graph (ADR-0003 & Target Architecture 4.1)
VALID_TRANSITIONS: dict[BookingStatus, list[BookingStatus]] = {
    BookingStatus.HOLD_RESERVED: [
        BookingStatus.CONFIRMED,
        BookingStatus.CANCELLED,
        BookingStatus.EXPIRED,
    ],
    BookingStatus.CONFIRMED: [
        BookingStatus.DISPATCHING,
        BookingStatus.ASSIGNED,
        BookingStatus.CANCELLED,
    ],
    BookingStatus.DISPATCHING: [
        BookingStatus.ASSIGNED,
        BookingStatus.FAILED_ASSIGNMENT,
        BookingStatus.CANCELLED,
    ],
    BookingStatus.ASSIGNED: [
        BookingStatus.EN_ROUTE,
        BookingStatus.DISPATCHING,
        BookingStatus.CANCELLED,
    ],
    BookingStatus.EN_ROUTE: [
        BookingStatus.ARRIVED,
        BookingStatus.CANCELLED,
    ],
    BookingStatus.ARRIVED: [
        BookingStatus.IN_PROGRESS,
        BookingStatus.CANCELLED,
    ],
    BookingStatus.IN_PROGRESS: [
        BookingStatus.COMPLETED,
    ],
    BookingStatus.COMPLETED: [],
    BookingStatus.CANCELLED: [],
    BookingStatus.FAILED_ASSIGNMENT: [
        BookingStatus.DISPATCHING,
        BookingStatus.CANCELLED,
    ],
    BookingStatus.EXPIRED: [],
}


def _ensure_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class BookingService:
    """Service layer managing the end-to-end customer booking lifecycle."""

    def __init__(
        self,
        db: AsyncSession,
        payment_gateway: PaymentGatewayPort | None = None,
        notification_service: NotificationPort | None = None,
        geo_provider: GeoRoutingPort | None = None,
    ) -> None:
        self.db = db
        self.payment_gateway = payment_gateway or get_payment_gateway()
        self.notifications = notification_service or get_notification_service()
        self.geo_provider = geo_provider or get_geo_provider()

    async def get_booking_by_id(self, booking_id: uuid.UUID) -> Booking:
        stmt = (
            select(Booking)
            .where(Booking.id == booking_id)
            .options(
                selectinload(Booking.customer),
                selectinload(Booking.assigned_professional).selectinload(ProfessionalProfile.user),
                selectinload(Booking.service),
                selectinload(Booking.items),
                selectinload(Booking.price_snapshot),
                selectinload(Booking.status_history),
                selectinload(Booking.payment_transactions),
                selectinload(Booking.dispatch_offers),
            )
        )
        res = await self.db.execute(stmt)
        booking = res.scalar_one_or_none()
        if not booking:
            raise NotFoundError("Booking", str(booking_id))
        return booking

    async def get_booking_by_idempotency_key(self, key: str) -> Booking | None:
        stmt = (
            select(Booking)
            .where(Booking.idempotency_key == key)
            .options(
                selectinload(Booking.customer),
                selectinload(Booking.assigned_professional).selectinload(ProfessionalProfile.user),
                selectinload(Booking.service),
                selectinload(Booking.items),
                selectinload(Booking.price_snapshot),
                selectinload(Booking.status_history),
                selectinload(Booking.payment_transactions),
                selectinload(Booking.dispatch_offers),
            )
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()


    @staticmethod
    def validate_transition(from_status: BookingStatus, to_status: BookingStatus) -> bool:
        """Validates whether a transition from one status to another is permitted."""
        allowed_targets = VALID_TRANSITIONS.get(from_status, [])
        if to_status not in allowed_targets:
            raise ValidationError(
                f"Invalid booking status transition from '{from_status.value}' to '{to_status.value}'."
            )
        return True

    @staticmethod
    def calculate_cancellation_refund(
        current_status: BookingStatus, total_paid_paise: int
    ) -> tuple[int, int]:
        """
        Calculates cancellation fee and refundable amount per SLA.
        Free before EN_ROUTE; ₹150 (15,000 paise) late cancellation fee once partner is en route.
        Returns: (fee_paise, refund_paise)
        """
        if current_status == BookingStatus.EN_ROUTE:
            fee = min(15000, total_paid_paise)
            return fee, total_paid_paise - fee
        return 0, total_paid_paise

    async def record_status_transition(
        self,
        booking: Booking,
        to_status: BookingStatus,
        actor_id: uuid.UUID | None,
        actor_role: str,
        reason: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Validates and applies a state machine transition."""
        self.validate_transition(booking.status, to_status)

        from_status = booking.status
        booking.status = to_status

        history_entry = BookingStatusHistory(
            booking_id=booking.id,
            from_status=from_status,
            to_status=to_status,
            actor_id=actor_id,
            actor_role=actor_role,
            reason=reason,
            metadata_json=metadata,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(history_entry)

    # ─────────────────────────────────────────────────────────────
    # Customer Journey: Reservation Hold Creation
    # ─────────────────────────────────────────────────────────────

    async def create_booking_hold(
        self, customer: User, data: BookingCreateRequest
    ) -> Booking:
        """
        Creates a temporary 10-minute reservation hold.
        Calculates quote, snapshots immutable pricing, locks slot if scheduled,
        and generates OTPs.
        """
        # Idempotency check: Return existing booking if same idempotency key is submitted
        existing = await self.get_booking_by_idempotency_key(data.idempotency_key)
        if existing:
            return existing

        # Verify Service
        service = await self.db.get(Service, data.service_id)
        if not service or not service.is_active:
            raise NotFoundError("Service", str(data.service_id))

        # Verify Address
        address = await self.db.get(SavedAddress, data.address_id)
        if not address or address.user_id != customer.id:
            raise NotFoundError("Address", str(data.address_id))

        address_snapshot = {
            "address_line1": address.address_line1,
            "address_line2": address.address_line2,
            "city": address.city,
            "state": address.state,
            "pincode": address.pincode,
            "landmark": address.landmark,
            "latitude": address.latitude or 12.9352,
            "longitude": address.longitude or 77.6245,
        }

        # Calculate Authoritative Price Quote
        catalog_service = CatalogService(self.db)
        quote_request = QuoteRequest(
            service_id=data.service_id,
            tier=data.tier_type,
            add_on_ids=data.add_on_ids,
            discount_code=data.coupon_code,
            pincode=address.pincode or "560038",
        )
        quote = await catalog_service.calculate_quote(quote_request)

        now_utc = datetime.now(timezone.utc)
        hold_expires_at = now_utc + timedelta(minutes=10)

        # Scheduled Appointment Handling
        slot = None
        scheduled_start = None
        scheduled_end = None
        assigned_pro_id = None

        if data.booking_type == BookingType.SCHEDULED:
            if not data.slot_id:
                raise ValidationError("Slot ID is required for scheduled appointments.", field="slot_id")

            slot_stmt = (
                select(AppointmentSlot)
                .where(AppointmentSlot.id == data.slot_id)
                .with_for_update()
            )
            slot = (await self.db.execute(slot_stmt)).scalar_one_or_none()
            if not slot:
                raise NotFoundError("AppointmentSlot", str(data.slot_id))

            # Expiration check
            slot_exp = _ensure_utc(slot.reservation_expires_at)
            if slot.status == SlotStatus.RESERVED and slot_exp and slot_exp < now_utc:
                slot.status = SlotStatus.AVAILABLE
                slot.reserved_by_user_id = None

            if slot.status != SlotStatus.AVAILABLE:
                raise ConflictError("The selected appointment slot is no longer available.")

            # Hold slot
            slot.status = SlotStatus.RESERVED
            slot.reserved_by_user_id = customer.id
            slot.reservation_expires_at = hold_expires_at
            scheduled_start = slot.start_time
            scheduled_end = slot.end_time
            assigned_pro_id = slot.professional_id
        else:
            # Instant Booking: check if preferred pro was explicitly chosen
            if data.preferred_professional_id:
                pro = await self.db.get(ProfessionalProfile, data.preferred_professional_id)
                if pro and pro.is_active:
                    assigned_pro_id = pro.id

        # Credible ETA calculation (Never guarantee 10m based on configuration alone)
        customer_coords = Coordinates(
            latitude=address_snapshot["latitude"], longitude=address_snapshot["longitude"]
        )
        origin_coords = Coordinates(latitude=12.9352, longitude=77.6245)  # City hub
        travel_est = await self.geo_provider.calculate_travel_estimate(origin_coords, customer_coords)
        credible_eta = max(15, travel_est.duration_minutes)

        # Generate OTPs
        start_otp = f"{secrets.randbelow(10000):04d}"
        completion_otp = f"{secrets.randbelow(10000):04d}"

        # Generate booking number
        date_prefix = now_utc.strftime("%Y%m%d")
        rand_suffix = secrets.token_hex(3).upper()
        booking_number = f"GN-{date_prefix}-{rand_suffix}"

        # Create Booking
        booking = Booking(
            booking_number=booking_number,
            customer_id=customer.id,
            assigned_professional_id=assigned_pro_id,
            service_id=data.service_id,
            tier_type=data.tier_type,
            booking_type=data.booking_type,
            status=BookingStatus.HOLD_RESERVED,
            idempotency_key=data.idempotency_key,
            address_id=data.address_id,
            address_snapshot=address_snapshot,
            scheduled_start_time=scheduled_start,
            scheduled_end_time=scheduled_end,
            slot_id=data.slot_id,
            hold_expires_at=hold_expires_at,
            start_otp=start_otp,
            completion_otp=completion_otp,
            eta_minutes=credible_eta,
            is_fallback_location=travel_est.is_fallback,
        )
        self.db.add(booking)
        await self.db.flush()

        # Add line items
        self.db.add(
            BookingItem(
                booking_id=booking.id,
                name=f"{service.name} ({data.tier_type.value.capitalize()})",
                item_type="SERVICE_TIER",
                price_paise=quote.base_price_paise,
                quantity=1,
            )
        )
        for add_on_id in data.add_on_ids:
            ao = await self.db.get(ServiceAddOn, add_on_id)
            if ao:
                self.db.add(
                    BookingItem(
                        booking_id=booking.id,
                        name=ao.name,
                        item_type="ADD_ON",
                        price_paise=ao.price_paise,
                        quantity=1,
                    )
                )

        # Create Immutable Price Snapshot
        add_ons_total_paise = sum(a.price_paise for a in quote.add_ons)
        taxable_amount_paise = quote.subtotal_paise - quote.discount_paise
        snapshot_dict = {
            "booking_number": booking_number,
            "service_id": str(data.service_id),
            "tier": data.tier_type.value,
            "base_rate_paise": quote.base_price_paise,
            "add_ons_total_paise": add_ons_total_paise,
            "travel_fee_paise": quote.travel_fee_paise,
            "discount_applied_paise": quote.discount_paise,
            "taxable_amount_paise": taxable_amount_paise,
            "cgst_paise": quote.tax_cgst_paise,
            "sgst_paise": quote.tax_sgst_paise,
            "total_payable_paise": quote.total_paise,
            "calculated_at": now_utc.isoformat(),
        }
        snapshot_hash = BookingPriceSnapshot.compute_hash(snapshot_dict)

        price_snapshot = BookingPriceSnapshot(
            booking_id=booking.id,
            base_rate_paise=quote.base_price_paise,
            add_ons_total_paise=add_ons_total_paise,
            travel_fee_paise=quote.travel_fee_paise,
            discount_applied_paise=quote.discount_paise,
            taxable_amount_paise=taxable_amount_paise,
            cgst_paise=quote.tax_cgst_paise,
            sgst_paise=quote.tax_sgst_paise,
            total_payable_paise=quote.total_paise,
            snapshot_payload=snapshot_dict,
            snapshot_hash=snapshot_hash,
        )
        self.db.add(price_snapshot)

        # Record Initial Status History
        self.db.add(
            BookingStatusHistory(
                booking_id=booking.id,
                from_status=None,
                to_status=BookingStatus.HOLD_RESERVED,
                actor_id=customer.id,
                actor_role=UserRole.CUSTOMER.value,
                reason="Customer initialized booking checkout hold",
                metadata_json={"hold_duration_minutes": 10},
                created_at=now_utc,
            )
        )

        await self.db.commit()
        return await self.get_booking_by_id(booking.id)

    # ─────────────────────────────────────────────────────────────
    # Sandbox Payment Initiation and Cryptographic Confirmation
    # ─────────────────────────────────────────────────────────────

    async def initiate_payment(
        self, booking_id: uuid.UUID, customer: User
    ) -> PaymentInitiateResponse:
        booking = await self.get_booking_by_id(booking_id)
        if booking.customer_id != customer.id:
            raise ForbiddenError("Unauthorized to pay for this booking.")

        now_utc = datetime.now(timezone.utc)
        hold_exp = _ensure_utc(booking.hold_expires_at)
        if booking.status != BookingStatus.HOLD_RESERVED or (hold_exp and hold_exp < now_utc):
            if booking.status == BookingStatus.HOLD_RESERVED:
                await self.record_status_transition(
                    booking, BookingStatus.EXPIRED, customer.id, UserRole.CUSTOMER.value, "Hold expired"
                )
                await self.db.commit()
            raise ConflictError("Reservation hold has expired. Please select a time slot again.")

        order_res = await self.payment_gateway.create_order(
            booking_id=booking.id,
            amount_paise=booking.price_snapshot.total_payable_paise,
            idempotency_key=f"pay_order_{booking.id}",
        )

        return PaymentInitiateResponse(
            booking_id=booking.id,
            booking_number=booking.booking_number,
            gateway_order_id=order_res.order_id,
            amount_paise=order_res.amount_paise,
            currency=order_res.currency,
            hold_expires_at=booking.hold_expires_at,
        )

    async def confirm_payment(
        self,
        booking_id: uuid.UUID,
        customer: User,
        data: PaymentConfirmRequest,
    ) -> PaymentConfirmResponse:
        """
        Cryptographic confirmation of payment.
        Validates signature, records transaction, and transitions to CONFIRMED.
        """
        booking = await self.get_booking_by_id(booking_id)
        if booking.customer_id != customer.id:
            raise ForbiddenError("Unauthorized to confirm this payment.")

        # Idempotency check: Return success if transaction with this key was already settled
        tx_stmt = select(PaymentTransaction).where(
            PaymentTransaction.idempotency_key == data.idempotency_key
        )
        existing_tx = (await self.db.execute(tx_stmt)).scalar_one_or_none()
        if existing_tx and existing_tx.status == PaymentStatus.CAPTURED:
            return PaymentConfirmResponse(
                ok=True,
                booking_id=booking.id,
                booking_status=booking.status,
                payment_status=existing_tx.status,
                message="Payment already verified and confirmed.",
            )

        now_utc = datetime.now(timezone.utc)
        hold_exp = _ensure_utc(booking.hold_expires_at)
        if booking.status != BookingStatus.HOLD_RESERVED or (hold_exp and hold_exp < now_utc):
            raise ConflictError("Hold window has expired; cannot authorize payment for expired reservation.")

        # Cryptographic signature validation
        verify_result = await self.payment_gateway.verify_payment(
            order_id=data.gateway_order_id,
            payment_id=data.gateway_payment_id,
            signature=data.signature,
        )

        if not verify_result.is_valid:
            # Record failed transaction audit
            fail_tx = PaymentTransaction(
                booking_id=booking.id,
                idempotency_key=data.idempotency_key,
                gateway_order_id=data.gateway_order_id,
                gateway_payment_id=data.gateway_payment_id,
                amount_paise=booking.price_snapshot.total_payable_paise,
                payment_method=data.payment_method,
                status=PaymentStatus.FAILED,
                signature=data.signature,
                raw_response={"error": verify_result.error_message},
            )
            self.db.add(fail_tx)
            await self.db.commit()
            raise ValidationError(
                verify_result.error_message or "Payment verification signature mismatch."
            )

        # Successful payment transaction
        success_tx = PaymentTransaction(
            booking_id=booking.id,
            idempotency_key=data.idempotency_key,
            gateway_order_id=data.gateway_order_id,
            gateway_payment_id=data.gateway_payment_id,
            amount_paise=booking.price_snapshot.total_payable_paise,
            payment_method=data.payment_method,
            status=PaymentStatus.CAPTURED,
            signature=data.signature,
            verified_at=now_utc,
            raw_response={"verified": True},
        )
        self.db.add(success_tx)

        # Lock Slot if scheduled
        if booking.slot_id:
            slot = await self.db.get(AppointmentSlot, booking.slot_id)
            if slot:
                slot.status = SlotStatus.BOOKED

        # Transition to CONFIRMED
        await self.record_status_transition(
            booking=booking,
            to_status=BookingStatus.CONFIRMED,
            actor_id=customer.id,
            actor_role=UserRole.CUSTOMER.value,
            reason="Payment authorized via Razorpay sandbox",
            metadata={"payment_id": data.gateway_payment_id},
        )

        await self.db.flush()

        # Send confirmation notification
        await self.notifications.send_notification(
            recipient_phone=customer.phone,
            message=(
                f"GlamNow: Booking {booking.booking_number} confirmed! "
                f"Your 4-digit start OTP is {booking.start_otp}."
            ),
            event_type="booking_confirmed",
            metadata={"booking_id": str(booking.id)},
        )

        # Next Step: Automatic dispatch trigger
        if booking.booking_type == BookingType.SCHEDULED and booking.assigned_professional_id:
            await self.record_status_transition(
                booking=booking,
                to_status=BookingStatus.ASSIGNED,
                actor_id=None,
                actor_role="system",
                reason="Scheduled visit assigned to preferred partner",
            )
        else:
            # Trigger quick dispatch search
            await self.dispatch_instant_booking(booking)

        await self.db.commit()

        return PaymentConfirmResponse(
            ok=True,
            booking_id=booking.id,
            booking_status=booking.status,
            payment_status=PaymentStatus.CAPTURED,
            message="Payment verified and booking confirmed successfully.",
        )

    # ─────────────────────────────────────────────────────────────
    # Quick Dispatch Engine: Proximity, Skills & Credible Arrival
    # ─────────────────────────────────────────────────────────────

    async def dispatch_instant_booking(self, booking: Booking) -> bool:
        """
        Dispatches booking by finding eligible nearby professionals.
        Evaluates service offering, verified status, proximity, and schedule capacity.
        """
        await self.record_status_transition(
            booking=booking,
            to_status=BookingStatus.DISPATCHING,
            actor_id=None,
            actor_role="system",
            reason="Auto-matching best nearby available partner",
        )

        cust_lat = booking.address_snapshot.get("latitude", 12.9352)
        cust_lng = booking.address_snapshot.get("longitude", 77.6245)
        cust_coords = Coordinates(latitude=cust_lat, longitude=cust_lng)

        # Query active verified professionals with instant booking
        stmt = (
            select(ProfessionalProfile)
            .where(
                ProfessionalProfile.is_active.is_(True),
                ProfessionalProfile.is_accepting_instant_bookings.is_(True),
                ProfessionalProfile.verification_status == VerificationStatus.VERIFIED,
            )
            .options(
                selectinload(ProfessionalProfile.user),
                selectinload(ProfessionalProfile.service_offerings),
            )
        )
        candidates = (await self.db.execute(stmt)).scalars().all()

        # Exclude professionals who already declined or timed out for this booking
        declined_pro_ids = {
            o.professional_id
            for o in (booking.dispatch_offers or [])
            if o.status in (DispatchOfferStatus.DECLINED, DispatchOfferStatus.TIMED_OUT)
        }

        eligible_ranked: list[tuple[ProfessionalProfile, float, int]] = []

        for pro in candidates:
            if pro.id in declined_pro_ids:
                continue
            # Check service offering qualification
            has_offering = any(
                o.service_id == booking.service_id
                and o.tier_type == booking.tier_type
                and o.is_active
                for o in pro.service_offerings
            )
            # Default fallback: if no explicit override exists, general active pros qualify
            if pro.service_offerings and not has_offering:
                continue

            # Calculate credible travel estimate
            pro_coords = Coordinates(latitude=pro.latitude, longitude=pro.longitude)
            estimate = await self.geo_provider.calculate_travel_estimate(pro_coords, cust_coords)

            if estimate.distance_km > pro.service_radius_km:
                continue

            # Score = (duration_mins * 1.5) - (rating * 5)
            score = (estimate.duration_minutes * 1.5) - (pro.rating * 5.0)
            eligible_ranked.append((pro, score, estimate.duration_minutes))

        if not eligible_ranked:
            # No eligible partner currently available in this sector
            await self.record_status_transition(
                booking=booking,
                to_status=BookingStatus.FAILED_ASSIGNMENT,
                actor_id=None,
                actor_role="system",
                reason="No active verified partners available within service zone",
            )
            return False

        # Sort by best dispatch score
        eligible_ranked.sort(key=lambda x: x[1])
        best_pro, _, eta_minutes = eligible_ranked[0]

        # Assign professional
        booking.assigned_professional_id = best_pro.id
        booking.eta_minutes = max(15, eta_minutes)

        offer = DispatchOffer(
            booking_id=booking.id,
            professional_id=best_pro.id,
            status=DispatchOfferStatus.OFFERED,
            offered_at=datetime.now(timezone.utc),
        )
        self.db.add(offer)

        await self.record_status_transition(
            booking=booking,
            to_status=BookingStatus.ASSIGNED,
            actor_id=None,
            actor_role="system",
            reason=f"Partner {best_pro.user.full_name if best_pro.user else ''} assigned (ETA {booking.eta_minutes}m)",
            metadata={"professional_id": str(best_pro.id), "eta_minutes": booking.eta_minutes},
        )

        # Notify professional
        if best_pro.user:
            await self.notifications.send_notification(
                recipient_phone=best_pro.user.phone,
                message=f"GlamNow: New service request {booking.booking_number}! Tap to accept/decline.",
                event_type="dispatch_offer",
                metadata={"booking_id": str(booking.id)},
            )

        return True

    # ─────────────────────────────────────────────────────────────
    # Professional Partner Acceptance, En-Route, and OTP Flow
    # ─────────────────────────────────────────────────────────────

    async def respond_to_dispatch(
        self,
        booking_id: uuid.UUID,
        pro_user: User,
        data: ProfessionalResponseAction,
    ) -> Booking:
        booking = await self.get_booking_by_id(booking_id)
        if not booking.assigned_professional or booking.assigned_professional.user_id != pro_user.id:
            raise ForbiddenError("You are not the assigned professional for this booking.")

        now_utc = datetime.now(timezone.utc)

        # Find active offer
        offer = next((o for o in booking.dispatch_offers if o.status == DispatchOfferStatus.OFFERED), None)

        if data.action == "accept":
            if offer:
                offer.status = DispatchOfferStatus.ACCEPTED
                offer.responded_at = now_utc

            await self.record_status_transition(
                booking=booking,
                to_status=BookingStatus.EN_ROUTE,
                actor_id=pro_user.id,
                actor_role=UserRole.PROFESSIONAL.value,
                reason="Professional accepted dispatch offer and started travel",
            )

            # Notify customer
            if booking.customer:
                await self.notifications.send_notification(
                    recipient_phone=booking.customer.phone,
                    message=f"GlamNow: Your stylist is en route! Arriving in ~{booking.eta_minutes or 20} mins.",
                    event_type="partner_en_route",
                    metadata={"booking_id": str(booking.id)},
                )
        else:
            # Decline: reassign to next best candidate
            if offer:
                offer.status = DispatchOfferStatus.DECLINED
                offer.responded_at = now_utc
                offer.decline_reason = data.decline_reason

            booking.assigned_professional_id = None
            reassigned = await self.dispatch_instant_booking(booking)
            if not reassigned:
                if booking.customer:
                    await self.notifications.send_notification(
                        recipient_phone=booking.customer.phone,
                        message="GlamNow: Partners in your area are currently busy. Rescheduling option available.",
                        event_type="assignment_failed",
                        metadata={"booking_id": str(booking.id)},
                    )

        await self.db.commit()
        return await self.get_booking_by_id(booking.id)

    async def mark_partner_arrived(
        self, booking_id: uuid.UUID, pro_user: User
    ) -> Booking:
        booking = await self.get_booking_by_id(booking_id)
        if not booking.assigned_professional or booking.assigned_professional.user_id != pro_user.id:
            raise ForbiddenError("Unauthorized: not the assigned partner.")

        await self.record_status_transition(
            booking=booking,
            to_status=BookingStatus.ARRIVED,
            actor_id=pro_user.id,
            actor_role=UserRole.PROFESSIONAL.value,
            reason="Partner arrived at customer doorstep",
        )

        if booking.customer:
            await self.notifications.send_notification(
                recipient_phone=booking.customer.phone,
                message=f"GlamNow: Your specialist has arrived! Share start OTP {booking.start_otp} to begin.",
                event_type="partner_arrived",
                metadata={"booking_id": str(booking.id)},
            )

        await self.db.commit()
        return await self.get_booking_by_id(booking.id)

    async def verify_start_otp(
        self, booking_id: uuid.UUID, pro_user: User, data: VerifyOtpRequest
    ) -> Booking:
        booking = await self.get_booking_by_id(booking_id)
        if not booking.assigned_professional or booking.assigned_professional.user_id != pro_user.id:
            raise ForbiddenError("Unauthorized.")

        if booking.status != BookingStatus.ARRIVED:
            raise ConflictError("Partner must mark arrival at doorstep before verifying OTP.")

        if booking.start_otp != data.otp:
            raise ValidationError("Invalid 4-digit start OTP provided by customer.", field="otp")

        await self.record_status_transition(
            booking=booking,
            to_status=BookingStatus.IN_PROGRESS,
            actor_id=pro_user.id,
            actor_role=UserRole.PROFESSIONAL.value,
            reason="Customer start OTP verified. Service in progress.",
        )

        await self.db.commit()
        return await self.get_booking_by_id(booking.id)

    async def complete_service(
        self, booking_id: uuid.UUID, pro_user: User, data: VerifyOtpRequest
    ) -> Booking:
        booking = await self.get_booking_by_id(booking_id)
        if not booking.assigned_professional or booking.assigned_professional.user_id != pro_user.id:
            raise ForbiddenError("Unauthorized.")

        if booking.status != BookingStatus.IN_PROGRESS:
            raise ConflictError("Service is not currently in progress.")

        if booking.completion_otp != data.otp:
            raise ValidationError("Invalid completion OTP provided.", field="otp")

        await self.record_status_transition(
            booking=booking,
            to_status=BookingStatus.COMPLETED,
            actor_id=pro_user.id,
            actor_role=UserRole.PROFESSIONAL.value,
            reason="Service completed and verified with completion OTP.",
        )

        if booking.customer:
            await self.notifications.send_notification(
                recipient_phone=booking.customer.phone,
                message=f"GlamNow: Service completed! Thank you for choosing GlamNow. Tap to rate your experience.",
                event_type="service_completed",
                metadata={"booking_id": str(booking.id)},
            )

        await self.db.commit()
        return await self.get_booking_by_id(booking.id)

    # ─────────────────────────────────────────────────────────────
    # Cancellation & Rescheduling Rules
    # ─────────────────────────────────────────────────────────────

    async def cancel_booking(
        self, booking_id: uuid.UUID, actor: User, data: CancelBookingRequest
    ) -> Booking:
        booking = await self.get_booking_by_id(booking_id)
        is_owner = booking.customer_id == actor.id
        is_admin = actor.role == UserRole.ADMIN

        if not (is_owner or is_admin):
            raise ForbiddenError("Unauthorized to cancel this booking.")

        if booking.status in (BookingStatus.COMPLETED, BookingStatus.CANCELLED):
            raise ConflictError(f"Cannot cancel booking with status {booking.status.value}.")

        if booking.status in (BookingStatus.ARRIVED, BookingStatus.IN_PROGRESS):
            raise ForbiddenError("Cannot cancel service once partner has arrived or begun treatment.")

        # Determine cancellation fee
        cancellation_fee = 0
        if booking.status == BookingStatus.EN_ROUTE:
            # Late cancellation fee once partner is en route
            cancellation_fee = 15000  # ₹150 compensation fee
            booking.cancellation_fee_paise = cancellation_fee

        booking.cancellation_reason = data.reason

        await self.record_status_transition(
            booking=booking,
            to_status=BookingStatus.CANCELLED,
            actor_id=actor.id,
            actor_role=actor.role.value,
            reason=data.reason,
            metadata={"cancellation_fee_paise": cancellation_fee},
        )

        # Release slot if scheduled
        if booking.slot_id:
            slot = await self.db.get(AppointmentSlot, booking.slot_id)
            if slot and slot.status in (SlotStatus.RESERVED, SlotStatus.BOOKED):
                slot.status = SlotStatus.AVAILABLE
                slot.reserved_by_user_id = None
                slot.reservation_expires_at = None

        await self.db.commit()
        return await self.get_booking_by_id(booking.id)

    async def reschedule_booking(
        self, booking_id: uuid.UUID, customer: User, data: RescheduleBookingRequest
    ) -> Booking:
        booking = await self.get_booking_by_id(booking_id)
        if booking.customer_id != customer.id:
            raise ForbiddenError("Unauthorized to reschedule this booking.")

        if booking.booking_type != BookingType.SCHEDULED:
            raise ValidationError("Only scheduled appointments can be rescheduled.")

        if booking.status not in (BookingStatus.CONFIRMED, BookingStatus.ASSIGNED):
            raise ConflictError(f"Cannot reschedule booking with status {booking.status.value}.")

        now_utc = datetime.now(timezone.utc)
        sched_start = _ensure_utc(booking.scheduled_start_time)
        if sched_start and sched_start - now_utc < timedelta(hours=2):
            raise ForbiddenError("Rescheduling requires at least 2 hours notice before appointment start.")

        # Verify and lock new slot
        new_slot_stmt = (
            select(AppointmentSlot)
            .where(AppointmentSlot.id == data.new_slot_id)
            .with_for_update()
        )
        new_slot = (await self.db.execute(new_slot_stmt)).scalar_one_or_none()
        if not new_slot or new_slot.status != SlotStatus.AVAILABLE:
            raise ConflictError("The new appointment slot is not available.")

        # Release old slot
        if booking.slot_id:
            old_slot = await self.db.get(AppointmentSlot, booking.slot_id)
            if old_slot:
                old_slot.status = SlotStatus.AVAILABLE
                old_slot.reserved_by_user_id = None

        # Lock new slot
        new_slot.status = SlotStatus.BOOKED
        booking.slot_id = new_slot.id
        booking.scheduled_start_time = new_slot.start_time
        booking.scheduled_end_time = new_slot.end_time
        booking.assigned_professional_id = new_slot.professional_id

        self.db.add(
            BookingStatusHistory(
                booking_id=booking.id,
                from_status=booking.status,
                to_status=booking.status,
                actor_id=customer.id,
                actor_role=UserRole.CUSTOMER.value,
                reason="Customer rescheduled appointment slot",
                metadata_json={"new_slot_id": str(new_slot.id)},
                created_at=now_utc,
            )
        )

        await self.db.commit()
        return await self.get_booking_by_id(booking.id)
