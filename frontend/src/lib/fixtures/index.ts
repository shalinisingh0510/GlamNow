/**
 * Realistic development fixtures for the GlamNow Indian marketplace.
 *
 * NOTE: These fixtures are strictly isolated from production API client code.
 * In Phase 3+, client hooks can swap from fixtures to live `/api/v1/*` endpoints seamlessly.
 */

export interface ServiceTierFixture {
  tier: "basic" | "standard" | "premium";
  title: string;
  description: string;
  pricePaise: number;
  durationMinutes: number;
  brands: string;
  inclusions: string[];
  isPopular?: boolean;
}

export interface ServiceItemFixture {
  id: string;
  categoryId: string;
  categoryName: string;
  name: string;
  description: string;
  icon: string;
  startingPricePaise: number;
  durationMinutes: number;
  tiers: ServiceTierFixture[];
}

export interface ProfessionalFixture {
  id: string;
  name: string;
  title: string;
  experienceYears: number;
  ratingScore: number;
  reviewCount: number;
  etaMinutes: number;
  specialties: string[];
  startingPricePaise: number;
  avatarText: string;
  isVerified: boolean;
  tier: "basic" | "standard" | "premium";
}

export interface TailoringServiceFixture {
  id: string;
  category: "saree_care" | "custom_stitching" | "alterations";
  title: string;
  description: string;
  pricePaise: number;
  estimatedHours: number;
  inclusions: string[];
  measurementModes: ("home_visit" | "sample_pickup" | "saved_profile")[];
}

// ─── Service Categories ──────────────────────────────────────────────────────
export const FIXTURE_CATEGORIES = [
  { id: "beauty", name: "Salon for Women", count: "32 Services", icon: "✨" },
  { id: "grooming", name: "Men's Grooming", count: "18 Services", icon: "✂️" },
  { id: "tailoring", name: "Tailoring & Alterations", count: "14 Services", icon: "🧵", badge: "Express Delivery" },
  { id: "massage", name: "Spa & Body Massage", count: "12 Services", icon: "🌿" },
  { id: "saree", name: "Saree Draping & Ironing", count: "6 Services", icon: "🥻" },
];

