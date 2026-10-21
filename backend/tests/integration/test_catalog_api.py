"""
Integration tests for Catalog browsing, search, filtering, quotes,
and dynamic admin publishing.
"""

from datetime import datetime, timezone
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.enums import ServiceTierType, WorkflowType
from app.modules.catalog.models import PricingRule, Service, ServiceCategory, ServiceTier
from app.modules.identity.enums import UserRole
from app.modules.identity.models import User
from app.modules.identity.security import create_access_token, hash_password


@pytest.fixture
async def sample_catalog_in_db(session: AsyncSession):
    now = datetime.now(timezone.utc)

    # Category 1: Beauty
    cat_beauty = ServiceCategory(
        slug="beauty",
        name="Beauty & Skincare",
        description="Facials and cleanups",
        icon="🌸",
        display_order=1,
        is_active=True,
    )
    # Category 2: Tailoring
    cat_tailoring = ServiceCategory(
        slug="womens-tailoring",
        name="Women's Tailoring",
        description="Custom blouses",
        icon="✂️",
        display_order=2,
        is_active=True,
    )
    session.add_all([cat_beauty, cat_tailoring])
    await session.flush()

    # Service in Beauty
    srv_facial = Service(
        category_id=cat_beauty.id,
        slug="hydra-facial",
        name="Hydra Facial",
        description="Deep pore cleansing",
        icon="🌸",
        workflow_type=WorkflowType.AT_HOME_VISIT,
        display_order=1,
        is_active=True,
    )
    # Service in Tailoring
    srv_blouse = Service(
        category_id=cat_tailoring.id,
        slug="designer-blouse",
        name="Designer Blouse Stitching",
        description="Custom tailored blouse",
        icon="✂️",
        workflow_type=WorkflowType.TAILORING_CUSTOM,
        display_order=1,
        is_active=True,
    )
    session.add_all([srv_facial, srv_blouse])
    await session.flush()

    # Tier for Facial
    tier_facial_std = ServiceTier(
        service_id=srv_facial.id,
        tier=ServiceTierType.STANDARD,
        name="Signature Care",
        description="Facial with massage",
        brands="O3+",
        duration_minutes=50,
        inclusions=["Cleanser", "O3+ Mask"],
        exclusions=[],
        is_popular=True,
        is_active=True,
    )
    session.add(tier_facial_std)
    await session.flush()

    rule_facial = PricingRule(
        tier_id=tier_facial_std.id,
        base_price_paise=79900,  # ₹799
        effective_from=now,
        is_active=True,
    )
    session.add(rule_facial)
    await session.commit()

    return {
        "cat_beauty": cat_beauty,
        "cat_tailoring": cat_tailoring,
        "srv_facial": srv_facial,
        "srv_blouse": srv_blouse,
        "tier_facial": tier_facial_std,
    }


@pytest.mark.asyncio
async def test_list_categories(client: AsyncClient, sample_catalog_in_db):
    res = await client.get("/api/v1/catalog/categories")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 2
    slugs = [c["slug"] for c in data]
    assert "beauty" in slugs
    assert "womens-tailoring" in slugs


@pytest.mark.asyncio
async def test_services_filtering_and_search(client: AsyncClient, sample_catalog_in_db):
    cat_tailoring = sample_catalog_in_db["cat_tailoring"]

    # 1. List all
    res_all = await client.get("/api/v1/catalog/services")
    assert res_all.status_code == 200
    assert len(res_all.json()) >= 2

    # 2. Filter by category
    res_cat = await client.get(f"/api/v1/catalog/services?category_id={cat_tailoring.id}")
    assert res_cat.status_code == 200
    data_cat = res_cat.json()
    assert len(data_cat) == 1
    assert data_cat[0]["slug"] == "designer-blouse"

    # 3. Search by keyword
    res_search = await client.get("/api/v1/catalog/services?search=hydra")
    assert res_search.status_code == 200
    data_search = res_search.json()
    assert len(data_search) == 1
    assert data_search[0]["name"] == "Hydra Facial"


