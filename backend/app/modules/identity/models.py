"""
Identity domain ORM models.
"""

from __future__ import annotations

from datetime import datetime, timezone
import uuid

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.modules.identity.enums import AddressLabel, ConsentType, UserRole


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    User entity representing customers, professionals, operations staff, and admins.
    """

    __tablename__ = "users"

    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role_enum", native_enum=False),
        default=UserRole.CUSTOMER,
        nullable=False,
        index=True,
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    saved_addresses: Mapped[list[SavedAddress]] = relationship(
        "SavedAddress", back_populates="user", cascade="all, delete-orphan"
    )
    consents: Mapped[list[ConsentRecord]] = relationship(
        "ConsentRecord", back_populates="user", cascade="all, delete-orphan"
    )
    refresh_tokens: Mapped[list[RefreshToken]] = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )


class SavedAddress(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Customer saved service delivery addresses.
    """

    __tablename__ = "saved_addresses"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    label: Mapped[AddressLabel] = mapped_column(
        Enum(AddressLabel, name="address_label_enum", native_enum=False),
        default=AddressLabel.HOME,
        nullable=False,
    )
    recipient_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    recipient_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    address_line1: Mapped[str] = mapped_column(String(255), nullable=False)
    address_line2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False, default="Bengaluru")
    state: Mapped[str] = mapped_column(String(100), nullable=False, default="Karnataka")
    pincode: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    landmark: Mapped[str | None] = mapped_column(String(150), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    user: Mapped[User] = relationship("User", back_populates="saved_addresses")


class ConsentRecord(Base, UUIDPrimaryKeyMixin):
    """
    DPDP Act 2023 compliance consent audit log.
    """

    __tablename__ = "consent_records"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    consent_type: Mapped[ConsentType] = mapped_column(
        Enum(ConsentType, name="consent_type_enum", native_enum=False),
        nullable=False,
    )
    granted: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    version: Mapped[str] = mapped_column(String(20), default="v1.0", nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped[User] = relationship("User", back_populates="consents")


class RefreshToken(Base, UUIDPrimaryKeyMixin):
    """
    Revocable session refresh tokens for secure JWT rotation.
    """

    __tablename__ = "refresh_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped[User] = relationship("User", back_populates="refresh_tokens")


# Composite index for user addresses
Index("ix_saved_addresses_user_pincode", SavedAddress.user_id, SavedAddress.pincode)
