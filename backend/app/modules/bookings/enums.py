"""
Enums for booking lifecycle, dispatch modes, and payment transactions.
"""

from __future__ import annotations

import enum


class BookingType(str, enum.Enum):
    """Dispatch mode: Instant express visit vs Scheduled premium slot."""
    INSTANT = "instant"          # Quick-commerce 15-30m auto-match
    SCHEDULED = "scheduled"      # Reserved specific professional and date/time slot


class BookingStatus(str, enum.Enum):
    """
    Validated state machine lifecycle for bookings.
    """
    HOLD_RESERVED = "hold_reserved"          # Temporary 10m checkout hold
    CONFIRMED = "confirmed"                  # Payment authorized / COD verified
    DISPATCHING = "dispatching"              # Automated nearby pro search & offer
    ASSIGNED = "assigned"                    # Professional assigned
    EN_ROUTE = "en_route"                    # Professional en route with live ETA
    ARRIVED = "arrived"                      # Partner arrived at customer doorstep
    IN_PROGRESS = "in_progress"              # 4-digit start OTP verified
    COMPLETED = "completed"                  # Service completed & verified
    CANCELLED = "cancelled"                  # Cancelled under SLA policy
    FAILED_ASSIGNMENT = "failed_assignment"  # No eligible partner accepted
    EXPIRED = "expired"                      # Hold TTL expired without payment


class PaymentStatus(str, enum.Enum):
    """Payment transaction states."""
    PENDING = "pending"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentMethod(str, enum.Enum):
    """Supported payment modes."""
    ONLINE_UPI = "online_upi"
    CARD = "card"
    NET_BANKING = "net_banking"
    CASH_ON_SERVICE = "cash_on_service"


class DispatchOfferStatus(str, enum.Enum):
    """State of a dispatch offer sent to a candidate professional."""
    OFFERED = "offered"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    TIMED_OUT = "timed_out"