// ─── Multi-Tier Service Definitions ──────────────────────────────────────────
export const FIXTURE_SERVICES: ServiceItemFixture[] = [
  {
    id: "srv_facial_glow",
    categoryId: "beauty",
    categoryName: "Facials & Skincare",
    name: "Glow Radiance Facial & De-tan",
    description: "Deep pore cleansing, fruit enzymatic peeling, micro-steam, blackhead removal, and massage.",
    icon: "🌸",
    startingPricePaise: 49900,
    durationMinutes: 45,
    tiers: [
      {
        tier: "basic",
        title: "Essential Glow",
        description: "Standard fruit cleansing and scrub with disposable sponge kit.",
        pricePaise: 49900,
        durationMinutes: 35,
        brands: "VLCC Natural Cosmeceuticals",
        inclusions: [
          "Cleansing milk & walnut scrub",
          "Soothing cucumber mask",
          "Sanitized single-use sheet kit",
        ],
      },
      {
        tier: "standard",
        title: "O3+ Radiance Signature",
        description: "Professional whitening & brightening peel with 10-minute neck and shoulder acupressure.",
        pricePaise: 99900,
        durationMinutes: 55,
        brands: "O3+ Professional Derma Series",
        inclusions: [
          "O3+ Glycolic brightening peel",
          "Ozone micro-steam & suction extraction",
          "10-min neck, shoulder & arm massage",
          "Rubber alginate peel-off mask",
        ],
        isPopular: true,
      },
      {
        tier: "premium",
        title: "Dermalogica Hydra-Infusion",
        description: "Medical-grade ultrasonic hydra infusion with organic calming botanicals and hand reflexology.",
        pricePaise: 189900,
        durationMinutes: 75,
        brands: "Dermalogica (USA Import)",
        inclusions: [
          "Dermalogica multi-acid exfoliation",
          "Ultrasonic ultrasound serum infusion",
          "Aromatherapy hot towel ritual",
          "Collagen eye mask & full scalp relaxer",
        ],
      },
    ],
  },
  {
    id: "srv_hair_spa",
    categoryId: "beauty",
    categoryName: "Hair & Styling",
    name: "Intense Moisture Hair Spa & Head Massage",
    description: "Deep conditioning steam bath, scalp detox, and blowdry finish for dry, chemically treated hair.",
    icon: "💆‍♀️",
    startingPricePaise: 59900,
    durationMinutes: 50,
    tiers: [
      {
        tier: "basic",
        title: "Nourish Care",
        description: "Hydrating hair mask with basic scalp steam.",
        pricePaise: 59900,
        durationMinutes: 40,
        brands: "Matrix Biolage Hydrasource",
        inclusions: [
          "Biolage deep conditioning masque",
          "15-minute soothing scalp massage",
          "Warm steam wrap & rinse",
        ],
      },
      {
        tier: "standard",
        title: "L'Oréal Mythic Oil Spa",
        description: "Enriched argan oil concentrate with ozone steam and precision blowdry.",
        pricePaise: 109900,
        durationMinutes: 60,
        brands: "L'Oréal Professionnel Serie Expert",
        inclusions: [
          "Mythic Oil lipid replenishment ampoule",
          "20-minute rhythmic pressure-point massage",
          "Ozone micro-mist cuticle sealing",
          "Silky blowdry styling finish",
        ],
        isPopular: true,
      },
      {
        tier: "premium",
        title: "Kérastase Chronologiste Ritual",
        description: "The pinnacle of hair regeneration with abyssinian pearl caviar and caviar serum.",
        pricePaise: 249900,
        durationMinutes: 80,
        brands: "Kérastase Paris Luxury Collection",
        inclusions: [
          "Chronologiste essential biomimetic caviar pearl",
          "Deep scalp scrub exfoliation",
          "Anti-aging thermal treatment",
          "Master stylist consultation & customized finish",
        ],
      },
    ],
  },
  {
    id: "srv_mens_sculpt",
    categoryId: "grooming",
    categoryName: "Men's Grooming",
    name: "Master Haircut & Beard Sculpting",
    description: "Tailored precision fade, hot towel straight-razor shave, and activated charcoal face cleanup.",
    icon: "✂️",
    startingPricePaise: 34900,
    durationMinutes: 40,
    tiers: [
      {
        tier: "basic",
        title: "Classic Trim & Shave",
        description: "Standard scissor cut and beard lining.",
        pricePaise: 34900,
        durationMinutes: 30,
        brands: "Gillette Professional & Wahl Pro",
        inclusions: [
          "Wahl clipper fade & scissor work",
          "Beard trimming & aftershave splash",
          "Disinfected single-use blade & towel",
        ],
      },
      {
        tier: "standard",
        title: "Gentleman's Signature",
        description: "Skin fade, eucalyptus hot towel beard sculpting, and charcoal blackhead mask.",
        pricePaise: 69900,
        durationMinutes: 50,
        brands: "The Man Company & Beardo Pro Series",
        inclusions: [
          "Tailored precision fade & taper",
          "Hot steam towel & beard butter conditioning",
          "Activated charcoal de-tan peel",
          "5-minute neck & temple vibration relaxer",
        ],
        isPopular: true,
      },
      {
        tier: "premium",
        title: "Executive Royal Grooming",
        description: "Bespoke hair styling, gold-leaf straight razor beard contouring, and diamond face cleanup.",
        pricePaise: 129900,
        durationMinutes: 70,
        brands: "Truefitt & Hill London",
        inclusions: [
          "Master barber session with hair analysis",
          "Pre-shave oil & luxury badger-brush lather",
          "Organic facial cleansing & cold towel pore closing",
          "Shoulder, neck, and back acupressure session",
        ],
      },
    ],
  },
];