@pytest.mark.asyncio
async def test_service_detail_endpoint(client: AsyncClient, sample_catalog_in_db):
    res = await client.get("/api/v1/catalog/services/hydra-facial")
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Hydra Facial"
    assert len(data["tiers"]) == 1
    assert data["tiers"][0]["tier"] == "standard"
    assert data["tiers"][0]["current_price_paise"] == 79900


@pytest.mark.asyncio
async def test_public_quote_calculation(client: AsyncClient, sample_catalog_in_db):
    srv = sample_catalog_in_db["srv_facial"]

    payload = {
        "service_id": str(srv.id),
        "tier": "standard",
        "add_on_ids": [],
    }
    res = await client.post("/api/v1/catalog/quote", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["service_name"] == "Hydra Facial"
    assert data["base_price_paise"] == 79900
    # CGST 9% (7191) + SGST 9% (7191) = 14382
    assert data["tax_cgst_paise"] == 7191
    assert data["tax_sgst_paise"] == 7191
    assert data["total_paise"] == 79900 + 14382
    assert "immutable_price_snapshot" in data


@pytest.mark.asyncio
async def test_admin_dynamic_publishing_without_code_changes(
    client: AsyncClient, session: AsyncSession
):
    # 1. Normal customer attempts admin route -> 403 Forbidden
    customer = User(
        phone="+919876599999",
        full_name="Regular Customer",
        role=UserRole.CUSTOMER,
        password_hash=hash_password("CustomerPass123!"),
        is_active=True,
    )
    session.add(customer)
    await session.commit()
    customer_token, _ = create_access_token(customer.id, UserRole.CUSTOMER)

    unauthorized_res = await client.post(
        "/api/v1/catalog/admin/categories",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={"slug": "new-cat", "name": "New Category", "icon": "✨"},
    )
    assert unauthorized_res.status_code == 403

    # 2. Admin user created
    admin = User(
        phone="+919876500000",
        full_name="Catalog Admin",
        role=UserRole.ADMIN,
        password_hash=hash_password("AdminPass123!"),
        is_active=True,
    )
    session.add(admin)
    await session.commit()
    admin_token, _ = create_access_token(admin.id, UserRole.ADMIN)

    # 3. Admin dynamically publishes new Category
    cat_res = await client.post(
        "/api/v1/catalog/admin/categories",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "slug": "ayurvedic-massage",
            "name": "Ayurvedic Massage",
            "description": "Authentic Kerala herbal therapies",
            "icon": "🌿",
        },
    )
    assert cat_res.status_code == 201
    cat_id = cat_res.json()["id"]

    # 4. Admin dynamically publishes new Service
    srv_res = await client.post(
        "/api/v1/catalog/admin/services",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "category_id": cat_id,
            "slug": "potli-warm-massage",
            "name": "Herbal Potli Warm Massage",
            "description": "Therapeutic heated herbal poultice massage",
            "icon": "🌿",
            "workflow_type": "at_home_visit",
        },
    )
    assert srv_res.status_code == 201
    srv_id = srv_res.json()["id"]

    # 5. Admin dynamically creates Premium Tier with initial pricing
    tier_res = await client.post(
        "/api/v1/catalog/admin/tiers",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "service_id": srv_id,
            "tier": "premium",
            "name": "Royal Ayurvedic Therapy",
            "description": "Full body potli with medicated sesame oil",
            "brands": "Kottakkal Arya Vaidya Sala",
            "duration_minutes": 90,
            "inclusions": ["Warm herbal potli", "Head massage", "Steam towel cleanse"],
            "base_price_paise": 199900,  # ₹1,999
        },
    )
    assert tier_res.status_code == 201
    assert tier_res.json()["tier"] == "premium"
    assert tier_res.json()["current_price_paise"] == 199900

    # 6. Public can now immediately query and calculate quote for this new service!
    public_res = await client.get(f"/api/v1/catalog/services/{srv_id}")
    assert public_res.status_code == 200
    assert public_res.json()["name"] == "Herbal Potli Warm Massage"
    assert len(public_res.json()["tiers"]) == 1

    quote_res = await client.post(
        "/api/v1/catalog/quote",
        json={"service_id": srv_id, "tier": "premium", "add_on_ids": []},
    )
    assert quote_res.status_code == 200
    assert quote_res.json()["base_price_paise"] == 199900
