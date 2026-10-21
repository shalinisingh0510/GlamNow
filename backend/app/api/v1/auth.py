"""
Authentication, profile, addresses, and DPDP consent endpoints.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db_session
from app.modules.identity.dependencies import get_current_user, require_role
from app.modules.identity.enums import UserRole
from app.modules.identity.models import User
from app.modules.identity.schemas import (
    ConsentCreateRequest,
    ConsentResponse,
    SavedAddressCreateRequest,
    SavedAddressResponse,
    SavedAddressUpdateRequest,
    TokenRefreshRequest,
    TokenResponse,
    UserLoginRequest,
    UserProfileUpdateRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.modules.identity.service import IdentityService

router = APIRouter(prefix="/auth", tags=["auth"])


def get_identity_service(session: AsyncSession = Depends(get_db_session)) -> IdentityService:
    return IdentityService(session)


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new customer account",
)
async def register(
    data: UserRegisterRequest,
    request: Request,
    service: IdentityService = Depends(get_identity_service),
) -> TokenResponse:
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return await service.register_customer(data, ip_address=ip_address, user_agent=user_agent)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate via phone/email and password",
)
async def login(
    data: UserLoginRequest,
    service: IdentityService = Depends(get_identity_service),
) -> TokenResponse:
    return await service.login(data.identifier, data.password)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Rotate refresh token and issue new access token",
)
async def refresh_token(
    data: TokenRefreshRequest,
    service: IdentityService = Depends(get_identity_service),
) -> TokenResponse:
    return await service.refresh_token(data.refresh_token)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke active refresh token session",
)
async def logout(
    data: TokenRefreshRequest,
    service: IdentityService = Depends(get_identity_service),
) -> Response:
    await service.logout(data.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current authenticated user profile",
)
async def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update authenticated user profile",
)
async def update_me(
    data: UserProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    service: IdentityService = Depends(get_identity_service),
) -> UserResponse:
    user = await service.update_profile(current_user.id, data)
    return UserResponse.model_validate(user)


# ─── Saved Addresses ─────────────────────────────────────────────────────────

@router.get(
    "/addresses",
    response_model=list[SavedAddressResponse],
    summary="List saved delivery addresses for current customer",
)
async def list_addresses(
    current_user: User = Depends(get_current_user),
    service: IdentityService = Depends(get_identity_service),
) -> list[SavedAddressResponse]:
    addresses = await service.list_addresses(current_user.id)
    return [SavedAddressResponse.model_validate(a) for a in addresses]


@router.post(
    "/addresses",
    response_model=SavedAddressResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new saved delivery address",
)
async def create_address(
    data: SavedAddressCreateRequest,
    current_user: User = Depends(get_current_user),
    service: IdentityService = Depends(get_identity_service),
) -> SavedAddressResponse:
    address = await service.add_address(current_user.id, data)
    return SavedAddressResponse.model_validate(address)


@router.patch(
    "/addresses/{address_id}",
    response_model=SavedAddressResponse,
    summary="Update a saved address (scoped to current customer)",
)
async def update_address(
    address_id: uuid.UUID,
    data: SavedAddressUpdateRequest,
    current_user: User = Depends(get_current_user),
    service: IdentityService = Depends(get_identity_service),
) -> SavedAddressResponse:
    address = await service.update_address(address_id, current_user.id, data)
    return SavedAddressResponse.model_validate(address)


@router.delete(
    "/addresses/{address_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a saved address (scoped to current customer)",
)
async def delete_address(
    address_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: IdentityService = Depends(get_identity_service),
) -> Response:
    await service.delete_address(address_id, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ─── DPDP Consent Records ───────────────────────────────────────────────────

@router.post(
    "/consent",
    response_model=ConsentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record customer consent under DPDP Act 2023",
)
async def record_consent(
    data: ConsentCreateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    service: IdentityService = Depends(get_identity_service),
) -> ConsentResponse:
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    record = await service.record_consent(
        current_user.id, data, ip_address=ip_address, user_agent=user_agent
    )
    return ConsentResponse.model_validate(record)


# ─── RBAC Role Escalation Test Route ─────────────────────────────────────────

@router.get(
    "/admin/audit-probe",
    summary="Admin-only diagnostic probe to test role escalation rejection",
)
async def admin_probe(
    admin_user: User = Depends(require_role(UserRole.ADMIN)),
) -> dict[str, str]:
    return {"status": "ok", "message": f"Welcome Administrator {admin_user.full_name}"}
