"use client";

import { useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";

// Sample verified professionals data
const FEATURED_PROS = [
  {
    id: "pro_1",
    name: "Priya Sharma",
    title: "Master Aesthetician & Hair Stylist",
    rating: 4.94,
    reviewsCount: 382,
    experience: "7+ years exp",
    etaMinutes: 18,
    specialties: ["Hydra Facial", "Bridal Hair", "Keratin Spa"],
    startingPrice: 599,
    tier: "premium" as const,
    avatar: "PS",
    verified: true,
  },
  {
    id: "pro_2",
    name: "Ramesh Kumar",
    title: "Men's Master Barber & Grooming Specialist",
    rating: 4.88,
    reviewsCount: 512,
    experience: "9+ years exp",
    etaMinutes: 24,
    specialties: ["Fade Cuts", "Beard Sculpting", "Charcoal Detan"],
    startingPrice: 349,
    tier: "standard" as const,
    avatar: "RK",
    verified: true,
  },
  {
    id: "pro_3",
    name: "Ananya Deshmukh",
    title: "Master Tailor & Draping Artisan",
    rating: 4.97,
    reviewsCount: 240,
    experience: "12+ years exp",
    etaMinutes: 30,
    specialties: ["Saree Draping", "Designer Blouses", "Pico-Fall"],
    startingPrice: 299,
    tier: "premium" as const,
    avatar: "AD",
    verified: true,
  },
];

// Service categories
const CATEGORIES = [
  { id: "beauty", name: "Salon for Women", count: "32 Services", icon: "✨" },
  { id: "grooming", name: "Men's Grooming", count: "18 Services", icon: "✂️" },
  { id: "tailoring", name: "Tailoring & Alterations", count: "14 Services", icon: "🧵", badge: "Express Delivery" },
  { id: "massage", name: "Spa & Body Massage", count: "12 Services", icon: "🌿" },
  { id: "saree", name: "Saree Draping & Ironing", count: "6 Services", icon: "🥻" },
];

export default function HomePage() {
  const [selectedCategory, setSelectedCategory] = useState("beauty");
  const [selectedTier, setSelectedTier] = useState<"all" | "basic" | "standard" | "premium">("all");
  const [pincodeInput, setPincodeInput] = useState("560038");
  const [serviceableStatus, setServiceableStatus] = useState<string | null>("Available • Express 15–30 min service active");
  const [selectedProId, setSelectedProId] = useState<string | null>("pro_1");
  const [tailoringStep, setTailoringStep] = useState(1);

  const handleCheckServiceability = (e: React.FormEvent) => {
    e.preventDefault();
    if (pincodeInput.length === 6) {
      setServiceableStatus(`Verified: Zone 4 (${pincodeInput}) has 14 professionals available right now.`);
    } else {
      setServiceableStatus("Please enter a valid 6-digit Indian PIN code.");
    }
  };

  return (
    <div className="flex flex-col min-h-screen">
      {/* ─── Hero Section ─── */}
      <section className="relative overflow-hidden bg-gradient-to-b from-gn-bg-secondary via-gn-bg-primary to-gn-bg-primary pt-12 pb-20 border-b border-gn-border-default">
        {/* Subtle decorative circles */}
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

              {serviceableStatus && (
                <p className="text-xs text-gn-success font-medium flex items-center justify-center lg:justify-start gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-emerald-500 inline-block" />
                  {serviceableStatus}
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

            {/* Right Column: Dynamic Preview Card */}
            <div className="lg:col-span-5">
              <Card className="p-6 bg-gn-bg-card border-gn-border-strong shadow-gn-lg relative overflow-hidden">
                <div className="flex items-center justify-between pb-4 border-b border-gn-border-default">
                  <div className="flex items-center gap-2">
                    <span className="h-3 w-3 rounded-full bg-emerald-500 gn-pulse" />
                    <span className="text-xs font-bold uppercase tracking-wider text-gn-text-secondary">
                      Active Live Matching
                    </span>
                  </div>
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
      <section className="bg-gn-bg-card border-b border-gn-border-default py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3 overflow-x-auto pb-2 scrollbar-none">
            {CATEGORIES.map((cat) => (
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

      {/* ─── Service Tier Comparison (Basic, Standard, Premium) ─── */}
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
                  onClick={() => setSelectedTier(t)}
                  className={`px-4 py-1.5 text-xs font-semibold rounded-gn-md capitalize transition-all cursor-pointer ${
                    selectedTier === t
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
            {/* Basic Tier Card */}
            {(selectedTier === "all" || selectedTier === "basic") && (
              <Card hover className="flex flex-col border-gn-border-default">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <Badge variant="basic">Basic Tier</Badge>
                    <span className="text-xs text-gn-text-muted">Swift &amp; Essential</span>
                  </div>
                  <CardTitle className="pt-2">Essential Care</CardTitle>
                  <CardDescription>
                    Ideal for routine grooming, quick touch-ups, and budget-friendly speed.
                  </CardDescription>
                </CardHeader>
                <CardContent className="flex-1 space-y-4">
                  <div className="flex items-baseline gap-1">
                    <span className="text-3xl font-bold font-serif text-gn-text-primary">₹399</span>
                    <span className="text-xs text-gn-text-tertiary">/ starting price</span>
                  </div>
                  <ul className="space-y-2 text-xs sm:text-sm text-gn-text-secondary">
                    <li className="flex items-center gap-2">✓ Standard branded consumables</li>
                    <li className="flex items-center gap-2">✓ Sanitized single-use tool pouch</li>
                    <li className="flex items-center gap-2">✓ Verified professional (1+ yr exp)</li>
                    <li className="flex items-center gap-2">✓ 20–30 min average duration</li>
                  </ul>
                </CardContent>
                <CardFooter>
                  <Button variant="ghost" className="w-full border border-gn-border-default hover:bg-gn-bg-secondary">
                    Select Basic Tier
                  </Button>
                </CardFooter>
              </Card>
            )}

            {/* Standard Tier Card */}
            {(selectedTier === "all" || selectedTier === "standard") && (
              <Card hover className="flex flex-col border-gn-accent-primary relative shadow-gn-md bg-gn-bg-card ring-1 ring-gn-accent-primary/20">
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <span className="bg-gn-accent-primary text-white text-[11px] font-bold px-3 py-1 rounded-full uppercase tracking-wider shadow-xs">
                    Most Popular
                  </span>
                </div>
                <CardHeader className="pt-8">
                  <div className="flex items-center justify-between">
                    <Badge variant="standard">Standard Tier</Badge>
                    <span className="text-xs text-amber-700 font-semibold">Recommended</span>
                  </div>
                  <CardTitle className="pt-2">Signature Experience</CardTitle>
                  <CardDescription>
                    Premium branded formulations, shoulder massage relaxer, and senior specialists.
                  </CardDescription>
                </CardHeader>
                <CardContent className="flex-1 space-y-4">
                  <div className="flex items-baseline gap-1">
                    <span className="text-3xl font-bold font-serif text-gn-text-primary">₹799</span>
                    <span className="text-xs text-gn-text-tertiary">/ starting price</span>
                  </div>
                  <ul className="space-y-2 text-xs sm:text-sm text-gn-text-secondary">
                    <li className="flex items-center gap-2">✓ Top-tier professional brands (O3+, Cheryl&apos;s)</li>
                    <li className="flex items-center gap-2">✓ 10-minute complimentary head &amp; shoulder relaxer</li>
                    <li className="flex items-center gap-2">✓ Senior aesthetician (3+ yrs exp, 4.8+ rating)</li>
                    <li className="flex items-center gap-2">✓ Complete disposable cleanup sheet</li>
                  </ul>
                </CardContent>
                <CardFooter>
                  <Button variant="primary" className="w-full">
                    Select Standard Tier
                  </Button>
                </CardFooter>
              </Card>
            )}

            {/* Premium Tier Card */}
            {(selectedTier === "all" || selectedTier === "premium") && (
              <Card hover className="flex flex-col border-purple-300 bg-gradient-to-b from-purple-50/50 to-gn-bg-card">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <Badge variant="premium">Premium Tier</Badge>
                    <span className="text-xs text-purple-900 font-semibold">Luxury Salon</span>
                  </div>
                  <CardTitle className="pt-2">Royal Indulgence</CardTitle>
                  <CardDescription>
                    Imported dermatological products, master stylists, aromatherapy &amp; full relaxation ritual.
                  </CardDescription>
                </CardHeader>
                <CardContent className="flex-1 space-y-4">
                  <div className="flex items-baseline gap-1">
                    <span className="text-3xl font-bold font-serif text-gn-text-primary">₹1,499</span>
                    <span className="text-xs text-gn-text-tertiary">/ starting price</span>
                  </div>
                  <ul className="space-y-2 text-xs sm:text-sm text-gn-text-secondary">
                    <li className="flex items-center gap-2">✓ Luxury salon imports (Kérastase, Dermalogica)</li>
                    <li className="flex items-center gap-2">✓ Master artist (7+ yrs exp, celebrity portfolio)</li>
                    <li className="flex items-center gap-2">✓ Essential oils &amp; sensory ambient setup</li>
                    <li className="flex items-center gap-2">✓ Unhurried, dedicated bespoke session</li>
                  </ul>
                </CardContent>
                <CardFooter>
                  <Button variant="secondary" className="w-full">
                    Select Premium Tier
                  </Button>
                </CardFooter>
              </Card>
            )}
          </div>
        </div>
      </section>

      {/* ─── Choose a Specific Professional ─── */}
      <section id="professionals" className="py-16 bg-gn-bg-secondary/40 border-y border-gn-border-default">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-start md:items-end justify-between mb-10 gap-4">
            <div>
              <Badge variant="primary" className="mb-2">Choose Your Professional</Badge>
              <h2 className="text-3xl font-bold font-serif text-gn-text-primary">
                Select by rating, portfolio &amp; live arrival estimate.
              </h2>
              <p className="text-sm text-gn-text-secondary mt-1 max-w-xl">
                Compare verified professionals nearby. View their authentic customer ratings, completed orders count, and immediate dispatch readiness.
              </p>
            </div>
            <Link href="#all-pros" className="text-xs font-semibold text-gn-accent-primary hover:underline shrink-0">
              View All 42 Pros in Bengaluru →
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {FEATURED_PROS.map((pro) => (
              <Card
                key={pro.id}
                hover
                onClick={() => setSelectedProId(pro.id)}
                className={`cursor-pointer transition-all ${
                  selectedProId === pro.id ? "ring-2 ring-gn-accent-primary shadow-gn-md border-transparent" : ""
                }`}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="h-12 w-12 rounded-full bg-gn-accent-primary-subtle text-gn-accent-primary font-serif font-bold text-lg flex items-center justify-center">
                        {pro.avatar}
                      </div>
                      <div>
                        <div className="flex items-center gap-1.5">
                          <h4 className="font-semibold text-gn-text-primary text-base">{pro.name}</h4>
                          {pro.verified && (
                            <span className="text-gn-accent-primary text-xs" title="Verified Professional">
                              ✓
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-gn-text-tertiary">{pro.title}</p>
                      </div>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3 pb-4">
                  <div className="flex items-center justify-between text-xs py-2 px-3 rounded-gn-sm bg-gn-bg-secondary">
                    <span className="font-bold text-amber-700">★ {pro.rating} ({pro.reviewsCount})</span>
                    <span className="text-gn-text-secondary">{pro.experience}</span>
                    <span className="font-semibold text-emerald-700">⚡ {pro.etaMinutes} mins ETA</span>
                  </div>

                  <div className="flex flex-wrap gap-1.5">
                    {pro.specialties.map((s) => (
                      <span key={s} className="text-[11px] px-2 py-0.5 rounded-full bg-gn-bg-tertiary/70 text-gn-text-secondary font-medium">
                        {s}
                      </span>
                    ))}
                  </div>
                </CardContent>
                <CardFooter className="pt-2 border-t border-gn-border-default/60 flex items-center justify-between">
                  <div>
                    <span className="text-[10px] text-gn-text-tertiary uppercase tracking-wide block">Starting at</span>
                    <span className="text-base font-bold text-gn-text-primary font-serif">₹{pro.startingPrice}</span>
                  </div>
                  <Button
                    variant={selectedProId === pro.id ? "primary" : "ghost"}
                    size="sm"
                    className={selectedProId === pro.id ? "" : "border border-gn-border-default"}
                  >
                    {selectedProId === pro.id ? "Selected ✓" : "Select Pro"}
                  </Button>
                </CardFooter>
              </Card>
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
              { num: 3, title: "3. Doorstep Fabric Pickup", desc: "Our rider collects your material &amp; sample in a sealed pouch." },
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

          {/* Interactive tailoring catalog sample */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card hover className="bg-gn-bg-card">
              <CardHeader>
                <div className="flex justify-between items-center">
                  <Badge variant="outline">Saree Care</Badge>
                  <span className="text-xs font-semibold text-emerald-600">24-48h Delivery</span>
                </div>
                <CardTitle className="pt-2">Pico-Fall &amp; Saree Rolling</CardTitle>
                <CardDescription>
                  Premium cotton fall stitching with interlocking pico border and steam press.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-2 text-sm text-gn-text-secondary">
                <p className="text-2xl font-bold font-serif text-gn-text-primary">₹299</p>
                <p className="text-xs text-gn-text-tertiary">• Doorstep fabric pickup &amp; return included</p>
                <p className="text-xs text-gn-text-tertiary">• Color-matched fall and high-tensile thread</p>
              </CardContent>
              <CardFooter>
                <Button variant="primary" size="sm" className="w-full">
                  Book Pico-Fall Service
                </Button>
              </CardFooter>
            </Card>

            <Card hover className="bg-gn-bg-card">
              <CardHeader>
                <div className="flex justify-between items-center">
                  <Badge variant="outline">Bespoke Stitching</Badge>
                  <span className="text-xs font-semibold text-gn-accent-primary">Master Tailor</span>
                </div>
                <CardTitle className="pt-2">Designer Blouse Stitching</CardTitle>
                <CardDescription>
                  Padded / non-padded blouse with custom neckline, latkan detailing &amp; perfect darts.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-2 text-sm text-gn-text-secondary">
                <p className="text-2xl font-bold font-serif text-gn-text-primary">₹699</p>
                <p className="text-xs text-gn-text-tertiary">• Home measurement visit or sample garment pickup</p>
                <p className="text-xs text-gn-text-tertiary">• Free trial &amp; alteration adjustment guarantee</p>
              </CardContent>
              <CardFooter>
                <Button variant="primary" size="sm" className="w-full">
                  Schedule Stitching
                </Button>
              </CardFooter>
            </Card>

            <Card hover className="bg-gn-bg-card">
              <CardHeader>
                <div className="flex justify-between items-center">
                  <Badge variant="outline">Alterations</Badge>
                  <span className="text-xs font-semibold text-amber-700">Express Alter</span>
                </div>
                <CardTitle className="pt-2">Trouser, Kurti &amp; Suit Alteration</CardTitle>
                <CardDescription>
                  Waist adjustment, length shortening, taper fit, sleeve reduction &amp; zip repair.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-2 text-sm text-gn-text-secondary">
                <p className="text-2xl font-bold font-serif text-gn-text-primary">₹199</p>
                <p className="text-xs text-gn-text-tertiary">• Doorstep pin-up measurement by tailor</p>
                <p className="text-xs text-gn-text-tertiary">• Finished within 48 hours</p>
              </CardContent>
              <CardFooter>
                <Button variant="primary" size="sm" className="w-full">
                  Book Alteration
                </Button>
              </CardFooter>
            </Card>
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
    </div>
  );
}
