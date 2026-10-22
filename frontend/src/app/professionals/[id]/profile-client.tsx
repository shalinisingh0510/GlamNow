"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { Rating } from "@/components/ui/rating";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { PortfolioGallery } from "@/components/professionals/portfolio-gallery";
import { SlotSelector, SlotItem } from "@/components/professionals/slot-selector";

export interface TierOffering {
  tier: string;
  name: string;
  pricePaise: number;
  duration: string;
  brands: string;
  inclusions: string[];
  isPopular?: boolean;
}

export interface WorkingHourSchedule {
  day: string;
  hours: string;
  breakTime: string | null;
}

export interface PortfolioRecord {
  id: string;
  title: string;
  description: string;
  imageUrl: string;
  serviceName: string;
  isVerified: boolean;
}

export interface DetailedProfile {
  id: string;
  name: string;
  title: string;
  bio: string;
  experienceYears: number;
  ratingScore: number;
  reviewCount: number;
  baseZoneName: string;
  serviceRadiusKm: number;
  isVerified: boolean;
  specialties: string[];
  tierOfferings: TierOffering[];
  workingHours: WorkingHourSchedule[];
  portfolio: PortfolioRecord[];
}

export function ProfileClient({ id }: { id: string }) {
  // Mock detailed profiles
  const profile: DetailedProfile = useMemo(() => {
    const profilesDb: Record<string, DetailedProfile> = {
      pro_1: {
        id: "pro_1",
        name: "Priya Sharma",
        title: "Master Aesthetician & Hair Specialist",
        bio: "Certified CIDESCO aesthetician with over 7 years of specialized expertise in medical facials, bridal skin preparation, and organic hair spas. Formerly senior cosmetologist at luxury salons in Bengaluru.",
        experienceYears: 7,
        ratingScore: 4.94,
        reviewCount: 382,
        baseZoneName: "Koramangala & Indiranagar, Bengaluru",
        serviceRadiusKm: 15,
        isVerified: true,
        specialties: ["Hydra Facial", "Bridal Hair", "Keratin Spa", "O3+ Radiance", "De-tan Peel"],
        tierOfferings: [
          {
            tier: "Basic",
            name: "Essential Glow Treatment",
            pricePaise: 49900,
            duration: "45 mins",
            brands: "VLCC Natural Cosmeceuticals",
            inclusions: ["Cleansing milk & walnut scrub", "Steam & gentle extraction", "Soothing cucumber mask"],
          },
          {
            tier: "Standard",
            name: "O3+ Radiance Signature",
            pricePaise: 99900,
            duration: "60 mins",
            brands: "O3+ Professional Derma",
            inclusions: ["O3+ brightening peel", "Ozone micro-steam & blackhead suction", "Neck & shoulder acupressure", "Rubber peel-off alginate mask"],
            isPopular: true,
          },
          {
            tier: "Premium",
            name: "Dermalogica 24K Gold Hydra Infusion",
            pricePaise: 189900,
            duration: "80 mins",
            brands: "Dermalogica (USA) & 24K Gold Serum",
            inclusions: ["Multi-acid micro-peel", "Ultrasound cold serum infusion", "Aromatherapy hot towel ritual", "Collagen eye mask & scalp relaxer"],
          },
        ],
        workingHours: [
          { day: "Monday", hours: "09:00 - 19:00", breakTime: "13:00 - 14:00 (Lunch)" },
          { day: "Tuesday", hours: "09:00 - 19:00", breakTime: "13:00 - 14:00 (Lunch)" },
          { day: "Wednesday", hours: "09:00 - 19:00", breakTime: "13:00 - 14:00 (Lunch)" },
          { day: "Thursday", hours: "09:00 - 19:00", breakTime: "13:00 - 14:00 (Lunch)" },
          { day: "Friday", hours: "09:00 - 19:00", breakTime: "13:00 - 14:00 (Lunch)" },
          { day: "Saturday", hours: "08:30 - 20:00", breakTime: "13:30 - 14:30 (Lunch)" },
          { day: "Sunday", hours: "Weekly Off", breakTime: null },
        ],
        portfolio: [
          {
            id: "p1",
            title: "Bridal Golden Glow Transformation",
            description: "Pre-wedding 3-step cellular repair facial for deep hydration and flawless makeup base.",
            imageUrl: "https://images.unsplash.com/photo-1560066984-138dadb4c035?w=600&auto=format&fit=crop&q=80",
            serviceName: "Bridal Facial",
            isVerified: true,
          },
          {
            id: "p2",
            title: "Keratin Smooth & Gloss Finish",
            description: "Formaldehyde-free keratin treatment restoring shine and eliminating frizz in Bengaluru humidity.",
            imageUrl: "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=600&auto=format&fit=crop&q=80",
            serviceName: "Hair Treatment",
            isVerified: true,
          },
          {
            id: "p3",
            title: "Hydra Deep Cleansing & Extraction",
            description: "Ultrasound pore vacuuming followed by hyaluronic acid cold mask infusion.",
            imageUrl: "https://images.unsplash.com/photo-1595476108010-b4d1f102b1b1?w=600&auto=format&fit=crop&q=80",
            serviceName: "Hydra Facial",
            isVerified: true,
          },
          {
            id: "p4",
            title: "Traditional South Indian Bridal Updo",
            description: "Traditional jasmine-braided updo with jewel attachment and 12-hour spray setting.",
            imageUrl: "https://images.unsplash.com/photo-1595476108010-b4d1f102b1b1?w=600&auto=format&fit=crop&q=80",
            serviceName: "Bridal Hair",
            isVerified: true,
          },
        ],
      },
      pro_3: {
        id: "pro_3",
        name: "Ananya Deshmukh",
        title: "Master Tailor & Saree Draping Artisan",
        bio: "12+ years of master craftsmanship in custom bridal blouse cuts, designer lehenga fitting, and precision pleated saree draping. Trusted by 200+ brides across South Bengaluru.",
        experienceYears: 12,
        ratingScore: 4.97,
        reviewCount: 240,
        baseZoneName: "HSR Layout & Koramangala, Bengaluru",
        serviceRadiusKm: 18,
        isVerified: true,
        specialties: ["Saree Draping", "Designer Blouses", "Pico-Fall", "Lehenga Alterations", "Zari Edging"],
        tierOfferings: [
          {
            tier: "Basic",
            name: "Classic Saree Draping & Pleating",
            pricePaise: 29900,
            duration: "25 mins",
            brands: "Ironing & Pin Kit included",
            inclusions: ["Steam touch-up", "Standard pleated front & pallu", "Safety pin stabilizer pack"],
          },
          {
            tier: "Standard",
            name: "Designer Blouse Stitching (with Pad)",
            pricePaise: 79900,
            duration: "48 hr delivery",
            brands: "Interlocking overlock & cotton lining",
            inclusions: ["Home measurement visit", "Padded cups & designer back latkan", "Free alteration warranty"],
            isPopular: true,
          },
          {
            tier: "Premium",
            name: "Bridal Couture Saree & Blouse Ensemble",
            pricePaise: 199900,
            duration: "72 hr delivery",
            brands: "Hand embroidery & French seams",
            inclusions: ["Express doorstep fabric pickup", "Couture fit guarantee", "Pre-event trial fit visit"],
          },
        ],
        workingHours: [
          { day: "Monday", hours: "10:00 - 20:00", breakTime: "14:00 - 15:00" },
          { day: "Tuesday", hours: "10:00 - 20:00", breakTime: "14:00 - 15:00" },
          { day: "Wednesday", hours: "10:00 - 20:00", breakTime: "14:00 - 15:00" },
          { day: "Thursday", hours: "10:00 - 20:00", breakTime: "14:00 - 15:00" },
          { day: "Friday", hours: "10:00 - 20:00", breakTime: "14:00 - 15:00" },
          { day: "Saturday", hours: "09:00 - 20:00", breakTime: "14:00 - 15:00" },
          { day: "Sunday", hours: "10:00 - 17:00", breakTime: "13:30 - 14:30" },
        ],
        portfolio: [
          {
            id: "p1",
            title: "Raw Silk Maggam Work Blouse",
            description: "Custom cut deep-U neck with antique gold zari embroidery and hand-tied silk latkans.",
            imageUrl: "https://images.unsplash.com/photo-1610030469983-98e550d6193c?w=600&auto=format&fit=crop&q=80",
            serviceName: "Custom Stitching",
            isVerified: true,
          },
          {
            id: "p2",
            title: "Royal Kanjeevaram Saree Draping",
            description: "Box pleat drape with zero shoulder slipping for 8-hour traditional wedding ceremony.",
            imageUrl: "https://images.unsplash.com/photo-1583391733956-3750e0ff4e8b?w=600&auto=format&fit=crop&q=80",
            serviceName: "Saree Draping",
            isVerified: true,
          },
        ],
      },
    };

    return profilesDb[id] || profilesDb["pro_1"];
  }, [id]);

  const [reservedSlot, setReservedSlot] = useState<SlotItem | null>(null);

  return (
    <div className="min-h-screen bg-gn-bg-primary py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Navigation Breadcrumb */}
        <div className="flex items-center gap-2 text-xs text-gn-text-tertiary">
          <Link href="/" className="hover:text-gn-text-primary">Home</Link>
          <span>/</span>
          <Link href="/professionals" className="hover:text-gn-text-primary">Verified Professionals</Link>
          <span>/</span>
          <span className="text-gn-text-primary font-medium">{profile.name}</span>
        </div>

        {/* Profile Header Hero */}
        <div className="rounded-gn-xl border border-gn-border-default bg-gn-bg-card p-6 sm:p-8 shadow-gn-sm">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="flex items-start gap-4 sm:gap-6">
              {/* Initials Avatar */}
              <div className="h-20 w-20 sm:h-24 sm:w-24 rounded-full bg-gradient-to-tr from-gn-accent-primary to-gn-accent-secondary text-white font-serif font-bold text-2xl sm:text-3xl flex items-center justify-center shrink-0 shadow-gn-sm">
                {profile.name.split(" ").map((n: string) => n[0]).join("")}
              </div>

              <div className="space-y-1.5">
                <div className="flex flex-wrap items-center gap-2">
                  <h1 className="text-2xl sm:text-3xl font-bold font-serif text-gn-text-primary">
                    {profile.name}
                  </h1>
                  {profile.isVerified && (
                    <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-xs font-bold flex items-center gap-1">
                      ✓ KYC &amp; Skill Verified
                    </span>
                  )}
                </div>

                <p className="text-sm font-medium text-gn-accent-primary">
                  {profile.title}
                </p>

                <p className="text-xs text-gn-text-tertiary flex items-center gap-2 pt-0.5">
                  <span>📍 {profile.baseZoneName}</span>
                  <span>•</span>
                  <span>{profile.experienceYears}+ Years Experience</span>
                  <span>•</span>
                  <span>Serving {profile.serviceRadiusKm} km radius</span>
                </p>

                {/* Rating Strip */}
                <div className="pt-2 flex items-center gap-3">
                  <Rating score={profile.ratingScore} reviewCount={profile.reviewCount} size="md" />
                  <span className="text-xs text-gn-text-tertiary">
                    99.4% On-Time Completion Rate
                  </span>
                </div>
              </div>
            </div>

            {/* Quick Action Button */}
            <div className="flex md:flex-col items-center md:items-end justify-between gap-3 pt-4 md:pt-0 border-t md:border-t-0 border-gn-border-default/60">
              <div className="text-left md:text-right">
                <span className="text-[10px] text-gn-text-tertiary uppercase tracking-wider block">
                  Transparent Base Rate
                </span>
                <span className="text-xl font-bold font-serif text-gn-text-primary">
                  From ₹{Math.round(profile.tierOfferings[0].pricePaise / 100)}
                </span>
              </div>
              <a href="#booking-slots">
                <Button variant="primary" size="md">
                  Book Slot Now ↓
                </Button>
              </a>
            </div>
          </div>

          {/* Bio text */}
          <div className="mt-6 pt-5 border-t border-gn-border-default/80 text-sm text-gn-text-secondary leading-relaxed">
            <h4 className="text-xs font-bold uppercase tracking-wider text-gn-text-tertiary mb-1">
              About Professional Partner
            </h4>
            <p>{profile.bio}</p>
          </div>

          {/* Skills Badges */}
          <div className="mt-4 flex flex-wrap gap-1.5">
            {profile.specialties.map((s: string) => (
              <Badge key={s} variant="outline" className="text-xs py-0.5 px-2.5">
                {s}
              </Badge>
            ))}
          </div>
        </div>

        {/* Transparent Service Tier Comparison */}
        <div className="space-y-4">
          <div>
            <h2 className="text-xl font-bold font-serif text-gn-text-primary">
              Transparent Service Pricing Tiers
            </h2>
            <p className="text-xs text-gn-text-tertiary">
              Guaranteed upfront pricing. No hidden doorstep charges, product surcharges, or tips expected.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {profile.tierOfferings.map((tier: TierOffering) => (
              <div
                key={tier.tier}
                className={`
                  rounded-gn-lg border p-5 flex flex-col justify-between space-y-4 transition-all
                  ${tier.isPopular
                    ? "bg-gn-bg-card border-gn-accent-primary ring-2 ring-gn-accent-primary/20 shadow-gn-md"
                    : "bg-gn-bg-card border-gn-border-default shadow-gn-sm"
                  }
                `}
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className={`text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded ${
                      tier.tier === "Basic" ? "bg-slate-100 text-slate-700" :
                      tier.tier === "Standard" ? "bg-gn-accent-primary-subtle text-gn-accent-primary" :
                      "bg-gn-accent-secondary-subtle text-gn-accent-secondary"
                    }`}>
                      {tier.tier} Tier
                    </span>
                    {tier.isPopular && (
                      <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                        Most Popular
                      </span>
                    )}
                  </div>

                  <div>
                    <h3 className="font-semibold text-gn-text-primary text-base">
                      {tier.name}
                    </h3>
                    <p className="text-xs text-gn-text-tertiary mt-0.5">
                      ⏱ {tier.duration} • Brands: {tier.brands}
                    </p>
                  </div>

                  <div className="pt-2">
                    <span className="text-2xl font-bold font-serif text-gn-text-primary">
                      ₹{Math.round(tier.pricePaise / 100)}
                    </span>
                    <span className="text-xs text-gn-text-tertiary ml-1">all-inclusive</span>
                  </div>

                  <div className="pt-3 border-t border-gn-border-default/60 space-y-2">
                    <span className="text-[11px] font-bold uppercase text-gn-text-tertiary block">
                      Inclusions:
                    </span>
                    <ul className="space-y-1.5 text-xs text-gn-text-secondary">
                      {tier.inclusions.map((inc: string, i: number) => (
                        <li key={i} className="flex items-start gap-1.5">
                          <span className="text-emerald-600 font-bold">✓</span>
                          <span>{inc}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                <a href="#booking-slots" className="pt-2">
                  <Button
                    variant={tier.isPopular ? "primary" : "outline"}
                    size="sm"
                    className="w-full text-xs"
                  >
                    Select {tier.tier} Tier
                  </Button>
                </a>
              </div>
            ))}
          </div>
        </div>

        {/* Authentic Portfolio Gallery */}
        <div className="rounded-gn-xl border border-gn-border-default bg-gn-bg-card p-6 shadow-gn-sm">
          <PortfolioGallery items={profile.portfolio} />
        </div>

        {/* Working Hours & Availability Schedule */}
        <div className="rounded-gn-xl border border-gn-border-default bg-gn-bg-card p-6 shadow-gn-sm space-y-4">
          <div>
            <h3 className="font-serif text-lg font-bold text-gn-text-primary">
              Weekly Shift Schedule &amp; Breaks
            </h3>
            <p className="text-xs text-gn-text-tertiary">
              Appointments are automatically synchronized to partner work shifts to avoid fatigue and ensure precision service.
            </p>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-7 gap-2.5">
            {profile.workingHours.map((wh: WorkingHourSchedule) => (
              <div
                key={wh.day}
                className="bg-gn-bg-secondary/70 p-3 rounded-gn-md border border-gn-border-default/80 text-center space-y-1"
              >
                <span className="text-xs font-bold text-gn-text-primary block">
                  {wh.day}
                </span>
                <span className="text-[11px] font-semibold text-gn-accent-primary block">
                  {wh.hours}
                </span>
                {wh.breakTime && (
                  <span className="text-[10px] text-gn-text-tertiary block">
                    {wh.breakTime}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Active Reservation Banner */}
        {reservedSlot && (
          <div className="p-4 rounded-gn-lg bg-emerald-50 border border-emerald-300 text-emerald-900 text-xs sm:text-sm flex items-center justify-between gn-fade-in shadow-xs">
            <span className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full bg-emerald-500 gn-pulse" />
              <span>
                Active Slot Held: <strong>{new Date(reservedSlot.startTime).toLocaleString("en-IN", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}</strong>
              </span>
            </span>
            <span className="text-xs font-bold text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded">
              Ready for Checkout
            </span>
          </div>
        )}

        {/* Bookable Appointment Slot Selector Section */}
        <div id="booking-slots" className="pt-2">
          <SlotSelector
            professionalId={profile.id}
            professionalName={profile.name}
            onSlotReserved={(slot) => setReservedSlot(slot)}
          />
        </div>
      </div>
    </div>
  );
}
