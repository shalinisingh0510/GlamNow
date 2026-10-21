"""
Identity and Access Control Enums.
"""

from __future__ import annotations

import enum


class UserRole(str, enum.Enum):
    """
    Server-enforced user roles.

    Frontend claims are advisory only; the server strictly validates
    the role from the authenticated session.
    """
    CUSTOMER = "customer"
    PROFESSIONAL = "professional"
    OPERATIONS_STAFF = "operations_staff"
    ADMIN = "admin"


class ConsentType(str, enum.Enum):
    """
    Consent types tracked under the DPDP Act 2023.
    """
    TERMS_OF_SERVICE = "terms_of_service"
    PRIVACY_POLICY = "privacy_policy"
    MEASUREMENT_STORAGE = "measurement_storage"
    MARKETING_SMS = "marketing_sms"


class AddressLabel(str, enum.Enum):
    """
    User-friendly labels for saved delivery addresses.
    """
    HOME = "home"
    WORK = "work"
    OTHER = "other"