// ─── Verified Professionals ──────────────────────────────────────────────────
export const FIXTURE_PROFESSIONALS: ProfessionalFixture[] = [
  {
    id: "pro_1",
    name: "Priya Sharma",
    title: "Master Aesthetician & Hair Stylist",
    experienceYears: 7,
    ratingScore: 4.94,
    reviewCount: 382,
    etaMinutes: 18,
    specialties: ["Hydra Facial", "Bridal Hair", "Keratin Spa"],
    startingPricePaise: 59900,
    avatarText: "PS",
    isVerified: true,
    tier: "premium",
  },
  {
    id: "pro_2",
    name: "Ramesh Kumar",
    title: "Men's Master Barber & Stylist",
    experienceYears: 9,
    ratingScore: 4.88,
    reviewCount: 512,
    etaMinutes: 24,
    specialties: ["Fade Cuts", "Beard Sculpting", "Charcoal Detan"],
    startingPricePaise: 34900,
    avatarText: "RK",
    isVerified: true,
    tier: "standard",
  },
  {
    id: "pro_3",
    name: "Ananya Deshmukh",
    title: "Master Tailor & Draping Artisan",
    experienceYears: 12,
    ratingScore: 4.97,
    reviewCount: 240,
    etaMinutes: 30,
    specialties: ["Saree Draping", "Designer Blouses", "Pico-Fall"],
    startingPricePaise: 29900,
    avatarText: "AD",
    isVerified: true,
    tier: "premium",
  },
  {
    id: "pro_4",
    name: "Deepak Verma",
    title: "Therapeutic Massage Specialist",
    experienceYears: 6,
    ratingScore: 4.91,
    reviewCount: 195,
    etaMinutes: 22,
    specialties: ["Deep Tissue", "Swedish Relaxation", "Potli Warm Therapy"],
    startingPricePaise: 89900,
    avatarText: "DV",
    isVerified: true,
    tier: "standard",
  },
];

// ─── Tailoring & Garment Care Fixtures ────────────────────────────────────────
export const FIXTURE_TAILORING_SERVICES: TailoringServiceFixture[] = [
  {
    id: "tailor_pico_fall",
    category: "saree_care",
    title: "Pico-Fall & Saree Rolling Steam",
    description: "Precision interlocking pico border, color-matched cotton fall attachment, and wrinkle-free steam press.",
    pricePaise: 29900,
    estimatedHours: 24,
    inclusions: [
      "Doorstep fabric pickup and return in sealed tamper-proof bag",
      "Pure cotton pre-shrunk matching fall",
      "Interlocked nylon pico stitching",
      "Gentle steam press before delivery",
    ],
    measurementModes: ["sample_pickup", "saved_profile"],
  },
  {
    id: "tailor_designer_blouse",
    category: "custom_stitching",
    title: "Designer Blouse Custom Stitching",
    description: "Custom neckline, padded cups option, princess cut darts, latkan tie-backs, and perfect armhole fit.",
    pricePaise: 69900,
    estimatedHours: 48,
    inclusions: [
      "Master tailor home measurement visit OR sample blouse pickup",
      "High-grade cotton inner lining included",
      "Reinforced hook-and-eye bar",
      "Free doorstep trial & adjustment guarantee",
    ],
    measurementModes: ["home_visit", "sample_pickup", "saved_profile"],
  },
  {
    id: "tailor_alterations",
    category: "alterations",
    title: "Trouser, Kurti & Suit Alterations",
    description: "Waist tightening/easing, length shortening, taper fit, sleeve reduction, and zipper replacement.",
    pricePaise: 19900,
    estimatedHours: 24,
    inclusions: [
      "Doorstep pin-up measurement by tailor",
      "Original hem finish preserved",
      "48-hour swift turnaround",
    ],
    measurementModes: ["home_visit", "sample_pickup"],
  },
];

// ─── Serviceable Zones Fixture ───────────────────────────────────────────────
export const FIXTURE_SERVICEABLE_ZONES = [
  { pincode: "560038", area: "Indiranagar, Bengaluru", etaMin: 15, etaMax: 25, activePros: 14 },
  { pincode: "560034", area: "Koramangala, Bengaluru", etaMin: 18, etaMax: 30, activePros: 18 },
  { pincode: "560001", area: "MG Road & Central, Bengaluru", etaMin: 20, etaMax: 30, activePros: 11 },
  { pincode: "560102", area: "HSR Layout, Bengaluru", etaMin: 15, etaMax: 25, activePros: 16 },
];
