"""
Database seed script for GlamNow initial catalog data.
Populates:
- Beauty, Hair, Makeup, Massage, Nails, Saree Draping, Pico-Fall, Women's Tailoring, Men's Tailoring
- Multi-tier configurations (Basic, Standard, Premium)
- Initial effective-dated pricing rules
- Service add-ons and discount coupons
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session_factory
from app.modules.catalog.enums import DiscountType, ServiceTierType, WorkflowType
from app.modules.catalog.models import (
    DiscountRule,
    PricingRule,
    Service,
    ServiceAddOn,
    ServiceCategory,
    ServiceTier,
)

SEED_CATEGORIES = [
    {"slug": "beauty", "name": "Beauty & Skincare", "description": "Facials, cleanups, waxing & de-tan", "icon": "🌸", "display_order": 1},
    {"slug": "hair", "name": "Hair & Styling", "description": "Haircuts, styling, spa & keratin", "icon": "💇‍♀️", "display_order": 2},
    {"slug": "makeup", "name": "Makeup & Makeovers", "description": "Party, bridal, engagement & festival glam", "icon": "💄", "display_order": 3},
    {"slug": "massage", "name": "Therapeutic Massage", "description": "Deep tissue, Swedish & relaxing head-shoulder massage", "icon": "🌿", "display_order": 4},
    {"slug": "nails", "name": "Nails & Hand Care", "description": "Manicure, pedicure, gel extensions & nail art", "icon": "💅", "display_order": 5},
    {"slug": "saree-draping", "name": "Saree Draping", "description": "Traditional & modern pleat styling with steam rolling", "icon": "🥻", "display_order": 6},
    {"slug": "pico-fall", "name": "Pico-Fall & Hemming", "description": "Doorstep saree pico, fall stitching & minor repairs", "icon": "🧵", "display_order": 7},
    {"slug": "womens-tailoring", "name": "Women's Tailoring", "description": "Bespoke blouse, kurti, lehenga & suit stitching", "icon": "✂️", "display_order": 8},
    {"slug": "mens-tailoring", "name": "Men's Tailoring", "description": "Custom shirts, trousers, suits & alterations", "icon": "👔", "display_order": 9},
]


async def seed_catalog_data(session: AsyncSession) -> None:
    now = datetime.now(timezone.utc)

    # 1. Categories
    category_map: dict[str, ServiceCategory] = {}
    for cat_data in SEED_CATEGORIES:
        cat = ServiceCategory(
            id=uuid.uuid4(),
            slug=cat_data["slug"],
            name=cat_data["name"],
            description=cat_data["description"],
            icon=cat_data["icon"],
            display_order=cat_data["display_order"],
            is_active=True,
        )
        session.add(cat)
        category_map[cat_data["slug"]] = cat

    await session.flush()

    # 2. Services, Tiers & Pricing Rules
    services_to_create = [
        # 1. Beauty: Hydra Facial
        {
            "category_slug": "beauty",
            "slug": "hydra-radiance-facial",
            "name": "Hydra Radiance Facial & De-tan",
            "description": "Deep pore cleansing, fruit enzymatic peeling, micro-steam & suction extraction.",
            "icon": "🌸",
            "workflow_type": WorkflowType.AT_HOME_VISIT,
            "display_order": 1,
            "tiers": [
                {
                    "tier": ServiceTierType.BASIC,
                    "name": "Essential Glow",
                    "description": "Standard fruit cleansing, steam & soothing face pack.",
                    "brands": "VLCC Natural Cosmeceuticals",
                    "duration": 40,
                    "price_paise": 49900,
                    "inclusions": ["Cleansing milk", "Walnut scrub", "Fruit pack", "Single-use sterile sheet"],
                    "exclusions": ["Ozone steam", "Neck acupressure"],
                },
                {
                    "tier": ServiceTierType.STANDARD,
                    "name": "Signature O3+ Radiance",
                    "description": "Professional brightening peel with 10-min neck & shoulder relaxer.",
                    "brands": "O3+ Professional Derma Series",
                    "duration": 60,
                    "price_paise": 99900,
                    "is_popular": True,
                    "inclusions": ["O3+ brightening peel", "Ozone micro-steam", "Shoulder acupressure", "Rubber alginate mask"],
                    "exclusions": ["Ultrasonic infusion"],
                },
                {
                    "tier": ServiceTierType.PREMIUM,
                    "name": "Royal Dermalogica Hydra-Infusion",
                    "description": "Ultrasound serum infusion, luxury botanical oils, and cooling jade roller.",
                    "brands": "Dermalogica (USA Import)",
                    "duration": 75,
                    "price_paise": 189900,
                    "inclusions": ["Multi-acid exfoliation", "Ultrasound infusion", "Collagen eye mask", "Hand reflexology"],
                    "exclusions": [],
                },
            ],
            "add_ons": [
                {"name": "Hydra-Eye Gel Mask", "price_paise": 19900, "duration": 10},
                {"name": "Charcoal Blackhead Nose Strip", "price_paise": 14900, "duration": 5},
            ],
        },
        # 2. Hair: Intense Moisture Hair Spa
        {
            "category_slug": "hair",
            "slug": "intense-moisture-hair-spa",
            "name": "Intense Moisture Hair Spa & Head Massage",
            "description": "Deep conditioning steam bath, scalp detox, and blowdry finish.",
            "icon": "💆‍♀️",
            "workflow_type": WorkflowType.AT_HOME_VISIT,
            "display_order": 2,
            "tiers": [
                {
                    "tier": ServiceTierType.BASIC,
                    "name": "Nourish Care",
                    "description": "Hydrating mask with basic scalp steam.",
                    "brands": "Matrix Biolage Hydrasource",
                    "duration": 40,
                    "price_paise": 59900,
                    "inclusions": ["Biolage conditioning masque", "15-min scalp massage", "Warm steam wrap"],
                    "exclusions": ["Cuticle ampoule"],
                },
                {
                    "tier": ServiceTierType.STANDARD,
                    "name": "L'Oréal Mythic Oil Spa",
                    "description": "Enriched argan oil concentrate with ozone steam and precision blowdry.",
                    "brands": "L'Oréal Professionnel Serie Expert",
                    "duration": 60,
                    "price_paise": 109900,
                    "is_popular": True,
                    "inclusions": ["Mythic Oil lipid ampoule", "20-min pressure-point massage", "Blowdry finish"],
                    "exclusions": ["Caviar scrub"],
                },
                {
                    "tier": ServiceTierType.PREMIUM,
                    "name": "Kérastase Chronologiste Ritual",
                    "description": "Biomimetic caviar pearl treatment with deep scalp scrub.",
                    "brands": "Kérastase Paris Luxury Collection",
                    "duration": 80,
                    "price_paise": 249900,
                    "inclusions": ["Caviar pearl infusion", "Deep scalp scrub", "Anti-aging thermal wrap", "Bespoke finish"],
                    "exclusions": [],
                },
            ],
            "add_ons": [
                {"name": "Split-End Sealer Serum", "price_paise": 24900, "duration": 10},
            ],
        },
        # 3. Saree Draping: Traditional & Modern Draping
        {
            "category_slug": "saree-draping",
            "slug": "saree-draping-styling",
            "name": "Professional Saree Draping & Pleat Setting",
            "description": "Master draping in Nivi, Bengali, Nauvari, Coorgi, or modern lehenga style with pin-up security.",
            "icon": "🥻",
            "workflow_type": WorkflowType.AT_HOME_VISIT,
            "display_order": 3,
            "tiers": [
                {
                    "tier": ServiceTierType.BASIC,
                    "name": "Classic Pleat Draping",
                    "description": "Standard Nivi style drape with ironed pleats.",
                    "brands": "Cotton & Silk Care Standards",
                    "duration": 25,
                    "price_paise": 29900,
                    "inclusions": ["Clean pleating", "Safety pinning", "Pallu drop adjustment"],
                    "exclusions": ["Pre-pleating box fold"],
                },
                {
                    "tier": ServiceTierType.STANDARD,
                    "name": "Designer Event Draping",
                    "description": "Heavy Kanjivaram, Banarasi, or Georgette draping with waist tuck.",
                    "brands": "Bridal Draping Essentials",
                    "duration": 40,
                    "price_paise": 49900,
                    "is_popular": True,
                    "inclusions": ["Heavy silk handling", "Double pallu styling", "Waist belt security", "Steam touch-up"],
                    "exclusions": [],
                },
            ],
            "add_ons": [],
        },
        # 4. Pico-Fall & Saree Care
        {
            "category_slug": "pico-fall",
            "slug": "saree-pico-fall-rolling",
            "name": "Saree Pico-Fall Stitching & Rolling Steam",
            "description": "Interlocking pico border, color-matched cotton fall, and doorstep pickup & return.",
            "icon": "🧵",
            "workflow_type": WorkflowType.SAREE_CARE,
            "display_order": 4,
            "tiers": [
                {
                    "tier": ServiceTierType.STANDARD,
                    "name": "Studio Interlock Pico-Fall",
                    "description": "Interlocked nylon pico border with matching pure cotton fall.",
                    "brands": "Madura Coats Thread & Pre-shrunk Cotton Fall",
                    "duration": 24,  # Hours turnaround
                    "price_paise": 29900,
                    "is_popular": True,
                    "inclusions": ["Pre-shrunk cotton fall", "Interlocking pico edge", "Wrinkle-free steam press", "Doorstep pickup & drop"],
                    "exclusions": [],
                },
            ],
            "add_ons": [
                {"name": "Saree Tassels / Latkan Stitching", "price_paise": 19900, "duration": 0},
            ],
        },
        # 5. Women's Tailoring: Designer Blouse
        {
            "category_slug": "womens-tailoring",
            "slug": "designer-blouse-stitching",
            "name": "Designer Blouse Custom Tailoring",
            "description": "Master tailor home measurement visit, custom necklines, cups & trial guarantee.",
            "icon": "✂️",
            "workflow_type": WorkflowType.TAILORING_CUSTOM,
            "display_order": 5,
            "tiers": [
                {
                    "tier": ServiceTierType.BASIC,
                    "name": "Classic 4-Dart Blouse",
                    "description": "Standard round or square neck with cotton lining.",
                    "brands": "Premium Cotton Linings & YKK Zippers",
                    "duration": 48,
                    "price_paise": 49900,
                    "inclusions": ["Sample garment pickup", "Cotton lining included", "Front hook-eye placket"],
                    "exclusions": ["Master tailor home visit", "Padded cups"],
                },
                {
                    "tier": ServiceTierType.STANDARD,
                    "name": "Princess Cut Designer Blouse",
                    "description": "Princess cut, deep back, padded cups, and master tailor home visit.",
                    "brands": "High-Density Foam Cups & Reinforced Seams",
                    "duration": 48,
                    "price_paise": 79900,
                    "is_popular": True,
                    "inclusions": ["Master tailor home visit", "Padded cups", "Piping finish", "Doorstep trial guarantee"],
                    "exclusions": ["Zardozi hand embroidery"],
                },
                {
                    "tier": ServiceTierType.PREMIUM,
                    "name": "Bridal Maggam & Zardozi Blouse",
                    "description": "Intricate hand embroidery, silk lining, and customized fit perfection.",
                    "brands": "Raw Silk & Gold Metallic Zari",
                    "duration": 96,
                    "price_paise": 249900,
                    "inclusions": ["Master artisan consultation", "Maggam handwork", "Silk lining", "2 fitting sessions"],
                    "exclusions": [],
                },
            ],
            "add_ons": [
                {"name": "Handmade Latkan Dori", "price_paise": 14900, "duration": 0},
                {"name": "Extra Fabric Collar Detailing", "price_paise": 19900, "duration": 0},
            ],
        },
    ]

    for s_data in services_to_create:
        cat = category_map[s_data["category_slug"]]
        service = Service(
            id=uuid.uuid4(),
            category_id=cat.id,
            slug=s_data["slug"],
            name=s_data["name"],
            description=s_data["description"],
            icon=s_data["icon"],
            workflow_type=s_data["workflow_type"],
            display_order=s_data["display_order"],
            is_active=True,
        )
        session.add(service)
        await session.flush()

        # Add Tiers & Pricing Rules
        for t_data in s_data["tiers"]:
            tier = ServiceTier(
                id=uuid.uuid4(),
                service_id=service.id,
                tier=t_data["tier"],
                name=t_data["name"],
                description=t_data["description"],
                brands=t_data["brands"],
                duration_minutes=t_data["duration"],
                inclusions=t_data["inclusions"],
                exclusions=t_data["exclusions"],
                is_popular=t_data.get("is_popular", False),
                is_active=True,
            )
            session.add(tier)
            await session.flush()

            # Create Pricing Rule
            rule = PricingRule(
                id=uuid.uuid4(),
                tier_id=tier.id,
                base_price_paise=t_data["price_paise"],
                effective_from=now,
                effective_to=None,
                is_active=True,
            )
            session.add(rule)

        # Add Add-ons
        for a_data in s_data["add_ons"]:
            addon = ServiceAddOn(
                id=uuid.uuid4(),
                service_id=service.id,
                name=a_data["name"],
                price_paise=a_data["price_paise"],
                duration_minutes=a_data["duration"],
                is_active=True,
            )
            session.add(addon)

    # 3. Promotional Discount Rules
    discounts = [
        DiscountRule(
            id=uuid.uuid4(),
            code="GLAMFIRST",
            discount_type=DiscountType.PERCENTAGE,
            value=20,  # 20% off
            max_discount_paise=20000,  # Max ₹200 off
            min_order_paise=49900,     # Min order ₹499
            valid_from=now,
            valid_to=None,
            is_active=True,
        ),
        DiscountRule(
            id=uuid.uuid4(),
            code="FESTIVE100",
            discount_type=DiscountType.FLAT_PAISE,
            value=10000,  # Flat ₹100 off
            max_discount_paise=10000,
            min_order_paise=39900,
            valid_from=now,
            valid_to=None,
            is_active=True,
        ),
    ]
    for d in discounts:
        session.add(d)

    await session.commit()
    print("Catalog seed completed successfully.")


if __name__ == "__main__":
    async def main() -> None:
        factory = get_session_factory()
        async with factory() as session:
            await seed_catalog_data(session)

    asyncio.run(main())
