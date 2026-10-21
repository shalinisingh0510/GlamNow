"""
Unit tests for the Pricing Engine, effective-dated rules, transparent quotes,
and price tampering rejection.
"""

from datetime import datetime, timedelta, timezone
import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, ValidationError
from app.modules.catalog.enums import DiscountType, ServiceTierType, WorkflowType
from app.modules.catalog.models import (
    DiscountRule,
    PricingRule,
    Service,
    ServiceAddOn,
    ServiceCategory,
    ServiceTier,
)
from app.modules.catalog.schemas import QuoteRequest
from app.modules.catalog.service import CatalogService


@pytest.fixture
async def seeded_catalog(session: AsyncSession):
    now = datetime.now(timezone.utc)

    # 1. Category
    cat = ServiceCategory(
        id=uuid.uuid4(),
        slug="beauty",
        name="Beauty & Skincare",
        description="Facials and cleanups",
        icon="🌸",
        display_order=1,
        is_active=True,
    )
    session.add(cat)
    await session.flush()

    # 2. Service
    service = Service(
        id=uuid.uuid4(),
        category_id=cat.id,
        slug="glow-facial",
        name="Glow Facial",
        description="Enzymatic cleansing and peel",
        icon="🌸",
        workflow_type=WorkflowType.AT_HOME_VISIT,
        display_order=1,
        is_active=True,
    )
    session.add(service)
    await session.flush()

    # 3. Tiers (Basic & Standard)
    tier_basic = ServiceTier(
        id=uuid.uuid4(),
        service_id=service.id,
        tier=ServiceTierType.BASIC,
        name="Essential Glow",
        description="Fruit facial",
        brands="VLCC",
        duration_minutes=30,
        inclusions=["Cleanser", "Scrub"],
        exclusions=["Steam"],
        is_popular=False,
        is_active=True,
    )
    tier_standard = ServiceTier(
        id=uuid.uuid4(),
        service_id=service.id,
        tier=ServiceTierType.STANDARD,
        name="Signature O3+",
        description="Brightening facial with steam",
        brands="O3+ Professional",
        duration_minutes=50,
        inclusions=["Cleanser", "O3+ Peel", "Steam"],
        exclusions=[],
        is_popular=True,
        is_active=True,
    )
    session.add_all([tier_basic, tier_standard])
    await session.flush()

    # 4. Effective-Dated Pricing Rules
    # Current active rule for Basic: ₹499 (49900 paise)
    rule_basic = PricingRule(
        id=uuid.uuid4(),
        tier_id=tier_basic.id,
        base_price_paise=49900,
        effective_from=now - timedelta(days=10),
        effective_to=None,
        is_active=True,
    )
    # Current active rule for Standard: ₹899 (89900 paise)
    rule_standard_current = PricingRule(
        id=uuid.uuid4(),
        tier_id=tier_standard.id,
        base_price_paise=89900,
        effective_from=now - timedelta(days=5),
        effective_to=now + timedelta(days=5),
        is_active=True,
    )
    # Future rule for Standard (effective in 5 days): ₹999 (99900 paise)
    rule_standard_future = PricingRule(
        id=uuid.uuid4(),
        tier_id=tier_standard.id,
        base_price_paise=99900,
        effective_from=now + timedelta(days=5),
        effective_to=None,
        is_active=True,
    )
    session.add_all([rule_basic, rule_standard_current, rule_standard_future])

    # 5. Add-ons
    addon1 = ServiceAddOn(
        id=uuid.uuid4(),
        service_id=service.id,
        name="Eye Gel Mask",
        price_paise=15000,  # ₹150
        duration_minutes=10,
        is_active=True,
    )
    session.add(addon1)

    # 6. Unrelated service add-on (for invalid combination test)
    unrelated_service = Service(
        id=uuid.uuid4(),
        category_id=cat.id,
        slug="unrelated-haircut",
        name="Haircut",
        description="Cut",
        icon="✂️",
        is_active=True,
    )
    session.add(unrelated_service)
    await session.flush()
    unrelated_addon = ServiceAddOn(
        id=uuid.uuid4(),
        service_id=unrelated_service.id,
        name="Hair Serum",
        price_paise=20000,
        is_active=True,
    )
    session.add(unrelated_addon)

    # 7. Discount rule: 10% off up to ₹100, min order ₹500
    discount = DiscountRule(
        id=uuid.uuid4(),
        code="GLAM10",
        discount_type=DiscountType.PERCENTAGE,
        value=10,
        max_discount_paise=10000,
        min_order_paise=50000,
        valid_from=now - timedelta(days=1),
        valid_to=now + timedelta(days=30),
        is_active=True,
    )
    session.add(discount)

    await session.commit()
    return {
        "service": service,
        "tier_basic": tier_basic,
        "tier_standard": tier_standard,
        "addon1": addon1,
        "unrelated_addon": unrelated_addon,
        "discount": discount,
    }


