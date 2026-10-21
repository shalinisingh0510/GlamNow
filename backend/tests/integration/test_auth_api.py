"""
Integration tests for authentication, address management, and server-enforced RBAC.
"""

from datetime import timedelta
import pytest
from httpx import AsyncClient

from app.modules.identity.enums import UserRole
from app.modules.identity.models import User
from app.modules.identity.security import create_access_token, hash_password


@pytest.mark.asyncio
async def test_customer_registration_happy_path(client: AsyncClient):
    payload = {
        "phone": "9876543210",
        "email": "customer1@glamnow.in",
        "full_name": "Pooja Sharma",
        "password": "SecurePassword123!",
        "role": "customer",
        "consent_terms": True,
        "consent_privacy": True,
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["phone"] == "+919876543210"
    assert data["user"]["role"] == "customer"


@pytest.mark.asyncio
async def test_registration_validation_errors(client: AsyncClient):
    # 1. Invalid Indian phone number
    res1 = await client.post(
        "/api/v1/auth/register",
        json={
            "phone": "12345",
            "full_name": "Invalid Phone",
            "password": "Password123!",
            "consent_terms": True,
            "consent_privacy": True,
        },
    )
    assert res1.status_code == 422

    # 2. Weak password (less than 8 chars or missing numbers/uppercase)
    res2 = await client.post(
        "/api/v1/auth/register",
        json={
            "phone": "9876543211",
            "full_name": "Weak Pw",
            "password": "weak",
            "consent_terms": True,
            "consent_privacy": True,
        },
    )
    assert res2.status_code == 422

    # 3. Missing mandatory privacy consent
    res3 = await client.post(
        "/api/v1/auth/register",
        json={
            "phone": "9876543212",
            "full_name": "No Consent",
            "password": "Password123!",
            "consent_terms": True,
            "consent_privacy": False,
        },
    )
    assert res3.status_code == 422


@pytest.mark.asyncio
async def test_registration_duplicate_phone_rejected(client: AsyncClient):
    payload = {
        "phone": "9876543220",
        "full_name": "Duplicate User",
        "password": "Password123!",
        "consent_terms": True,
        "consent_privacy": True,
    }
    res1 = await client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    # Attempt duplicate
    res2 = await client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["errors"][0]["message"]


@pytest.mark.asyncio
async def test_login_and_token_refresh(client: AsyncClient):
    # Register first
    await client.post(
        "/api/v1/auth/register",
        json={
            "phone": "9876543230",
            "email": "loginuser@glamnow.in",
            "full_name": "Login User",
            "password": "Password123!",
            "consent_terms": True,
            "consent_privacy": True,
        },
    )

    # Login with phone
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"identifier": "9876543230", "password": "Password123!"},
    )
    assert login_res.status_code == 200
    token_data = login_res.json()
    access_token = token_data["access_token"]
    refresh_token = token_data["refresh_token"]

    # Access protected /auth/me
    me_res = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_res.status_code == 200
    assert me_res.json()["phone"] == "+919876543230"

    # Refresh token rotation
    refresh_res = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_res.status_code == 200
    new_token_data = refresh_res.json()
    assert "access_token" in new_token_data
    assert new_token_data["refresh_token"] != refresh_token  # Rotated!

    # Replaying old refresh token must be rejected
    replayed_res = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert replayed_res.status_code == 401


@pytest.mark.asyncio
async def test_unauthorized_and_expired_access(client: AsyncClient):
    # 1. Missing token
    res1 = await client.get("/api/v1/auth/me")
    assert res1.status_code == 401

    # 2. Expired token
    from uuid import uuid4

    expired_token, _ = create_access_token(
        uuid4(), UserRole.CUSTOMER, expires_delta=timedelta(minutes=-10)
    )
    res2 = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert res2.status_code == 401
    assert "expired" in res2.json()["errors"][0]["message"].lower()


@pytest.mark.asyncio
async def test_role_escalation_rejection(client: AsyncClient, session):
    # Create customer account
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "phone": "9876543240",
            "full_name": "Normal Customer",
            "password": "Password123!",
            "consent_terms": True,
            "consent_privacy": True,
        },
    )
    customer_token = reg_res.json()["access_token"]

    # Customer attempts to access Admin probe -> 403 Forbidden!
    admin_probe_res = await client.get(
        "/api/v1/auth/admin/audit-probe",
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert admin_probe_res.status_code == 403
    assert "Access denied" in admin_probe_res.json()["errors"][0]["message"]

    # Create Admin in DB directly
    admin_user = User(
        phone="+919999999999",
        email="admin@glamnow.in",
        full_name="Super Admin",
        role=UserRole.ADMIN,
        password_hash=hash_password("AdminPass123!"),
        is_active=True,
    )
    session.add(admin_user)
    await session.commit()

    admin_token, _ = create_access_token(admin_user.id, UserRole.ADMIN)
    admin_probe_res_ok = await client.get(
        "/api/v1/auth/admin/audit-probe",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_probe_res_ok.status_code == 200
    assert "Welcome Administrator" in admin_probe_res_ok.json()["message"]


@pytest.mark.asyncio
async def test_address_management_and_cross_customer_isolation(client: AsyncClient):
    # Customer 1
    c1_res = await client.post(
        "/api/v1/auth/register",
        json={
            "phone": "9876543251",
            "full_name": "Customer 1",
            "password": "Password123!",
            "consent_terms": True,
            "consent_privacy": True,
        },
    )
    c1_token = c1_res.json()["access_token"]

    # Customer 2
    c2_res = await client.post(
        "/api/v1/auth/register",
        json={
            "phone": "9876543252",
            "full_name": "Customer 2",
            "password": "Password123!",
            "consent_terms": True,
            "consent_privacy": True,
        },
    )
    c2_token = c2_res.json()["access_token"]

    # Customer 1 creates an address
    addr_res = await client.post(
        "/api/v1/auth/addresses",
        headers={"Authorization": f"Bearer {c1_token}"},
        json={
            "label": "home",
            "recipient_name": "Customer 1",
            "address_line1": "Flat 402, Lotus Apartments",
            "city": "Bengaluru",
            "state": "Karnataka",
            "pincode": "560038",
            "is_default": True,
        },
    )
    assert addr_res.status_code == 201
    address_id = addr_res.json()["id"]

    # Customer 1 lists addresses -> sees 1 address
    list_res1 = await client.get(
        "/api/v1/auth/addresses",
        headers={"Authorization": f"Bearer {c1_token}"},
    )
    assert len(list_res1.json()) == 1

    # Customer 2 lists addresses -> sees 0 addresses (isolation!)
    list_res2 = await client.get(
        "/api/v1/auth/addresses",
        headers={"Authorization": f"Bearer {c2_token}"},
    )
    assert len(list_res2.json()) == 0

    # Customer 2 tries to delete Customer 1's address -> 404 (prevent leaking existence)
    delete_res = await client.delete(
        f"/api/v1/auth/addresses/{address_id}",
        headers={"Authorization": f"Bearer {c2_token}"},
    )
    assert delete_res.status_code == 404

    # Customer 1 deletes their own address -> 204
    delete_res_ok = await client.delete(
        f"/api/v1/auth/addresses/{address_id}",
        headers={"Authorization": f"Bearer {c1_token}"},
    )
    assert delete_res_ok.status_code == 204
