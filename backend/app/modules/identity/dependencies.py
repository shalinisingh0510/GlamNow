"""
Server-enforced authentication dependencies and resource authorization policies.

CRITICAL INVARIANT: Never trust frontend role claims. All authorization checks
are strictly evaluated on the server using authenticated database records.
"""

from __future__ import annotations

from typing import Annotated, Callable
import uuid

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ForbiddenError, UnauthorizedError
from app.db import get_db_session
from app.modules.identity.enums import UserRole
from app.modules.identity.models import User
from app.modules.identity.repository import UserRepository
from app.modules.identity.security import decode_access_token


async def get_current_user(
    authorization: Annotated[str | None, Header(description="Bearer <JWT>")] = None,
    session: AsyncSession = Depends(get_db_session),
) -> User:
    """
    Extracts Bearer JWT from Authorization header, validates signature and expiration,
    and loads the active User record from the database.
    """
    if not authorization:
        raise UnauthorizedError(message="Authentication credentials were not provided")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise UnauthorizedError(message="Invalid authorization header format. Expected 'Bearer <token>'")

    token = parts[1]
    payload = decode_access_token(token)

    try:
        user_id = uuid.UUID(payload["sub"])
    except (ValueError, KeyError):
        raise UnauthorizedError(message="Malformed token identifier")

    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(user_id)
    if user is None:
        raise UnauthorizedError(message="User account no longer exists")

    if not user.is_active:
        raise ForbiddenError(message="Account has been deactivated. Please contact support.")

    return user


def require_role(*allowed_roles: UserRole) -> Callable[[User], User]:
    """
    Dependency factory that restricts endpoint access to specified roles.
    Raises HTTP 403 Forbidden if the user's role is not in allowed_roles.
    """
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise ForbiddenError(
                message=f"Access denied. Requires one of roles: {[r.value for r in allowed_roles]}"
            )
        return current_user

    return role_checker


# ─── Granular Resource Authorization Policies ────────────────────────────────

def verify_customer_ownership(resource_owner_id: uuid.UUID, current_user: User) -> None:
    """
    Enforces that customers can only read/write their own resources.
    Admins and operations staff can bypass for operational interventions.
    """
    if current_user.role in (UserRole.ADMIN, UserRole.OPERATIONS_STAFF):
        return

    if current_user.id != resource_owner_id:
        raise ForbiddenError(message="Access denied: You do not own this resource")


def verify_booking_access(
    booking_customer_id: uuid.UUID,
    assigned_pro_id: uuid.UUID | None,
    current_user: User,
) -> None:
    """
    Authorization policy for service bookings:
    - Customer can view/manage if they placed the booking.
    - Assigned professional can view/manage if assigned to the booking.
    - Admin & operations staff can view/intervene.
    """
    if current_user.role in (UserRole.ADMIN, UserRole.OPERATIONS_STAFF):
        return

    if current_user.role == UserRole.CUSTOMER and current_user.id == booking_customer_id:
        return

    if current_user.role == UserRole.PROFESSIONAL and assigned_pro_id and current_user.id == assigned_pro_id:
        return

    raise ForbiddenError(message="Access denied: You are not authorized to view or manage this booking")


def verify_tailoring_measurement_access(
    customer_id: uuid.UUID,
    assigned_master_tailor_id: uuid.UUID | None,
    current_user: User,
    is_job_active: bool = True,
) -> None:
    """
    DPDP Act Compliance: Body measurements and fitting references are sensitive personal data.
    - Customer has perpetual access to their own measurements.
    - Assigned master tailor has access ONLY while the tailoring job is actively in progress.
    - General staff or unassigned professionals are strictly denied access.
    """
    if current_user.role == UserRole.ADMIN:
        return

    if current_user.id == customer_id:
        return

    if (
        current_user.role == UserRole.PROFESSIONAL
        and assigned_master_tailor_id
        and current_user.id == assigned_master_tailor_id
        and is_job_active
    ):
        return

    raise ForbiddenError(
        message="Access denied: Sensitive tailoring measurement data is restricted under privacy policy"
    )


def verify_catalog_mutation_permission(current_user: User) -> None:
    """
    Strictly permits only Administrator and Operations Staff to modify the catalog.
    """
    if current_user.role not in (UserRole.ADMIN, UserRole.OPERATIONS_STAFF):
        raise ForbiddenError(message="Admin or Operations Staff privileges required to modify catalog")
