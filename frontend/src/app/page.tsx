"use client";

import { useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Dialog } from "@/components/ui/dialog";
import { BottomSheet } from "@/components/ui/bottom-sheet";
import { PricingTierCard } from "@/components/ui/pricing-tier-card";
import { ServiceCard } from "@/components/ui/service-card";
import { ProfessionalCard } from "@/components/ui/professional-card";
import { StatusIndicator } from "@/components/ui/status-indicator";
import { EmptyState } from "@/components/ui/empty-state";
import {
  FIXTURE_CATEGORIES,
  FIXTURE_SERVICES,
  FIXTURE_PROFESSIONALS,
  FIXTURE_TAILORING_SERVICES,
  FIXTURE_SERVICEABLE_ZONES,
} from "@/lib/fixtures";
import { useCategories, useServices, useCalculateQuote } from "@/features/catalog/hooks";
import type { QuoteResponseDto, ServiceSummaryDto } from "@/features/catalog/api";
import { BookingModal } from "@/features/booking/booking-modal";

function buildFallbackQuote(
  service: ServiceSummaryDto,
  tier: "basic" | "standard" | "premium",
  addOns: string[],
  promo: string
): QuoteResponseDto {
  const basePaise = tier === "basic" ? 39900 : tier === "standard" ? 79900 : 149900;
  const addOnsPaise = addOns.length * 29900;
  const travelPaise = 0;
  const deliveryPaise = service.workflow_type === "tailoring_doorstep" ? 9900 : 0;
  const subtotal = basePaise + addOnsPaise + travelPaise + deliveryPaise;
  const discount = promo.toUpperCase() === "WELCOME50" ? Math.min(Math.round(subtotal * 0.5), 15000) : 0;
  const net = Math.max(0, subtotal - discount);
  const cgst = Math.round(net * 0.09);
  const sgst = Math.round(net * 0.09);

  return {
    quote_id: `preview_quote_${service.id}_${tier}`,
    service_id: service.id,
    service_name: service.name,
    tier,
    tier_name: `${tier.toUpperCase()} Signature`,
    duration_minutes: service.duration_minutes,
    brands: tier === "basic" ? "VLCC & Streax" : tier === "standard" ? "O3+ & L'Oréal" : "Kérastase Paris",
    inclusions: ["Verified professional", "Sterile sealed pouch", "Complete post-care disposal"],
    base_price_paise: basePaise,
    add_ons: addOns.map((id) => ({
      id,
      name: id === "addon_detan" ? "Express De-Tan Pack" : "Aromatherapy Scalp Massage",
      price_paise: 29900,
      duration_minutes: 15,
    })),
    travel_fee_paise: travelPaise,
    pickup_delivery_fee_paise: deliveryPaise,
    subtotal_paise: subtotal,
    discount_paise: discount,
    tax_cgst_paise: cgst,
    tax_sgst_paise: sgst,
    tax_rate_percent: 18.0,
    total_paise: net + cgst + sgst,
    expires_at: "2026-10-21T14:30:00.000Z",
    immutable_price_snapshot: { snapshot_ver: "1.0", integrity: "verified" },
  };
}