@pytest.mark.asyncio
async def test_quote_calculation_with_gst(session: AsyncSession, seeded_catalog):
    service = seeded_catalog["service"]
    addon = seeded_catalog["addon1"]
    catalog_service = CatalogService(session)

    # Request basic tier + add-on
    req = QuoteRequest(
        service_id=service.id,
        tier=ServiceTierType.BASIC,
        add_on_ids=[addon.id],
    )
    quote = await catalog_service.calculate_quote(req)

    # Base price: 49900
    # Addon: 15000
    # Subtotal: 64900 paise (₹649.00)
    assert quote.base_price_paise == 49900
    assert len(quote.add_ons) == 1
    assert quote.add_ons[0].price_paise == 15000
    assert quote.duration_minutes == 40  # 30m tier + 10m addon
    assert quote.subtotal_paise == 64900

    # GST 18%: 9% CGST (5841) + 9% SGST (5841) = 11682 paise
    assert quote.tax_cgst_paise == round(64900 * 0.09)
    assert quote.tax_sgst_paise == round(64900 * 0.09)
    assert quote.total_paise == 64900 + quote.tax_cgst_paise + quote.tax_sgst_paise

    # Immutable snapshot validation
    snapshot = quote.immutable_price_snapshot
    assert snapshot["service_name"] == "Glow Facial"
    assert snapshot["tier"] == "basic"
    assert snapshot["total_paise"] == quote.total_paise
    assert snapshot["currency"] == "INR"


@pytest.mark.asyncio
async def test_effective_dated_pricing_rules(session: AsyncSession, seeded_catalog):
    service = seeded_catalog["service"]
    catalog_service = CatalogService(session)
    now = datetime.now(timezone.utc)

    # 1. Query today -> should get current price ₹899 (89900)
    quote_today = await catalog_service.calculate_quote(
        QuoteRequest(service_id=service.id, tier=ServiceTierType.STANDARD),
        at_time=now,
    )
    assert quote_today.base_price_paise == 89900

    # 2. Query 7 days in future -> should pick future price ₹999 (99900)
    future_time = now + timedelta(days=7)
    quote_future = await catalog_service.calculate_quote(
        QuoteRequest(service_id=service.id, tier=ServiceTierType.STANDARD),
        at_time=future_time,
    )
    assert quote_future.base_price_paise == 99900


@pytest.mark.asyncio
async def test_discount_calculation_and_cap(session: AsyncSession, seeded_catalog):
    service = seeded_catalog["service"]
    catalog_service = CatalogService(session)

    # Standard tier base price = 89900 paise (₹899)
    # Discount GLAM10 = 10% of 89900 = 8990 paise (₹89.90), below max cap of 10000
    req = QuoteRequest(
        service_id=service.id,
        tier=ServiceTierType.STANDARD,
        discount_code="GLAM10",
    )
    quote = await catalog_service.calculate_quote(req)

    assert quote.discount_paise == 8990
    assert quote.subtotal_paise == 89900 - 8990
    # Tax computed on net taxable amount
    expected_cgst = round((89900 - 8990) * 0.09)
    assert quote.tax_cgst_paise == expected_cgst


@pytest.mark.asyncio
async def test_invalid_addon_combination_rejected(session: AsyncSession, seeded_catalog):
    service = seeded_catalog["service"]
    unrelated_addon = seeded_catalog["unrelated_addon"]
    catalog_service = CatalogService(session)

    # Attempting to add an add-on from a different service
    req = QuoteRequest(
        service_id=service.id,
        tier=ServiceTierType.BASIC,
        add_on_ids=[unrelated_addon.id],
    )
    with pytest.raises(ValidationError) as exc_info:
        await catalog_service.calculate_quote(req)
    assert "do not belong to this service" in str(exc_info.value)


@pytest.mark.asyncio
async def test_non_existent_tier_rejected(session: AsyncSession, seeded_catalog):
    service = seeded_catalog["service"]
    catalog_service = CatalogService(session)

    # Service only has basic and standard, requesting premium should fail
    req = QuoteRequest(service_id=service.id, tier=ServiceTierType.PREMIUM)
    with pytest.raises(NotFoundError):
        await catalog_service.calculate_quote(req)
