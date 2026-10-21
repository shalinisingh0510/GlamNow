"""
Identity service orchestrating business rules, password verification, token issuance,
and cross-tenant isolation.
"""

from __future__ import annotations

from datetime import datetime, timezone
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError
from app.modules.identity.enums import ConsentType, UserRole
from app.modules.identity.models import ConsentRecord, RefreshToken, SavedAddress, User
from app.modules.identity.repository import (
    AddressRepository,
    ConsentRepository,
    TokenRepository,
    UserRepository,
)
from app.modules.identity.schemas import (
    ConsentCreateRequest,
    SavedAddressCreateRequest,
    SavedAddressUpdateRequest,
    TokenResponse,
    UserProfileUpdateRequest,
    UserRegisterRequest,
    UserSummary,
)
from app.modules.identity.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)


class IdentityService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)
        self.address_repo = AddressRepository(session)
        self.consent_repo = ConsentRepository(session)
        self.token_repo = TokenRepository(session)

    async def register_customer(
        self,
        data: UserRegisterRequest,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> TokenResponse:
        """
        Registers a new customer, records mandatory DPDP consent, and returns auth tokens.
        """
        # Ensure public registration cannot escalate role
        if data.role != UserRole.CUSTOMER:
            raise ForbiddenError(message="Public registration is only available for customer accounts")

        # 1. Check existing phone
        existing_phone = await self.user_repo.get_by_phone(data.phone)
        if existing_phone is not None:
            raise ConflictError(message="An account with this mobile number already exists")

        # 2. Check existing email
        if data.email:
            existing_email = await self.user_repo.get_by_email(data.email)
            if existing_email is not None:
                raise ConflictError(message="An account with this email address already exists")

        # 3. Hash password with Argon2
        hashed_pw = hash_password(data.password)

        # 4. Create User entity
        user = User(
            phone=data.phone,
            email=data.email,
            full_name=data.full_name,
            role=UserRole.CUSTOMER,
            password_hash=hashed_pw,
            is_active=True,
            is_verified=False,
        )
        await self.user_repo.create(user)

        # 5. Record mandatory Terms and Privacy consents
        for c_type in [ConsentType.TERMS_OF_SERVICE, ConsentType.PRIVACY_POLICY]:
            consent = ConsentRecord(
                user_id=user.id,
                consent_type=c_type,
                granted=True,
                version="v1.0",
                ip_address=ip_address,
                user_agent=user_agent,
            )
            await self.consent_repo.record_consent(consent)

        # 6. Issue access and refresh tokens
        return await self._issue_token_response(user)

    async def login(self, identifier: str, plain_password: str) -> TokenResponse:
        """
        Authenticates a user via phone or email and password.
        Uses constant-time comparison to prevent timing side-channel attacks.
        """
        clean_id = identifier.strip()
        if clean_id.isdigit() and len(clean_id) == 10:
            clean_id = f"+91{clean_id}"

        user = await self.user_repo.get_by_identifier(clean_id)
        if user is None:
            # Timing attack prevention dummy verify
            verify_password("dummy", "$argon2id$v=19$m=65536,t=3,p=4$dummy$dummy")
            raise UnauthorizedError(message="Invalid mobile number, email, or password")

        if not verify_password(plain_password, user.password_hash):
            raise UnauthorizedError(message="Invalid mobile number, email, or password")

        if not user.is_active:
            raise ForbiddenError(message="Account has been suspended or deactivated. Please contact support.")

        return await self._issue_token_response(user)

    async def refresh_token(self, raw_refresh_token: str) -> TokenResponse:
        """
        Rotates a refresh token and issues a new access token.
        """
        token_digest = hash_token(raw_refresh_token)
        token_entity = await self.token_repo.find_valid_token(token_digest)
        if token_entity is None:
            raise UnauthorizedError(message="Invalid or expired session. Please log in again.")

        user = await self.user_repo.get_by_id(token_entity.user_id)
        if user is None or not user.is_active:
            raise UnauthorizedError(message="User account is inactive or not found")

        # Revoke the used refresh token (rotation)
        await self.token_repo.revoke_token(token_digest)

        return await self._issue_token_response(user)

    async def logout(self, raw_refresh_token: str) -> bool:
        token_digest = hash_token(raw_refresh_token)
        return await self.token_repo.revoke_token(token_digest)

    async def get_user_profile(self, user_id: uuid.UUID) -> User:
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError(message="User not found")
        return user

    async def update_profile(self, user_id: uuid.UUID, data: UserProfileUpdateRequest) -> User:
        user = await self.get_user_profile(user_id)
        if data.full_name is not None:
            user.full_name = data.full_name
        if data.email is not None and data.email != user.email:
            existing = await self.user_repo.get_by_email(data.email)
            if existing is not None and existing.id != user.id:
                raise ConflictError(message="This email is already in use by another account")
            user.email = data.email

        return await self.user_repo.update(user)

    # ─── Address Management (With strict tenant isolation) ───────────────────
    async def list_addresses(self, user_id: uuid.UUID) -> list[SavedAddress]:
        return await self.address_repo.list_by_user(user_id)

    async def add_address(self, user_id: uuid.UUID, data: SavedAddressCreateRequest) -> SavedAddress:
        address = SavedAddress(
            user_id=user_id,
            label=data.label,
            recipient_name=data.recipient_name,
            recipient_phone=data.recipient_phone,
            address_line1=data.address_line1,
            address_line2=data.address_line2,
            city=data.city,
            state=data.state,
            pincode=data.pincode,
            landmark=data.landmark,
            latitude=data.latitude,
            longitude=data.longitude,
            is_default=data.is_default,
        )
        return await self.address_repo.create(address)

    async def get_address(self, address_id: uuid.UUID, user_id: uuid.UUID) -> SavedAddress:
        address = await self.address_repo.get_user_address(address_id, user_id)
        if address is None:
            # Return NotFoundError to prevent leaking existence of other customer addresses
            raise NotFoundError(message="Saved address not found")
        return address

    async def update_address(
        self, address_id: uuid.UUID, user_id: uuid.UUID, data: SavedAddressUpdateRequest
    ) -> SavedAddress:
        address = await self.get_address(address_id, user_id)
        update_dict = data.model_dump(exclude_unset=True)
        for key, val in update_dict.items():
            setattr(address, key, val)
        return await self.address_repo.update(address)

    async def delete_address(self, address_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        deleted = await self.address_repo.delete_user_address(address_id, user_id)
        if not deleted:
            raise NotFoundError(message="Saved address not found")
        return True

    # ─── Consent Logging ─────────────────────────────────────────────────────
    async def record_consent(
        self,
        user_id: uuid.UUID,
        data: ConsentCreateRequest,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> ConsentRecord:
        consent = ConsentRecord(
            user_id=user_id,
            consent_type=data.consent_type,
            granted=data.granted,
            version=data.version,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return await self.consent_repo.record_consent(consent)

    async def list_consents(self, user_id: uuid.UUID) -> list[ConsentRecord]:
        return await self.consent_repo.list_user_consents(user_id)

    # ─── Token Issuance Helper ───────────────────────────────────────────────
    async def _issue_token_response(self, user: User) -> TokenResponse:
        access_token, expires_at = create_access_token(user.id, user.role)
        raw_refresh_token, rt_expires_at = create_refresh_token(user.id)

        # Store hashed refresh token in database
        rt_entity = RefreshToken(
            user_id=user.id,
            token_hash=hash_token(raw_refresh_token),
            expires_at=rt_expires_at,
            is_revoked=False,
        )
        await self.token_repo.store_refresh_token(rt_entity)

        expires_in = int((expires_at - datetime.now(timezone.utc)).total_seconds())

        return TokenResponse(
            access_token=access_token,
            refresh_token=raw_refresh_token,
            token_type="bearer",
            expires_in_seconds=3600,
            user=UserSummary.model_validate(user),
        )