export default function HomePage() {
  const [selectedCategory, setSelectedCategory] = useState("beauty");
  const [catalogSearch, setCatalogSearch] = useState("");
  const [selectedTierFilter, setSelectedTierFilter] = useState<"all" | "basic" | "standard" | "premium">("all");
  const [pincodeInput, setPincodeInput] = useState("560038");
  const [serviceableNotice, setServiceableNotice] = useState<string | null>(
    "Verified: Indiranagar Zone (560038) has 14 professionals available for 15–25 min dispatch."
  );
  const [selectedProId, setSelectedProId] = useState<string | null>("pro_1");
  const [tailoringStep, setTailoringStep] = useState(1);

  // Dynamic Server Catalog Queries with TanStack Query
  const { data: serverCategories } = useCategories();
  const { data: serverServices } = useServices(
    selectedCategory === "all" ? undefined : selectedCategory,
    catalogSearch || undefined
  );

  // Modal and Sheet states for testing interactions
  const [tierModalService, setTierModalService] = useState<ServiceSummaryDto | null>(null);
  const [activeTier, setActiveTier] = useState<"basic" | "standard" | "premium">("standard");
  const [selectedAddOns, setSelectedAddOns] = useState<string[]>([]);
  const [promoCodeInput, setPromoCodeInput] = useState("");
  const [calculatedQuote, setCalculatedQuote] = useState<QuoteResponseDto | null>(null);
  const quoteMutation = useCalculateQuote();

  const [mobileCartSheetOpen, setMobileCartSheetOpen] = useState(false);
  const [cartCount, setCartCount] = useState(2);
  const [bagNotice, setBagNotice] = useState<string | null>(null);

  const [bookingModalOpen, setBookingModalOpen] = useState(false);
  const [bookingModalService, setBookingModalService] = useState<ServiceSummaryDto | null>(null);

  const handleOpenBooking = (
    service: ServiceSummaryDto,
    tier: "basic" | "standard" | "premium" = "standard"
  ) => {
    setBookingModalService(service);
    setActiveTier(tier);
    setBookingModalOpen(true);
    setTierModalService(null);
    setMobileCartSheetOpen(false);
  };

  const handleCheckServiceability = (e: React.FormEvent) => {
    e.preventDefault();
    const zone = FIXTURE_SERVICEABLE_ZONES.find((z) => z.pincode === pincodeInput.trim());
    if (zone) {
      setServiceableNotice(
        `Verified: ${zone.area} (${zone.pincode}) has ${zone.activePros} professionals available for ${zone.etaMin}–${zone.etaMax} min dispatch.`
      );
    } else {
      setServiceableNotice(`Zone ${pincodeInput} is pending expansion. Select Indiranagar (560038) or Koramangala (560034).`);
    }
  };

  const handleAddToCart = (serviceName: string) => {
    setCartCount((prev) => prev + 1);
    setBagNotice(`Added "${serviceName}" to your service bag.`);
    setTimeout(() => setBagNotice(null), 3000);
  };

  const computeQuoteForService = async (
    service: ServiceSummaryDto,
    tier: "basic" | "standard" | "premium",
    addOns: string[] = selectedAddOns,
    promo: string = promoCodeInput
  ) => {
    try {
      const res = await quoteMutation.mutateAsync({
        service_id: service.id,
        tier,
        add_on_ids: addOns.length > 0 ? addOns : undefined,
        discount_code: promo.trim() || undefined,
      });
      if (res) {
        setCalculatedQuote(res);
      }
    } catch {
      // Fallback calculation for preview if backend is starting
      setCalculatedQuote(buildFallbackQuote(service, tier, addOns, promo));
    }
  };

  const handleOpenTierModal = (service: ServiceSummaryDto) => {
    setTierModalService(service);
    setActiveTier("standard");
    setSelectedAddOns([]);
    setPromoCodeInput("");
    computeQuoteForService(service, "standard", [], "");
  };

  // Categories list (combines server + fixtures)
  const categoriesList = serverCategories && serverCategories.length > 0
    ? serverCategories
    : FIXTURE_CATEGORIES.map((c, i) => ({
        id: c.id,
        slug: c.id,
        name: c.name,
        description: null,
        icon: c.icon,
        display_order: i + 1,
        is_active: true,
        service_count: parseInt(c.count) || 8,
      }));

  // Services list
  const activeServices: ServiceSummaryDto[] = serverServices && serverServices.length > 0
    ? serverServices
    : FIXTURE_SERVICES.filter(
        (s) => (s.categoryId === selectedCategory || selectedCategory === "all") &&
               (!catalogSearch || s.name.toLowerCase().includes(catalogSearch.toLowerCase()) || s.description.toLowerCase().includes(catalogSearch.toLowerCase()))
      ).map((s) => ({
        id: s.id,
        category_id: s.categoryId,
        category_name: s.categoryName,
        slug: s.id,
        name: s.name,
        description: s.description,
        icon: s.icon,
        workflow_type: s.categoryId.includes("tailoring") ? "tailoring_doorstep" : "at_home_visit",
        starting_price_paise: s.startingPricePaise,
        duration_minutes: s.durationMinutes,
        available_tiers: s.tiers.map((t) => t.tier),
      }));

  return (
    <div className="flex flex-col min-h-screen">
      {/* Dynamic Toast / Bag Notification */}
      {bagNotice && (
        <div className="fixed bottom-6 right-6 z-50 p-4 rounded-gn-lg bg-gn-text-primary text-gn-bg-primary shadow-gn-xl gn-slide-up flex items-center gap-3">
          <span className="text-emerald-400 font-bold">✓</span>
          <span className="text-sm font-medium">{bagNotice}</span>
          <button
            onClick={() => setMobileCartSheetOpen(true)}
            className="text-xs text-gn-accent-secondary font-bold underline ml-2 cursor-pointer"
          >
            View Bag ({cartCount})
          </button>
        </div>
      )}

      {/* ─── Hero Section ─── */}
      <section className="relative overflow-hidden bg-gradient-to-b from-gn-bg-secondary via-gn-bg-primary to-gn-bg-primary pt-12 pb-20 border-b border-gn-border-default">
        {/* Ambient Blur Accents */}
        <div className="absolute top-0 right-1/4 -mt-20 w-96 h-96 bg-gn-accent-primary-subtle rounded-full blur-3xl opacity-50 pointer-events-none" />
        <div className="absolute bottom-0 left-1/3 -mb-20 w-80 h-80 bg-gn-accent-secondary-subtle rounded-full blur-3xl opacity-50 pointer-events-none" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
            {/* Left Column: Vision & Pitch */}
            <div className="lg:col-span-7 space-y-6 text-center lg:text-left">
              <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-gn-full bg-gn-accent-primary-subtle border border-gn-accent-primary/20 text-gn-accent-primary text-xs font-semibold">
                <span>⚡ India&apos;s Fastest At-Home Salon &amp; Tailoring</span>
                <span className="w-1.5 h-1.5 rounded-full bg-gn-accent-primary" />
                <span>15–30 Min Arrival</span>
              </div>

              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold font-serif tracking-tight text-gn-text-primary leading-[1.15]">
                Luxury salon, spa &amp; custom tailoring at your doorstep.
              </h1>

              <p className="text-lg sm:text-xl text-gn-text-secondary max-w-2xl font-normal leading-relaxed">
                Book top-rated, background-verified professionals in minutes. Compare transparent service tiers,
                pick your favourite stylist, or schedule doorstep custom stitching with home fabric pickup.
              </p>

              {/* Serviceability / PIN code search bar */}
              <form onSubmit={handleCheckServiceability} className="flex flex-col sm:flex-row gap-2 max-w-lg mx-auto lg:mx-0 pt-2">
                <div className="relative flex-1">
                  <Input
                    type="text"
                    placeholder="Enter your 6-digit PIN code..."
                    value={pincodeInput}
                    onChange={(e) => setPincodeInput(e.target.value)}
                    maxLength={6}
                    className="pl-10 font-medium"
                  />
                  <svg className="w-4 h-4 text-gn-text-tertiary absolute left-3.5 top-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                </div>
                <Button type="submit" variant="primary" size="md" className="shrink-0">
                  Check Availability
                </Button>
              </form>

              {serviceableNotice && (
                <p className="text-xs text-gn-success font-medium flex items-center justify-center lg:justify-start gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-emerald-500 inline-block" />
                  {serviceableNotice}
                </p>
              )}

              {/* Trust Indicators */}
              <div className="grid grid-cols-3 gap-4 pt-4 border-t border-gn-border-default/80 max-w-lg mx-auto lg:mx-0">
                <div>
                  <p className="text-2xl font-bold font-serif text-gn-text-primary">15-30m</p>
                  <p className="text-xs text-gn-text-tertiary">Quick Dispatch</p>
                </div>
                <div>
                  <p className="text-2xl font-bold font-serif text-gn-text-primary">4.92★</p>
                  <p className="text-xs text-gn-text-tertiary">10k+ Reviews</p>
                </div>
                <div>
                  <p className="text-2xl font-bold font-serif text-gn-text-primary">100%</p>
                  <p className="text-xs text-gn-text-tertiary">Sanitized Single-use Kits</p>
                </div>
              </div>
            </div>

            {/* Right Column: Dynamic Live Preview Card */}
            <div className="lg:col-span-5">
              <Card className="p-6 bg-gn-bg-card border-gn-border-strong shadow-gn-lg relative overflow-hidden">
                <div className="flex items-center justify-between pb-4 border-b border-gn-border-default">
                  <StatusIndicator status="dispatched" pulse />
                  <Badge variant="primary">Instant Booking</Badge>
                </div>

                <div className="py-5 space-y-4">
                  <div className="flex items-start gap-4 p-3 rounded-gn-md bg-gn-bg-secondary/60 border border-gn-border-default">
                    <div className="h-12 w-12 rounded-full bg-gn-accent-primary text-white flex items-center justify-center font-bold font-serif shrink-0">
                      PS
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <h4 className="font-semibold text-sm text-gn-text-primary truncate">Priya Sharma</h4>
                        <span className="text-xs font-bold text-amber-600">★ 4.94</span>
                      </div>
                      <p className="text-xs text-gn-text-secondary truncate">Senior Aesthetician • L&apos;Oréal Certified</p>
                      <div className="flex items-center gap-2 mt-2">
                        <Badge variant="success" className="text-[10px] py-0">Arriving in 18 min</Badge>
                        <span className="text-xs font-semibold text-gn-accent-primary">₹799 snapshot price</span>
                      </div>
                    </div>
                  </div>

                  <div className="p-3.5 rounded-gn-md border border-dashed border-gn-accent-secondary/50 bg-gn-accent-secondary-subtle/30 space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-medium text-gn-text-primary">Custom Tailoring Add-on:</span>
                      <span className="font-bold text-gn-accent-secondary-hover">Doorstep Measurement</span>
                    </div>
                    <p className="text-xs text-gn-text-secondary">
                      Need a blouse or salwar stitched? Our master tailor collects fabric &amp; fits sample garments in the same visit.
                    </p>
                  </div>
                </div>

                <Link href="#services" className="block w-full">
                  <Button variant="primary" size="lg" className="w-full">
                    Explore All Services &amp; Tiers
                  </Button>
                </Link>
              </Card>
            </div>
          </div>
        </div>
      </section>

      {/* ─── Categories Navigation Bar ─── */}
      <section className="bg-gn-bg-card border-b border-gn-border-default py-4 sticky top-16 sm:top-20 z-30 shadow-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-3">
          <div className="flex items-center gap-3 overflow-x-auto pb-1 scrollbar-none">
            <button
              onClick={() => setSelectedCategory("all")}
              className={`
                flex items-center gap-2 px-3.5 py-2 rounded-gn-lg border text-xs font-semibold whitespace-nowrap cursor-pointer transition-all
                ${selectedCategory === "all"
                  ? "bg-gn-accent-primary text-white border-gn-accent-primary shadow-gn-sm"
                  : "bg-gn-bg-card text-gn-text-secondary border-gn-border-default hover:border-gn-border-strong hover:bg-gn-bg-secondary"
                }
              `}
            >
              <span>✨</span>
              <span>All Categories</span>
            </button>
            {categoriesList.map((cat) => (
              <button
                key={cat.id}
                onClick={() => setSelectedCategory(cat.id)}
                className={`
                  flex items-center gap-2 px-3.5 py-2 rounded-gn-lg border text-xs font-medium whitespace-nowrap cursor-pointer transition-all
                  ${selectedCategory === cat.id
                    ? "bg-gn-accent-primary text-white border-gn-accent-primary shadow-gn-sm font-semibold"
                    : "bg-gn-bg-card text-gn-text-secondary border-gn-border-default hover:border-gn-border-strong hover:bg-gn-bg-secondary"
                  }
                `}
              >
                <span className="text-sm">{cat.icon}</span>
                <span>{cat.name}</span>
              </button>
            ))}
          </div>

          {/* Catalog Keyword Search */}
          <div className="flex items-center gap-2 max-w-md">
            <div className="relative w-full">
              <input
                type="text"
                placeholder="Search services (e.g. facial, haircut, saree draping, blouse stitching)..."
                value={catalogSearch}
                onChange={(e) => setCatalogSearch(e.target.value)}
                className="w-full h-9 rounded-gn-md border border-gn-border-default bg-gn-bg-secondary px-3 text-xs text-gn-text-primary placeholder:text-gn-text-muted gn-focus-ring"
              />
              {catalogSearch && (
                <button
                  onClick={() => setCatalogSearch("")}
                  className="absolute right-2 top-2 text-xs text-gn-text-muted hover:text-gn-text-primary"
                >
                  ✕
                </button>
              )}
            </div>
            <Link href="/admin/catalog">
              <Button variant="ghost" size="sm" className="text-xs whitespace-nowrap hidden sm:inline-flex">
                Admin Catalog ⚙
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* ─── Service Catalog Grid with ServiceCard Component ─── */}
      <section className="py-12 bg-gn-bg-secondary/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h3 className="text-2xl font-bold font-serif text-gn-text-primary">Featured Services</h3>
              <p className="text-xs sm:text-sm text-gn-text-secondary mt-0.5">
                Dynamic catalog with transparent multi-tier options and single-use sterile kits.
              </p>
            </div>
            <button
              onClick={() => setMobileCartSheetOpen(true)}
              className="md:hidden text-xs font-semibold text-gn-accent-primary flex items-center gap-1 cursor-pointer"
            >
              <span>View Bag ({cartCount})</span>
              <span>→</span>
            </button>
          </div>

          {activeServices.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {activeServices.map((service) => (
                <ServiceCard
                  key={service.id}
                  id={service.id}
                  category={service.category_name || service.category_id}
                  name={service.name}
                  description={service.description}
                  durationMinutes={service.duration_minutes}
                  startingPricePaise={service.starting_price_paise}
                  icon={service.icon}
                  onSelectTier={() => handleOpenTierModal(service)}
                  onQuickBook={() => handleAddToCart(service.name)}
                />
              ))}
            </div>
          ) : (
            <EmptyState
              title="No services found matching your criteria"
              description="Try adjusting your category filter or search keywords."
              actionLabel="Clear Search"
              onAction={() => {
                setCatalogSearch("");
                setSelectedCategory("all");
              }}
            />
          )}
        </div>
      </section>

      {/* ─── Multi-Tier Service Comparison (Basic, Standard, Premium) ─── */}
      <section id="services" className="py-16 bg-gn-bg-primary">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-12 space-y-3">
            <Badge variant="secondary">Transparent Multi-Tier Pricing</Badge>
            <h2 className="text-3xl sm:text-4xl font-bold font-serif text-gn-text-primary">
              Choose the exact experience tier you desire.
            </h2>
            <p className="text-gn-text-secondary text-sm sm:text-base">
              Every tier delivers verified background-checked professionals with sterile equipment. Compare products, consultation time, and inclusions before you book.
            </p>

            <div className="inline-flex p-1 rounded-gn-lg bg-gn-bg-secondary border border-gn-border-default mt-4">
              {(["all", "basic", "standard", "premium"] as const).map((t) => (
                <button
                  key={t}
                  onClick={() => setSelectedTierFilter(t)}
                  className={`px-4 py-1.5 text-xs font-semibold rounded-gn-md capitalize transition-all cursor-pointer ${
                    selectedTierFilter === t
                      ? "bg-gn-bg-card text-gn-text-primary shadow-gn-sm"
                      : "text-gn-text-tertiary hover:text-gn-text-primary"
                  }`}
                >
                  {t === "all" ? "Compare All Tiers" : `${t} Tier`}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {(selectedTierFilter === "all" || selectedTierFilter === "basic") && (
              <PricingTierCard
                tier="basic"
                title="Essential Care"
                description="Ideal for routine grooming, quick touch-ups, and budget-friendly speed."
                pricePaise={39900}
                durationMinutes={30}
                brands="Streax, VLCC & Garnier Professional"
                inclusions={[
                  "Standard branded consumables",
                  "Sanitized single-use tool pouch",
                  "Verified professional (1+ yr exp)",
                  "20–30 min average duration",
                ]}
                onSelect={() => handleAddToCart("Basic Essential Care")}
              />
            )}

            {(selectedTierFilter === "all" || selectedTierFilter === "standard") && (
              <PricingTierCard
                tier="standard"
                title="Signature Experience"
                description="Premium branded formulations, shoulder massage relaxer, and senior specialists."
                pricePaise={79900}
                durationMinutes={50}
                brands="O3+, Cheryl's Cosmeceuticals & L'Oréal Serie Expert"
                isPopular
                inclusions={[
                  "Top-tier professional brands (O3+, Cheryl's)",
                  "10-minute complimentary head & shoulder relaxer",
                  "Senior aesthetician (3+ yrs exp, 4.8+ rating)",
                  "Complete disposable cleanup sheet",
                ]}
                onSelect={() => handleAddToCart("Standard Signature Care")}
              />
            )}

            {(selectedTierFilter === "all" || selectedTierFilter === "premium") && (
              <PricingTierCard
                tier="premium"
                title="Royal Indulgence"
                description="Imported dermatological products, master stylists, aromatherapy & full relaxation ritual."
                pricePaise={149900}
                durationMinutes={75}
                brands="Kérastase Paris, Dermalogica & Truefitt & Hill"
                inclusions={[
                  "Luxury salon imports (Kérastase, Dermalogica)",
                  "Master artist (7+ yrs exp, celebrity portfolio)",
                  "Essential oils & sensory ambient setup",
                  "Unhurried, dedicated bespoke session",
                ]}
                onSelect={() => handleAddToCart("Premium Royal Indulgence")}
              />
            )}
          </div>
        </div>
      </section>

      {/* ─── Choose a Specific Professional with ProfessionalCard Component ─── */}
      <section id="professionals" className="py-16 bg-gn-bg-secondary/40 border-y border-gn-border-default">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-start md:items-end justify-between mb-10 gap-4">
            <div>
              <Badge variant="primary" className="mb-2">Choose Your Professional</Badge>
              <h2 className="text-3xl font-bold font-serif text-gn-text-primary">
                Select by rating, portfolio &amp; live arrival estimate.
              </h2>
              <p className="text-sm text-gn-text-secondary mt-1 max-w-xl">
                Compare verified professionals nearby. View authentic customer ratings, completed orders count, and immediate dispatch readiness.
              </p>
            </div>
            <span className="text-xs font-semibold text-gn-accent-primary">
              Showing active pros in Bengaluru
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {FIXTURE_PROFESSIONALS.slice(0, 3).map((pro) => (
              <ProfessionalCard
                key={pro.id}
                id={pro.id}
                name={pro.name}
                title={pro.title}
                experienceYears={pro.experienceYears}
                ratingScore={pro.ratingScore}
                reviewCount={pro.reviewCount}
                etaMinutes={pro.etaMinutes}
                specialties={pro.specialties}
                startingPricePaise={pro.startingPricePaise}
                avatarText={pro.avatarText}
                isVerified={pro.isVerified}
                isSelected={selectedProId === pro.id}
                onSelect={() => setSelectedProId(pro.id)}
              />
            ))}
          </div>
        </div>
      </section>

      {/* ─── Doorstep Custom Tailoring & Alterations Studio ─── */}
      <section id="tailoring" className="py-16 bg-gn-bg-primary">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl mx-auto text-center mb-12 space-y-3">
            <Badge variant="secondary">Doorstep Tailoring &amp; Alterations</Badge>
            <h2 className="text-3xl sm:text-4xl font-bold font-serif text-gn-text-primary">
              Custom stitching, saree draping &amp; pico-fall made effortless.
            </h2>
            <p className="text-gn-text-secondary text-sm sm:text-base">
              No more repeated trips to the tailor shop. Book home measurement visits or send your best-fitting garment for replication.
            </p>
          </div>

          {/* 4-step interactive tailoring process */}
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 mb-10">
            {[
              { num: 1, title: "1. Select Garment", desc: "Saree pico-fall, blouse, kurti, hemming, or suit alteration." },
              { num: 2, title: "2. Measurement Mode", desc: "Master tailor home visit or provide a sample fitting garment." },
              { num: 3, title: "3. Doorstep Fabric Pickup", desc: "Our rider collects your material & sample in a sealed pouch." },
              { num: 4, title: "4. Delivered & Fitted", desc: "Crafted by master tailors and delivered back with trial guarantee." },
            ].map((step) => (
              <div
                key={step.num}
                onClick={() => setTailoringStep(step.num)}
                className={`p-5 rounded-gn-lg border cursor-pointer transition-all ${
                  tailoringStep === step.num
                    ? "bg-gn-bg-card border-gn-accent-primary shadow-gn-md ring-1 ring-gn-accent-primary/20"
                    : "bg-gn-bg-secondary/60 border-gn-border-default hover:bg-gn-bg-secondary"
                }`}
              >
                <div className="flex items-center gap-2 mb-2">
                  <span className={`h-6 w-6 rounded-full flex items-center justify-center text-xs font-bold ${
                    tailoringStep === step.num ? "bg-gn-accent-primary text-white" : "bg-gn-bg-tertiary text-gn-text-secondary"
                  }`}>
                    {step.num}
                  </span>
                  <h4 className="font-semibold text-sm text-gn-text-primary">{step.title}</h4>
                </div>
                <p className="text-xs text-gn-text-secondary leading-relaxed">{step.desc}</p>
              </div>
            ))}
          </div>

          {/* Interactive tailoring catalog items */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {FIXTURE_TAILORING_SERVICES.map((t) => (
              <Card key={t.id} hover className="bg-gn-bg-card">
                <CardHeader>
                  <div className="flex justify-between items-center">
                    <Badge variant="outline">{t.category.replace("_", " ")}</Badge>
                    <span className="text-xs font-semibold text-emerald-600">{t.estimatedHours}h Turnaround</span>
                  </div>
                  <CardTitle className="pt-2">{t.title}</CardTitle>
                  <CardDescription>{t.description}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-2 text-sm text-gn-text-secondary">
                  <p className="text-2xl font-bold font-serif text-gn-text-primary">
                    ₹{Math.round(t.pricePaise / 100)}
                  </p>
                  <ul className="space-y-1 text-xs text-gn-text-tertiary pt-1">
                    {t.inclusions.map((inc, i) => (
                      <li key={i}>• {inc}</li>
                    ))}
                  </ul>
                </CardContent>
                <CardFooter>
                  <Button
                    variant="primary"
                    size="sm"
                    className="w-full"
                    onClick={() => handleAddToCart(t.title)}
                  >
                    Book Service
                  </Button>
                </CardFooter>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* ─── Track & Safety Section ─── */}
      <section id="track" className="py-16 bg-gn-bg-secondary/50 border-t border-gn-border-default">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="p-8 rounded-gn-xl bg-gradient-to-r from-gn-text-primary to-gn-text-secondary text-white shadow-gn-xl">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
              <div className="lg:col-span-8 space-y-4">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 text-xs font-medium text-gn-accent-secondary">
                  <span>🔒 Production-Grade Trust &amp; Safety Architecture</span>
                </div>
                <h3 className="text-2xl sm:text-3xl font-bold font-serif text-white">
                  Live Dispatch Tracking &amp; Idempotent Safe Payments
                </h3>
                <p className="text-sm text-gn-text-muted leading-relaxed max-w-2xl">
                  Every booking snapshot is cryptographically versioned to prevent surprise price drift. Professionals are GPS-tracked with secure OTP verification before starting service.
                </p>
                <div className="flex flex-wrap gap-4 pt-2 text-xs text-gn-bg-primary">
                  <span>✓ UPI / Cards / NetBanking</span>
                  <span>✓ 100% Refund on unfulfilled bookings</span>
                  <span>✓ Dedicated SOS &amp; Support Escalation</span>
                </div>
              </div>
              <div className="lg:col-span-4 flex flex-col gap-3">
                <Input
                  type="text"
                  placeholder="Enter Order ID (e.g., ORD-8291)..."
                  className="bg-white/10 border-white/20 text-white placeholder:text-zinc-400"
                />
                <Button variant="primary" size="md" className="w-full">
                  Track Live Booking
                </Button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── Multi-Tier Comparison & Transparent Pricing Dialog ─── */}
      {tierModalService && (
        <Dialog
          open={Boolean(tierModalService)}
          onClose={() => setTierModalService(null)}
          title={`Configure & Compare: ${tierModalService.name}`}
          description="Transparent tier comparison with live server-side pricing breakdown, 18% GST, and locked quote guarantee."
          className="max-w-2xl"
        >
          <div className="space-y-5">
            {/* Tier Selector Tabs */}
            <div>
              <label className="block text-xs font-semibold text-gn-text-secondary uppercase tracking-wider mb-2">
                1. Select Experience Tier
              </label>
              <div className="grid grid-cols-3 gap-2">
                {(["basic", "standard", "premium"] as const).map((t) => {
                  const isSelected = activeTier === t;
                  return (
                    <button
                      key={t}
                      type="button"
                      onClick={() => {
                        setActiveTier(t);
                        computeQuoteForService(tierModalService, t, selectedAddOns, promoCodeInput);
                      }}
                      className={`p-3 rounded-gn-lg border text-left transition-all cursor-pointer ${
                        isSelected
                          ? "bg-gn-accent-primary-subtle/50 border-gn-accent-primary ring-1 ring-gn-accent-primary shadow-gn-sm"
                          : "bg-gn-bg-secondary/40 border-gn-border-default hover:bg-gn-bg-secondary"
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <Badge variant={t}>{t.toUpperCase()}</Badge>
                        {t === "standard" && (
                          <span className="text-[10px] text-amber-500 font-bold">★ POPULAR</span>
                        )}
                      </div>
                      <div className="font-serif font-bold text-sm text-gn-text-primary">
                        {t === "basic" ? "Essential" : t === "standard" ? "Signature" : "Royal"}
                      </div>
                      <div className="text-[11px] text-gn-text-tertiary">
                        {t === "basic" ? "~30 mins" : t === "standard" ? "~50 mins" : "~75 mins"}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Selected Tier Details & Inclusions */}
            <div className="p-3.5 rounded-gn-md border border-gn-border-default bg-gn-bg-secondary/30 space-y-2 text-xs">
              <div className="flex justify-between items-center">
                <span className="font-semibold text-gn-text-primary">
                  {activeTier === "basic" ? "Essential Care" : activeTier === "standard" ? "Signature Experience" : "Royal Indulgence"}
                </span>
                <span className="text-gn-text-muted">
                  Brands: {activeTier === "basic" ? "Streax & VLCC Professional" : activeTier === "standard" ? "O3+ & L'Oréal Professional" : "Kérastase Paris & Dermalogica"}
                </span>
              </div>
              <ul className="grid grid-cols-1 sm:grid-cols-2 gap-1 text-[11px] text-gn-text-secondary pt-1">
                <li className="flex items-center gap-1.5">
                  <span className="text-emerald-500 font-bold">✓</span>
                  <span>Sterile single-use sealed tool kit</span>
                </li>
                <li className="flex items-center gap-1.5">
                  <span className="text-emerald-500 font-bold">✓</span>
                  <span>{activeTier === "basic" ? "1+ yr certified specialist" : activeTier === "standard" ? "3+ yrs senior aesthetician" : "7+ yrs celebrity master artist"}</span>
                </li>
                <li className="flex items-center gap-1.5">
                  <span className="text-emerald-500 font-bold">✓</span>
                  <span>{activeTier === "basic" ? "Post-session cleanup" : activeTier === "standard" ? "10m head relaxer + cleanup" : "Aromatherapy + bespoke ritual"}</span>
                </li>
                <li className="flex items-center gap-1.5">
                  <span className="text-emerald-500 font-bold">✓</span>
                  <span>Disposables &amp; protective floor sheet</span>
                </li>
              </ul>
            </div>

            {/* 2. Optional Service Add-Ons */}
            <div>
              <label className="block text-xs font-semibold text-gn-text-secondary uppercase tracking-wider mb-2">
                2. Custom Add-Ons
              </label>
              <div className="space-y-2">
                {[
                  { id: "addon_detan", name: "Express Sara De-Tan Pack", price: 299, desc: "Botanical glow treatment (+15m)" },
                  { id: "addon_massage", name: "Aromatherapy Scalp Massage", price: 349, desc: "Relaxing warm oil massage (+15m)" },
                ].map((addon) => {
                  const isChecked = selectedAddOns.includes(addon.id);
                  return (
                    <label
                      key={addon.id}
                      className={`flex items-center justify-between p-2.5 rounded-gn-md border cursor-pointer text-xs transition-all ${
                        isChecked
                          ? "bg-gn-accent-primary-subtle/30 border-gn-accent-primary"
                          : "bg-gn-bg-card border-gn-border-default hover:bg-gn-bg-secondary"
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={(e) => {
                            const next = e.target.checked
                              ? [...selectedAddOns, addon.id]
                              : selectedAddOns.filter((id) => id !== addon.id);
                            setSelectedAddOns(next);
                            computeQuoteForService(tierModalService, activeTier, next, promoCodeInput);
                          }}
                          className="rounded text-gn-accent-primary"
                        />
                        <div>
                          <span className="font-semibold text-gn-text-primary">{addon.name}</span>
                          <span className="text-gn-text-tertiary ml-2 text-[11px]">{addon.desc}</span>
                        </div>
                      </div>
                      <span className="font-serif font-bold text-gn-text-primary">+₹{addon.price}</span>
                    </label>
                  );
                })}
              </div>
            </div>

            {/* 3. Promo Code Section */}
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="Promo Code (e.g. WELCOME50)"
                value={promoCodeInput}
                onChange={(e) => setPromoCodeInput(e.target.value.toUpperCase())}
                className="h-8 rounded-gn-md border border-gn-border-default bg-gn-bg-secondary px-3 text-xs text-gn-text-primary placeholder:text-gn-text-muted uppercase flex-1"
              />
              <Button
                variant="outline"
                size="sm"
                className="h-8 text-xs"
                onClick={() => computeQuoteForService(tierModalService, activeTier, selectedAddOns, promoCodeInput)}
              >
                Apply Code
              </Button>
            </div>

            {/* 4. Real-Time Transparent Quote Breakdown */}
            {calculatedQuote && (
              <div className="p-4 rounded-gn-lg border border-gn-accent-primary/20 bg-gn-bg-card shadow-gn-sm space-y-2 text-xs">
                <div className="flex items-center justify-between font-semibold text-gn-text-primary border-b border-gn-border-subtle pb-2">
                  <span>Transparent Price Quote (Live Server Engine)</span>
                  <Badge variant="primary">18% GST Compliant</Badge>
                </div>

                <div className="flex justify-between text-gn-text-secondary">
                  <span>Base Tier ({calculatedQuote.tier.toUpperCase()}):</span>
                  <span>₹{Math.round(calculatedQuote.base_price_paise / 100)}</span>
                </div>

                {calculatedQuote.add_ons && calculatedQuote.add_ons.length > 0 && (
                  <div className="flex justify-between text-gn-text-secondary">
                    <span>Add-ons ({calculatedQuote.add_ons.length}):</span>
                    <span>
                      +₹{Math.round(calculatedQuote.add_ons.reduce((acc, a) => acc + a.price_paise, 0) / 100)}
                    </span>
                  </div>
                )}

                {calculatedQuote.pickup_delivery_fee_paise > 0 && (
                  <div className="flex justify-between text-gn-text-secondary">
                    <span>Doorstep Tailoring Pickup &amp; Return:</span>
                    <span>+₹{Math.round(calculatedQuote.pickup_delivery_fee_paise / 100)}</span>
                  </div>
                )}

                {calculatedQuote.discount_paise > 0 && (
                  <div className="flex justify-between text-emerald-500 font-semibold">
                    <span>Discount Applied:</span>
                    <span>-₹{Math.round(calculatedQuote.discount_paise / 100)}</span>
                  </div>
                )}

                <div className="flex justify-between text-gn-text-muted text-[11px]">
                  <span>GST (9% CGST + 9% SGST):</span>
                  <span>
                    +₹{Math.round((calculatedQuote.tax_cgst_paise + calculatedQuote.tax_sgst_paise) / 100)}
                  </span>
                </div>

                <div className="pt-2 border-t border-gn-border-subtle flex justify-between items-center text-sm font-bold text-gn-text-primary">
                  <span>Total Amount Payable:</span>
                  <span className="font-serif text-lg text-gn-accent-primary">
                    ₹{Math.round(calculatedQuote.total_paise / 100)}
                  </span>
                </div>

                <div className="flex items-center justify-between pt-1 text-[10px] text-gn-text-muted">
                  <span>🔒 Locked Snapshot Valid for 15 minutes</span>
                  <span className="text-emerald-500 font-semibold">ADR-0003 Immutable Snapshot Ready</span>
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex justify-end gap-2 pt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setTierModalService(null)}
              >
                Close
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  const title = `${tierModalService.name} (${activeTier.toUpperCase()})`;
                  handleAddToCart(title);
                  setTierModalService(null);
                }}
              >
                Add to Bag
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={() => {
                  handleOpenBooking(tierModalService, activeTier);
                }}
              >
                ⚡ Instant Book &amp; Dispatch
              </Button>
            </div>
          </div>
        </Dialog>
      )}

      {/* ─── Customer Journey Booking Checkout Modal ─── */}
      <BookingModal
        isOpen={bookingModalOpen}
        onClose={() => setBookingModalOpen(false)}
        service={bookingModalService}
        initialTier={activeTier}
      />

      {/* ─── Mobile Cart / Service Bag BottomSheet ─── */}
      <BottomSheet
        open={mobileCartSheetOpen}
        onClose={() => setMobileCartSheetOpen(false)}
        title="Your Service Bag"
        description="Review items before scheduling or instant booking."
        footer={
          <div className="space-y-3">
            <div className="flex justify-between items-center text-sm font-semibold">
              <span>Estimated Total:</span>
              <span className="font-serif text-lg text-gn-accent-primary">₹1,298</span>
            </div>
            <Button
              variant="primary"
              size="lg"
              className="w-full"
              onClick={() => {
                const srv =
                  tierModalService ||
                  (serverServices?.[0] as ServiceSummaryDto) ||
                  (FIXTURE_SERVICES[0] as unknown as ServiceSummaryDto);
                handleOpenBooking(srv, "standard");
              }}
            >
              Proceed to Booking Checkout &amp; Hold
            </Button>
          </div>
        }
      >
        <div className="space-y-3">
          <div className="p-3 rounded-gn-md border border-gn-border-default flex justify-between items-center">
            <div>
              <p className="font-semibold text-sm">Glow Radiance Facial (O3+)</p>
              <p className="text-xs text-gn-text-tertiary">Standard Tier • 55 mins</p>
            </div>
            <span className="font-serif font-bold text-sm">₹999</span>
          </div>
          <div className="p-3 rounded-gn-md border border-gn-border-default flex justify-between items-center">
            <div>
              <p className="font-semibold text-sm">Pico-Fall &amp; Saree Rolling</p>
              <p className="text-xs text-gn-text-tertiary">Doorstep Pickup included</p>
            </div>
            <span className="font-serif font-bold text-sm">₹299</span>
          </div>
        </div>
      </BottomSheet>
    </div>
  );
}
