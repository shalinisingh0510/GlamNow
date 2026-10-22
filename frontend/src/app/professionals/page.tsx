"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { ProfessionalDiscoveryCard } from "@/components/professionals/professional-discovery-card";
import { FIXTURE_CATEGORIES } from "@/lib/fixtures";
import { Button } from "@/components/ui/button";

export default function ProfessionalsDiscoveryPage() {
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [searchSkill, setSearchSkill] = useState<string>("");
  const [minRating, setMinRating] = useState<number>(0);
  const [maxPrice, setMaxPrice] = useState<number>(3000);
  const [instantOnly, setInstantOnly] = useState<boolean>(false);
  const [selectedSector, setSelectedSector] = useState<string>("koramangala");
  const [simulateMapOutage, setSimulateMapOutage] = useState<boolean>(false);

  // Extended professional profiles for discovery
  const professionalsList = useMemo(() => {
    return [
      {
        id: "pro_1",
        name: "Priya Sharma",
        title: "Master Aesthetician & Hair Specialist",
        experienceYears: 7,
        ratingScore: 4.94,
        reviewCount: 382,
        etaMinutes: simulateMapOutage ? 30 : 18,
        specialties: ["Hydra Facial", "Bridal Hair", "Keratin Spa", "O3+ Radiance"],
        category: "beauty",
        baseZoneName: "Koramangala, Bengaluru",
        isVerified: true,
        isInstantBooking: true,
        tierPrices: { basic: 49900, standard: 99900, premium: 189900 },
        portfolioSamples: [
          "https://images.unsplash.com/photo-1560066984-138dadb4c035?w=300&auto=format&fit=crop&q=80",
          "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=300&auto=format&fit=crop&q=80",
          "https://images.unsplash.com/photo-1595476108010-b4d1f102b1b1?w=300&auto=format&fit=crop&q=80",
        ],
        availableSlotsCount: 6,
      },
      {
        id: "pro_2",
        name: "Ramesh Kumar",
        title: "Men's Master Barber & Beard Stylist",
        experienceYears: 9,
        ratingScore: 4.88,
        reviewCount: 512,
        etaMinutes: simulateMapOutage ? 25 : 22,
        specialties: ["Fade Cuts", "Beard Sculpting", "Charcoal Detan", "Head Acupressure"],
        category: "grooming",
        baseZoneName: "Indiranagar, Bengaluru",
        isVerified: true,
        isInstantBooking: true,
        tierPrices: { basic: 34900, standard: 69900, premium: 129900 },
        portfolioSamples: [
          "https://images.unsplash.com/photo-1503951914875-452162b0f3f1?w=300&auto=format&fit=crop&q=80",
          "https://images.unsplash.com/photo-1622286342621-4bd786c2447c?w=300&auto=format&fit=crop&q=80",
        ],
        availableSlotsCount: 4,
      },
      {
        id: "pro_3",
        name: "Ananya Deshmukh",
        title: "Master Tailor & Saree Draping Artisan",
        experienceYears: 12,
        ratingScore: 4.97,
        reviewCount: 240,
        etaMinutes: simulateMapOutage ? 35 : 28,
        specialties: ["Saree Draping", "Designer Blouses", "Pico-Fall", "Lehenga Alterations"],
        category: "tailoring",
        baseZoneName: "HSR Layout, Bengaluru",
        isVerified: true,
        isInstantBooking: false,
        tierPrices: { basic: 29900, standard: 79900, premium: 199900 },
        portfolioSamples: [
          "https://images.unsplash.com/photo-1610030469983-98e550d6193c?w=300&auto=format&fit=crop&q=80",
          "https://images.unsplash.com/photo-1583391733956-3750e0ff4e8b?w=300&auto=format&fit=crop&q=80",
        ],
        availableSlotsCount: 3,
      },
      {
        id: "pro_4",
        name: "Deepak Verma",
        title: "Certified Spa & Deep Tissue Therapist",
        experienceYears: 6,
        ratingScore: 4.91,
        reviewCount: 195,
        etaMinutes: simulateMapOutage ? 25 : 20,
        specialties: ["Deep Tissue", "Swedish Relaxation", "Potli Warm Therapy", "Foot Reflexology"],
        category: "massage",
        baseZoneName: "Koramangala, Bengaluru",
        isVerified: true,
        isInstantBooking: true,
        tierPrices: { basic: 89900, standard: 149900, premium: 249900 },
        portfolioSamples: [
          "https://images.unsplash.com/photo-1544161515-4ab6ce6db874?w=300&auto=format&fit=crop&q=80",
          "https://images.unsplash.com/photo-1519823551278-64ac92734fb1?w=300&auto=format&fit=crop&q=80",
        ],
        availableSlotsCount: 5,
      },
    ];
  }, [simulateMapOutage]);

  // Filter logic
  const filteredProfessionals = useMemo(() => {
    return professionalsList.filter((pro) => {
      // Category
      if (selectedCategory !== "all" && pro.category !== selectedCategory) {
        return false;
      }
      // Skill search
      if (searchSkill.trim()) {
        const query = searchSkill.toLowerCase();
        const hasSkill = pro.specialties.some((s) => s.toLowerCase().includes(query));
        const matchesName = pro.name.toLowerCase().includes(query);
        if (!hasSkill && !matchesName) return false;
      }
      // Rating
      if (pro.ratingScore < minRating) {
        return false;
      }
      // Max price (check starting basic price)
      if (Math.round(pro.tierPrices.basic / 100) > maxPrice) {
        return false;
      }
      // Instant only
      if (instantOnly && !pro.isInstantBooking) {
        return false;
      }
      return true;
    });
  }, [professionalsList, selectedCategory, searchSkill, minRating, maxPrice, instantOnly]);

  return (
    <div className="min-h-screen bg-gn-bg-primary py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Breadcrumb & Header */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-xs text-gn-text-tertiary">
            <Link href="/" className="hover:text-gn-text-primary">Home</Link>
            <span>/</span>
            <span className="text-gn-text-primary font-medium">Verified Professionals</span>
          </div>
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold font-serif text-gn-text-primary tracking-tight">
                Discover Verified Stylists &amp; Artisans
              </h1>
              <p className="text-sm text-gn-text-secondary mt-1 max-w-2xl">
                Choose specific vetted professionals by transparent tier price, authentic portfolio, review score, and live arrival estimates.
              </p>
            </div>

            {/* Provider Outage Fallback Demonstration Toggle */}
            <div className="bg-gn-bg-card p-3 rounded-gn-md border border-gn-border-default shadow-xs flex items-center gap-3">
              <div className="text-right">
                <span className="text-xs font-bold text-gn-text-primary block">
                  Map Routing Adapter
                </span>
                <span className="text-[10px] text-gn-text-tertiary">
                  {simulateMapOutage ? "Simulating Outage (Fallback Active)" : "Google Maps Live"}
                </span>
              </div>
              <button
                onClick={() => setSimulateMapOutage(!simulateMapOutage)}
                className={`
                  relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out gn-focus-ring
                  ${simulateMapOutage ? "bg-amber-500" : "bg-emerald-500"}
                `}
                title="Toggle provider fallback mode"
              >
                <span
                  className={`
                    pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-md ring-0 transition duration-200 ease-in-out
                    ${simulateMapOutage ? "translate-x-5" : "translate-x-0"}
                  `}
                />
              </button>
            </div>
          </div>
        </div>

        {/* Fallback Notice Banner (when map outage simulated) */}
        {simulateMapOutage && (
          <div className="p-4 rounded-gn-md bg-amber-50 border border-amber-300 text-amber-900 text-xs sm:text-sm flex items-start gap-3 gn-fade-in shadow-xs">
            <span className="text-lg">⚠️</span>
            <div className="space-y-0.5">
              <span className="font-bold">Live Traffic Provider Offline — Fallback Matrix Engaged</span>
              <p className="text-amber-800 text-xs">
                In compliance with ADR-0004, GlamNow never invents false live GPS coordinates when third-party mapping providers time out.
                Arrival times are calculated using standard urban straight-line transit models (~20 km/h + 10 min salon prep buffer).
              </p>
            </div>
          </div>
        )}

        {/* Filter Toolbar */}
        <div className="bg-gn-bg-card rounded-gn-lg border border-gn-border-default p-5 shadow-gn-sm space-y-4">
          {/* Top row: Search input & Category pills */}
          <div className="flex flex-col md:flex-row gap-4 items-stretch md:items-center justify-between">
            {/* Skill / Name Search */}
            <div className="relative flex-1 max-w-md">
              <input
                type="text"
                placeholder="Search by skill (e.g., Hydra Facial, Saree Draping)..."
                value={searchSkill}
                onChange={(e) => setSearchSkill(e.target.value)}
                className="w-full h-10 pl-9 pr-4 rounded-gn-md border border-gn-border-default bg-gn-bg-secondary text-sm text-gn-text-primary placeholder:text-gn-text-muted gn-focus-ring"
              />
              <span className="absolute left-3 top-2.5 text-gn-text-tertiary">🔍</span>
              {searchSkill && (
                <button
                  onClick={() => setSearchSkill("")}
                  className="absolute right-3 top-2.5 text-xs text-gn-text-tertiary hover:text-gn-text-primary font-bold"
                >
                  ✕
                </button>
              )}
            </div>

            {/* Sector / Locality Selector */}
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-gn-text-tertiary">Sector:</span>
              <select
                value={selectedSector}
                onChange={(e) => setSelectedSector(e.target.value)}
                className="h-10 px-3 rounded-gn-md border border-gn-border-default bg-gn-bg-secondary text-xs text-gn-text-primary font-medium gn-focus-ring cursor-pointer"
              >
                <option value="koramangala">Koramangala (560034)</option>
                <option value="indiranagar">Indiranagar (560038)</option>
                <option value="hsr">HSR Layout (560102)</option>
                <option value="whitefield">Whitefield (560066)</option>
                <option value="jayanagar">Jayanagar (560041)</option>
              </select>
            </div>

            {/* Instant Booking Toggle */}
            <label className="flex items-center gap-2 cursor-pointer select-none text-xs font-semibold text-gn-text-secondary">
              <input
                type="checkbox"
                checked={instantOnly}
                onChange={(e) => setInstantOnly(e.target.checked)}
                className="h-4 w-4 rounded border-gn-border-default text-gn-accent-primary focus:ring-gn-accent-primary"
              />
              <span>⚡ Instant Arrival Only (&lt;30m)</span>
            </label>
          </div>

          {/* Category Filter Pills */}
          <div className="flex flex-wrap gap-2 pt-2 border-t border-gn-border-default/60">
            <button
              onClick={() => setSelectedCategory("all")}
              className={`
                px-3 py-1.5 rounded-full text-xs font-semibold transition-all cursor-pointer gn-focus-ring
                ${selectedCategory === "all"
                  ? "bg-gn-accent-primary text-white shadow-xs"
                  : "bg-gn-bg-secondary text-gn-text-secondary hover:bg-gn-bg-secondary/80"
                }
              `}
            >
              All Categories
            </button>
            {FIXTURE_CATEGORIES.map((cat) => (
              <button
                key={cat.id}
                onClick={() => setSelectedCategory(cat.id)}
                className={`
                  px-3 py-1.5 rounded-full text-xs font-semibold transition-all cursor-pointer flex items-center gap-1 gn-focus-ring
                  ${selectedCategory === cat.id
                    ? "bg-gn-accent-primary text-white shadow-xs"
                    : "bg-gn-bg-secondary text-gn-text-secondary hover:bg-gn-bg-secondary/80"
                  }
                `}
              >
                <span>{cat.icon}</span>
                <span>{cat.name}</span>
              </button>
            ))}
          </div>

          {/* Secondary Filters: Rating & Max Price */}
          <div className="flex flex-wrap items-center justify-between gap-4 pt-3 border-t border-gn-border-default/60 text-xs">
            <div className="flex items-center gap-4">
              <span className="font-semibold text-gn-text-tertiary">Min Rating:</span>
              <div className="flex gap-1">
                {[0, 4.5, 4.8, 4.9].map((score) => (
                  <button
                    key={score}
                    onClick={() => setMinRating(score)}
                    className={`
                      px-2.5 py-1 rounded text-xs transition-all cursor-pointer
                      ${minRating === score
                        ? "bg-gn-accent-secondary text-white font-bold"
                        : "bg-gn-bg-secondary text-gn-text-secondary hover:bg-gn-bg-secondary/80"
                      }
                    `}
                  >
                    {score === 0 ? "Any" : `★ ${score}+`}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex items-center gap-3">
              <span className="font-semibold text-gn-text-tertiary">Starting Rate:</span>
              <span className="font-bold text-gn-text-primary">Under ₹{maxPrice}</span>
              <input
                type="range"
                min="300"
                max="3000"
                step="100"
                value={maxPrice}
                onChange={(e) => setMaxPrice(Number(e.target.value))}
                className="w-28 accent-gn-accent-primary cursor-pointer"
              />
            </div>
          </div>
        </div>

        {/* Results Count & Grid */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold text-gn-text-secondary">
              Showing <strong>{filteredProfessionals.length}</strong> verified partner{filteredProfessionals.length === 1 ? "" : "s"}
            </span>
            <span className="text-xs text-gn-text-tertiary">
              Arrival estimate calculated for <strong>{selectedSector.toUpperCase()}</strong>
            </span>
          </div>

          {filteredProfessionals.length === 0 ? (
            <div className="p-12 text-center rounded-gn-lg border border-dashed border-gn-border-default bg-gn-bg-card space-y-3">
              <span className="text-3xl">🔍</span>
              <h3 className="font-semibold text-gn-text-primary text-base">No matching professionals found</h3>
              <p className="text-xs text-gn-text-tertiary max-w-md mx-auto">
                Try widening your rating score, raising the maximum price, or clearing your skill keyword search.
              </p>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setSelectedCategory("all");
                  setSearchSkill("");
                  setMinRating(0);
                  setMaxPrice(3000);
                  setInstantOnly(false);
                }}
              >
                Reset All Filters
              </Button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-6">
              {filteredProfessionals.map((pro) => (
                <ProfessionalDiscoveryCard
                  key={pro.id}
                  id={pro.id}
                  name={pro.name}
                  title={pro.title}
                  experienceYears={pro.experienceYears}
                  ratingScore={pro.ratingScore}
                  reviewCount={pro.reviewCount}
                  etaMinutes={pro.etaMinutes}
                  specialties={pro.specialties}
                  baseZoneName={pro.baseZoneName}
                  isVerified={pro.isVerified}
                  isInstantBooking={pro.isInstantBooking}
                  tierPrices={pro.tierPrices}
                  portfolioSamples={pro.portfolioSamples}
                  isFallbackLocation={simulateMapOutage}
                  fallbackMessage="Live map provider offline. Using regional transit matrix."
                  availableSlotsCount={pro.availableSlotsCount}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
