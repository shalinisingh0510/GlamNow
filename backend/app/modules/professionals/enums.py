"""
Enums for professionals, schedules, and appointment availability.
"""

from __future__ import annotations

import enum


class VerificationStatus(str, enum.Enum):
    """
    KYC and skill verification states for onboarding professionals.
    """
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    VERIFIED = "verified"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


class SlotStatus(str, enum.Enum):
    """
    Appointment slot booking status.
    """
    AVAILABLE = "available"
    RESERVED = "reserved"      # Temporary lock during checkout
    BOOKED = "booked"          # Confirmed order
    BLOCKED = "blocked"        # Personal time off or break


class DayOfWeek(str, enum.Enum):
    """Day of week for recurring weekly schedules."""
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"
