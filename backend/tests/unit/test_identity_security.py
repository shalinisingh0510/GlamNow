"""
Unit tests for identity security, password hashing, JWT lifecycles, and authorization policies.
"""

from datetime import timedelta
import uuid
import pytest

from app.core.errors import ForbiddenError, UnauthorizedError
from app.modules.identity.dependencies import (
    verify_booking_access,
    verify_catalog_mutation_permission,
    verify_customer_ownership,
    verify_tailoring_measurement_access,
)
from app.modules.identity.enums import UserRole
from app.modules.identity.models import User
from app.modules.identity.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    hash_password,
    hash_token,
    verify_password,
)


def test_password_hash_and_verify():
    password = "SuperSecret123!"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword123!", hashed) is False


def test_jwt_access_token_lifecycle():
    user_id = uuid.uuid4()
    role = UserRole.CUSTOMER

    token, expires_at = create_access_token(user_id, role)
    assert isinstance(token, str)

    payload = decode_access_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["role"] == role.value
    assert payload["type"] == "access"


def test_expired_jwt_raises_unauthorized():
    user_id = uuid.uuid4()
    # Expired 5 minutes ago
    token, _ = create_access_token(user_id, UserRole.CUSTOMER, expires_delta=timedelta(minutes=-5))

    with pytest.raises(UnauthorizedError) as exc_info:
        decode_access_token(token)
    assert "expired" in str(exc_info.value).lower()


def test_invalid_jwt_raises_unauthorized():
    with pytest.raises(UnauthorizedError):
        decode_access_token("invalid.jwt.token")


def test_refresh_token_hashing():
    raw_token, expires_at = create_refresh_token(uuid.uuid4())
    digest1 = hash_token(raw_token)
    digest2 = hash_token(raw_token)

    assert digest1 == digest2
    assert len(digest1) == 64  # SHA-256 hex string


# ─── Authorization Policy Tests ──────────────────────────────────────────────

def test_customer_ownership_policy():
    customer_id = uuid.uuid4()
    other_customer_id = uuid.uuid4()

    customer_user = User(
        id=customer_id,
        phone="+919876543210",
        full_name="Alice",
        role=UserRole.CUSTOMER,
        password_hash="dummy",
    )
    admin_user = User(
        id=uuid.uuid4(),
        phone="+919876543211",
        full_name="Admin",
        role=UserRole.ADMIN,
        password_hash="dummy",
    )

    # Customer accessing their own resource: Allowed
    verify_customer_ownership(customer_id, customer_user)

    # Admin accessing customer resource: Allowed
    verify_customer_ownership(customer_id, admin_user)

    # Customer accessing another customer's resource: Forbidden
    with pytest.raises(ForbiddenError):
        verify_customer_ownership(other_customer_id, customer_user)


def test_booking_access_policy():
    customer_id = uuid.uuid4()
    pro_id = uuid.uuid4()
    unassigned_pro_id = uuid.uuid4()

    customer = User(id=customer_id, phone="+919876543210", full_name="Alice", role=UserRole.CUSTOMER, password_hash="x")
    assigned_pro = User(id=pro_id, phone="+919876543211", full_name="Stylist Priya", role=UserRole.PROFESSIONAL, password_hash="x")
    unassigned_pro = User(id=unassigned_pro_id, phone="+919876543212", full_name="Stylist Ramesh", role=UserRole.PROFESSIONAL, password_hash="x")
    ops_staff = User(id=uuid.uuid4(), phone="+919876543213", full_name="Ops Team", role=UserRole.OPERATIONS_STAFF, password_hash="x")

    # Customer who booked: Allowed
    verify_booking_access(customer_id, pro_id, customer)

    # Assigned professional: Allowed
    verify_booking_access(customer_id, pro_id, assigned_pro)

    # Operations staff: Allowed
    verify_booking_access(customer_id, pro_id, ops_staff)

    # Unassigned professional: Forbidden
    with pytest.raises(ForbiddenError):
        verify_booking_access(customer_id, pro_id, unassigned_pro)


def test_tailoring_measurement_privacy_policy():
    customer_id = uuid.uuid4()
    tailor_id = uuid.uuid4()
    other_pro_id = uuid.uuid4()

    customer = User(id=customer_id, phone="+919876543210", full_name="Customer", role=UserRole.CUSTOMER, password_hash="x")
    master_tailor = User(id=tailor_id, phone="+919876543211", full_name="Master Tailor", role=UserRole.PROFESSIONAL, password_hash="x")
    other_pro = User(id=other_pro_id, phone="+919876543212", full_name="Stylist", role=UserRole.PROFESSIONAL, password_hash="x")

    # Customer viewing own measurements: Allowed
    verify_tailoring_measurement_access(customer_id, tailor_id, customer)

    # Assigned master tailor during active job window: Allowed
    verify_tailoring_measurement_access(customer_id, tailor_id, master_tailor, is_job_active=True)

    # Assigned master tailor after job closed: Forbidden (retention limit)
    with pytest.raises(ForbiddenError):
        verify_tailoring_measurement_access(customer_id, tailor_id, master_tailor, is_job_active=False)

    # Other unassigned professional: Forbidden
    with pytest.raises(ForbiddenError):
        verify_tailoring_measurement_access(customer_id, tailor_id, other_pro)


def test_catalog_mutation_policy():
    admin = User(id=uuid.uuid4(), phone="+919876543210", full_name="Admin", role=UserRole.ADMIN, password_hash="x")
    ops = User(id=uuid.uuid4(), phone="+919876543211", full_name="Ops", role=UserRole.OPERATIONS_STAFF, password_hash="x")
    customer = User(id=uuid.uuid4(), phone="+919876543212", full_name="Customer", role=UserRole.CUSTOMER, password_hash="x")

    verify_catalog_mutation_permission(admin)
    verify_catalog_mutation_permission(ops)

    with pytest.raises(ForbiddenError):
        verify_catalog_mutation_permission(customer)
