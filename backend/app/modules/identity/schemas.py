"""
Pydantic v2 schemas for identity, authentication, profile, addresses, and consent.
"""

from __future__ import annotations

from datetime import datetime
import re
import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.modules.identity.enums import AddressLabel, ConsentType, UserRole

# Indian mobile phone regex: optionally +91, followed by 6, 7, 8, or 9 and 9 digits
INDIAN_PHONE_REGEX = re.compile(r"^(\+91)?[6-9]\d{9}$")
# 6-digit Indian PIN code regex
INDIAN_PINCODE_REGEX = re.compile(r"^[1-9][0-9]{5}$")


class UserSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    phone: str
    email: EmailStr | None = None
    full_name: str
    role: UserRole
    is_active: bool
    is_verified: bool


class UserRegisterRequest(BaseModel):
    phone: str = Field(..., description="Indian 10-digit mobile number with or without +91")
    email: EmailStr | None = None
    full_name: str = Field(..., min_length=2, max_length=150)
    password: str = Field(..., min_length=8, max_length=128)
    role: UserRole = Field(default=UserRole.CUSTOMER, description="Registration role; only customer allowed via public endpoint")
    consent_terms: bool = Field(..., description="Must be True to comply with Terms of Service")
    consent_privacy: bool = Field(..., description="Must be True to comply with DPDP Privacy Policy")

    @field_validator("phone")
    @classmethod
    def validate_indian_phone(cls, v: str) -> str:
        clean = v.replace(" ", "").replace("-", "")
        if not INDIAN_PHONE_REGEX.match(clean):
            raise ValueError("Phone number must be a valid 10-digit Indian mobile number")
        # Standardize to format +91XXXXXXXXXX
        if not clean.startswith("+91"):
            clean = f"+91{clean}"
        return clean

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v) or not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one uppercase letter and one digit")
        return v

    @field_validator("consent_terms", "consent_privacy")
    @classmethod
    def validate_mandatory_consents(cls, v: bool, info) -> bool:
        if not v:
            raise ValueError(f"{info.field_name} must be accepted to register")
        return v


class UserLoginRequest(BaseModel):
    identifier: str = Field(..., description="Registered mobile number or email address")
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in_seconds: int
    user: UserSummary


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    phone: str
    email: EmailStr | None = None
    full_name: str
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime


class UserProfileUpdateRequest(BaseModel):
    full_name: str | None = Field(None, min_length=2, max_length=150)
    email: EmailStr | None = None


class SavedAddressCreateRequest(BaseModel):
    label: AddressLabel = AddressLabel.HOME
    recipient_name: str | None = Field(None, max_length=150)
    recipient_phone: str | None = Field(None, max_length=20)
    address_line1: str = Field(..., min_length=5, max_length=255)
    address_line2: str | None = Field(None, max_length=255)
    city: str = Field(default="Bengaluru", max_length=100)
    state: str = Field(default="Karnataka", max_length=100)
    pincode: str = Field(..., description="6-digit Indian PIN code")
    landmark: str | None = Field(None, max_length=150)
    latitude: float | None = None
    longitude: float | None = None
    is_default: bool = False

    @field_validator("pincode")
    @classmethod
    def validate_pincode(cls, v: str) -> str:
        clean = v.strip()
        if not INDIAN_PINCODE_REGEX.match(clean):
            raise ValueError("Pincode must be a valid 6-digit Indian PIN code")
        return clean


class SavedAddressUpdateRequest(BaseModel):
    label: AddressLabel | None = None
    recipient_name: str | None = None
    recipient_phone: str | None = None
    address_line1: str | None = Field(None, min_length=5, max_length=255)
    address_line2: str | None = None
    city: str | None = None
    state: str | None = None
    pincode: str | None = None
    landmark: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    is_default: bool | None = None

    @field_validator("pincode")
    @classmethod
    def validate_pincode_optional(cls, v: str | None) -> str | None:
        if v is not None:
            clean = v.strip()
            if not INDIAN_PINCODE_REGEX.match(clean):
                raise ValueError("Pincode must be a valid 6-digit Indian PIN code")
            return clean
        return None


class SavedAddressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    label: AddressLabel
    recipient_name: str | None = None
    recipient_phone: str | None = None
    address_line1: str
    address_line2: str | None = None
    city: str
    state: str
    pincode: str
    landmark: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    is_default: bool
    created_at: datetime


class ConsentCreateRequest(BaseModel):
    consent_type: ConsentType
    granted: bool = True
    version: str = "v1.0"


class ConsentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    consent_type: ConsentType
    granted: bool
    version: str
    granted_at: datetime
