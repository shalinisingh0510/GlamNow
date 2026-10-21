"use client";

import Link from "next/link";
import { useState } from "react";
import { Button } from "./ui/button";
import { Dialog } from "./ui/dialog";
import { Navigation } from "./ui/navigation";
import { FIXTURE_SERVICEABLE_ZONES } from "@/lib/fixtures";

export function Header() {
  const [selectedZone, setSelectedZone] = useState(FIXTURE_SERVICEABLE_ZONES[0]);
  const [locationDialogOpen, setLocationDialogOpen] = useState(false);
  const [customPincode, setCustomPincode] = useState("");
  const [pincodeError, setPincodeError] = useState<string | null>(null);

  const handleSelectZone = (zone: typeof FIXTURE_SERVICEABLE_ZONES[0]) => {
    setSelectedZone(zone);
    setLocationDialogOpen(false);
    setPincodeError(null);
  };

  const handleCustomPincodeSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const found = FIXTURE_SERVICEABLE_ZONES.find((z) => z.pincode === customPincode.trim());
    if (found) {
      setSelectedZone(found);
      setLocationDialogOpen(false);
      setPincodeError(null);
      setCustomPincode("");
    } else {
      setPincodeError(`Zone for PIN ${customPincode} is coming soon. Please choose an active Bengaluru sector.`);
    }
  };

  return (
    <>
      <header className="sticky top-0 z-40 w-full border-b border-gn-border-default bg-gn-bg-card/95 backdrop-blur-md">
        {/* Top Banner: Quick Commerce Promise */}
        <div className="bg-gn-text-primary text-gn-bg-primary px-4 py-1.5 text-xs font-medium text-center flex items-center justify-center gap-2">
          <span className="inline-block h-2 w-2 rounded-full bg-emerald-400 gn-pulse" />
          <span>⚡ Quick At-Home Services: Stylists &amp; Specialists arriving in <strong>15–30 mins</strong></span>
          <span className="hidden sm:inline text-gn-text-muted">•</span>
          <span className="hidden sm:inline text-gn-accent-secondary">Doorstep Tailoring with Free Measurement Pickup</span>
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16 sm:h-20 gap-4">
            {/* Brand Logo */}
            <Link href="/" className="flex items-center gap-2.5 shrink-0">
              <div className="h-10 w-10 rounded-gn-md bg-gradient-to-tr from-gn-accent-primary to-gn-accent-secondary flex items-center justify-center shadow-gn-sm">
                <span className="text-white font-serif text-2xl font-bold tracking-tight">G</span>
              </div>
              <div>
                <span className="text-2xl font-bold tracking-tight text-gn-text-primary font-serif">
                  Glam<span className="text-gn-accent-primary">Now</span>
                </span>
                <p className="text-[10px] tracking-wider uppercase text-gn-text-tertiary font-semibold -mt-1">
                  At-Home Services &amp; Tailoring
                </p>
              </div>
            </Link>

            {/* Location Pincode Selector Chip */}
            <button
              onClick={() => setLocationDialogOpen(true)}
              className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-gn-full bg-gn-bg-secondary border border-gn-border-default text-xs text-gn-text-secondary hover:border-gn-border-strong cursor-pointer transition-all gn-focus-ring"
            >
              <svg className="w-4 h-4 text-gn-accent-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <span className="font-semibold text-gn-text-primary">{selectedZone.area}</span>
              <span className="text-gn-text-muted">({selectedZone.pincode})</span>
              <span className="text-gn-accent-primary font-medium ml-1">Change ▾</span>
            </button>

            {/* Navigation Links Component */}
            <Navigation />

            {/* Action CTAs */}
            <div className="flex items-center gap-2 sm:gap-3">
              <Link href="#cart">
                <Button variant="ghost" size="sm" className="relative">
                  <svg className="w-5 h-5 text-gn-text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
                  </svg>
                  <span className="hidden sm:inline ml-1 font-medium text-xs">Bag</span>
                  <span className="absolute -top-1 -right-1 h-4 w-4 rounded-full bg-gn-accent-primary text-white text-[10px] flex items-center justify-center font-bold">
                    2
                  </span>
                </Button>
              </Link>
              <Button variant="primary" size="sm" className="hidden sm:inline-flex">
                Book Service
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Change Location / PIN Code Dialog */}
      <Dialog
        open={locationDialogOpen}
        onClose={() => setLocationDialogOpen(false)}
        title="Select Service Location"
        description="Choose your area to check available nearby stylists, master tailors, and live arrival times."
      >
        <div className="space-y-4">
          <form onSubmit={handleCustomPincodeSubmit} className="flex gap-2">
            <input
              type="text"
              placeholder="Enter 6-digit PIN code..."
              value={customPincode}
              onChange={(e) => setCustomPincode(e.target.value)}
              maxLength={6}
              className="flex h-10 w-full rounded-gn-md border border-gn-border-default bg-gn-bg-card px-3 text-sm text-gn-text-primary placeholder:text-gn-text-muted gn-focus-ring"
            />
            <Button type="submit" variant="primary" size="sm">
              Verify
            </Button>
          </form>

          {pincodeError && (
            <p className="text-xs text-gn-error">{pincodeError}</p>
          )}

          <div className="pt-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-gn-text-tertiary block mb-2">
              Active Express Delivery Sectors
            </span>
            <div className="space-y-2">
              {FIXTURE_SERVICEABLE_ZONES.map((zone) => (
                <div
                  key={zone.pincode}
                  onClick={() => handleSelectZone(zone)}
                  className={`
                    p-3 rounded-gn-md border cursor-pointer transition-all flex items-center justify-between
                    ${selectedZone.pincode === zone.pincode
                      ? "bg-gn-accent-primary-subtle/50 border-gn-accent-primary text-gn-text-primary font-medium"
                      : "bg-gn-bg-secondary/60 border-gn-border-default hover:bg-gn-bg-secondary text-gn-text-secondary"
                    }
                  `}
                >
                  <div>
                    <p className="text-sm font-semibold text-gn-text-primary">{zone.area}</p>
                    <p className="text-xs text-gn-text-tertiary">PIN {zone.pincode} • {zone.activePros} Pros online</p>
                  </div>
                  <span className="text-xs font-bold text-emerald-700">
                    {zone.etaMin}–{zone.etaMax}m ETA
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </Dialog>
    </>
  );
}
