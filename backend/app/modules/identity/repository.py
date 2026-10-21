"""
Identity database repositories with strict user-tenant isolation.
"""

from __future__ import annotations

from datetime import datetime, timezone
import uuid

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.models import ConsentRecord, RefreshToken, SavedAddress, User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_phone(self, phone: str) -> User | None:
        result = await self.session.execute(select(User).where(User.phone == phone))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_identifier(self, identifier: str) -> User | None:
        """Finds user by phone or email."""
        stmt = select(User).where((User.phone == identifier) | (User.email == identifier))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        return user

    async def update(self, user: User) -> User:
        await self.session.flush()
        return user


class AddressRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_by_user(self, user_id: uuid.UUID) -> list[SavedAddress]:
        stmt = (
            select(SavedAddress)
            .where(SavedAddress.user_id == user_id)
            .order_by(SavedAddress.is_default.desc(), SavedAddress.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_user_address(self, address_id: uuid.UUID, user_id: uuid.UUID) -> SavedAddress | None:
        """
        Retrieves address only if it belongs to the given user_id.
        Prevents cross-customer access.
        """
        stmt = select(SavedAddress).where(
            SavedAddress.id == address_id,
            SavedAddress.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, address: SavedAddress) -> SavedAddress:
        if address.is_default:
            # Unset existing default for this user
            await self.session.execute(
                update(SavedAddress)
                .where(SavedAddress.user_id == address.user_id)
                .values(is_default=False)
            )
        self.session.add(address)
        await self.session.flush()
        return address

    async def update(self, address: SavedAddress) -> SavedAddress:
        if address.is_default:
            await self.session.execute(
                update(SavedAddress)
                .where(SavedAddress.user_id == address.user_id, SavedAddress.id != address.id)
                .values(is_default=False)
            )
        await self.session.flush()
        return address

    async def delete_user_address(self, address_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        stmt = delete(SavedAddress).where(
            SavedAddress.id == address_id,
            SavedAddress.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        return bool(result.rowcount > 0)


class ConsentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record_consent(self, consent: ConsentRecord) -> ConsentRecord:
        self.session.add(consent)
        await self.session.flush()
        return consent

    async def list_user_consents(self, user_id: uuid.UUID) -> list[ConsentRecord]:
        stmt = (
            select(ConsentRecord)
            .where(ConsentRecord.user_id == user_id)
            .order_by(ConsentRecord.granted_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class TokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def store_refresh_token(self, token_entity: RefreshToken) -> RefreshToken:
        self.session.add(token_entity)
        await self.session.flush()
        return token_entity

    async def find_valid_token(self, token_hash: str) -> RefreshToken | None:
        now = datetime.now(timezone.utc)
        stmt = select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.is_revoked == False,  # noqa: E712
            RefreshToken.expires_at > now,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke_token(self, token_hash: str) -> bool:
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .values(is_revoked=True)
        )
        result = await self.session.execute(stmt)
        return bool(result.rowcount > 0)

    async def revoke_all_user_tokens(self, user_id: uuid.UUID) -> int:
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .values(is_revoked=True)
        )
        result = await self.session.execute(stmt)
        return result.rowcount
