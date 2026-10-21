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
  type ServiceItemFixture,
} from "@/lib/fixtures";

export default function HomePage() {
  const [selectedCategory, setSelectedCategory] = useState("beauty");
  const [selectedTierFilter, setSelectedTierFilter] = useState<"all" | "basic" | "standard" | "premium">("all");
  const [pincodeInput, setPincodeInput] = useState("560038");
  const [serviceableNotice, setServiceableNotice] = useState<string | null>(
    "Verified: Indiranagar Zone (560038) has 14 professionals available for 15–25 min dispatch."
  );
  const [selectedProId, setSelectedProId] = useState<string | null>("pro_1");
  const [tailoringStep, setTailoringStep] = useState(1);

  // Modal and Sheet states for testing interactions
  const [tierModalService, setTierModalService] = useState<ServiceItemFixture | null>(null);
  const [mobileCartSheetOpen, setMobileCartSheetOpen] = useState(false);
  const [cartCount, setCartCount] = useState(2);
  const [bagNotice, setBagNotice] = useState<string | null>(null);

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

  // Filter services by category
  const activeServices = FIXTURE_SERVICES.filter(
    (s) => s.categoryId === selectedCategory || selectedCategory === "all"
  );

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
      <section className="bg-gn-bg-card border-b border-gn-border-default py-6 sticky top-16 sm:top-20 z-30 shadow-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3 overflow-x-auto pb-2 scrollbar-none">
            {FIXTURE_CATEGORIES.map((cat) => (
              <button
                key={cat.id}
                onClick={() => setSelectedCategory(cat.id)}
                className={`
                  flex items-center gap-2.5 px-4 py-2.5 rounded-gn-lg border text-sm font-medium whitespace-nowrap cursor-pointer transition-all
                  ${selectedCategory === cat.id
                    ? "bg-gn-accent-primary text-white border-gn-accent-primary shadow-gn-sm"
                    : "bg-gn-bg-card text-gn-text-secondary border-gn-border-default hover:border-gn-border-strong hover:bg-gn-bg-secondary"
                  }
                `}
              >
                <span className="text-base">{cat.icon}</span>
                <span>{cat.name}</span>
                {cat.badge && (
                  <span className={`text-[10px] px-1.5 py-0.2 rounded-full font-bold ${
                    selectedCategory === cat.id ? "bg-white text-gn-accent-primary" : "bg-gn-accent-secondary-subtle text-gn-accent-secondary-hover"
                  }`}>
                    {cat.badge}
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* ─── Service Catalog Grid with ServiceCard Component ─── */}
      <section className="py-14 bg-gn-bg-secondary/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h3 className="text-2xl font-bold font-serif text-gn-text-primary">Featured Services</h3>
              <p className="text-xs sm:text-sm text-gn-text-secondary mt-0.5">
                Every service offers tiered formulations and sanitized single-use kits.
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
                  category={service.categoryName}
                  name={service.name}
                  description={service.description}
                  durationMinutes={service.durationMinutes}
                  startingPricePaise={service.startingPricePaise}
                  icon={service.icon}
                  onSelectTier={() => setTierModalService(service)}
                  onQuickBook={() => handleAddToCart(service.name)}
                />
              ))}
            </div>
          ) : (
            <EmptyState
              title="No services found in this category"
              description="We are constantly expanding our service catalog in your location."
              actionLabel="Reset Category Filter"
              onAction={() => setSelectedCategory("beauty")}
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

      {/* ─── Tier Detail Dialog (Triggered from ServiceCard) ─── */}
      {tierModalService && (
        <Dialog
          open={Boolean(tierModalService)}
          onClose={() => setTierModalService(null)}
          title={`Tier Options for ${tierModalService.name}`}
          description="Compare product formulations, duration, and inclusions."
          className="max-w-2xl"
        >
          <div className="space-y-4">
            {tierModalService.tiers.map((t) => (
              <div
                key={t.tier}
                className="p-4 rounded-gn-lg border border-gn-border-default bg-gn-bg-secondary/40 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <Badge variant={t.tier}>{t.tier.toUpperCase()}</Badge>
                    <h4 className="font-bold text-sm text-gn-text-primary">{t.title}</h4>
                    <span className="text-xs text-gn-text-tertiary">~{t.durationMinutes}m</span>
                  </div>
                  <p className="text-xs text-gn-text-secondary mt-1">{t.description}</p>
                  <p className="text-[11px] text-gn-text-muted mt-1 font-medium">Brands: {t.brands}</p>
                </div>
                <div className="shrink-0 flex items-center gap-3">
                  <span className="font-serif font-bold text-lg text-gn-text-primary">
                    ₹{Math.round(t.pricePaise / 100)}
                  </span>
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => {
                      handleAddToCart(`${tierModalService.name} (${t.title})`);
                      setTierModalService(null);
                    }}
                  >
                    Select
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </Dialog>
      )}

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
                alert("Proceeding to checkout with idempotent hold.");
                setMobileCartSheetOpen(false);
              }}
            >
              Proceed to Booking Hold
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
