"use client";

import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Rating } from "@/components/ui/rating";
import { Button } from "@/components/ui/button";

export interface ProfessionalDiscoveryCardProps {
  id: string;
  name: string;
  title: string;
  experienceYears: number;
  ratingScore: number;
  reviewCount: number;
  etaMinutes: number;
  specialties: string[];
  baseZoneName?: string;
  isVerified?: boolean;
  isInstantBooking?: boolean;
  tierPrices?: {
    basic: number;
    standard: number;
    premium: number;
  };
  portfolioSamples?: string[];
  isFallbackLocation?: boolean;
  fallbackMessage?: string;
  availableSlotsCount?: number;
}

export function ProfessionalDiscoveryCard({
  id,
  name,
  title,
  experienceYears,
  ratingScore,
  reviewCount,
  etaMinutes,
  specialties,
  baseZoneName = "Bengaluru Central",
  isVerified = true,
  isInstantBooking = true,
  tierPrices = { basic: 49900, standard: 99900, premium: 189900 },
  portfolioSamples = [
    "https://images.unsplash.com/photo-1560066984-138dadb4c035?w=200&auto=format&fit=crop&q=80",
    "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=200&auto=format&fit=crop&q=80",
    "https://images.unsplash.com/photo-1595476108010-b4d1f102b1b1?w=200&auto=format&fit=crop&q=80",
  ],
  isFallbackLocation = false,
  fallbackMessage,
  availableSlotsCount = 5,
}: ProfessionalDiscoveryCardProps) {
  const initials = name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .slice(0, 2);

  return (
    <div className="rounded-gn-lg border border-gn-border-default bg-gn-bg-card p-5 shadow-gn-sm hover:shadow-gn-md hover:border-gn-accent-primary/60 transition-all flex flex-col justify-between space-y-4">
      {/* Top Header: Avatar, Name, Verification, Zone */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="h-14 w-14 rounded-full bg-gradient-to-br from-gn-accent-primary to-gn-accent-secondary text-white font-serif font-bold text-lg flex items-center justify-center shrink-0 shadow-xs">
            {initials}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-gn-text-primary text-base sm:text-lg">
                {name}
              </h3>
              {isVerified && (
                <span
                  className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-[10px] font-bold"
                  title="Police & Skill Verified Professional"
                >
                  ✓ Verified
                </span>
              )}
            </div>
            <p className="text-xs text-gn-text-tertiary">{title}</p>
            <p className="text-[11px] text-gn-text-muted mt-0.5 flex items-center gap-1">
              📍 {baseZoneName} • {experienceYears}+ yrs experience
            </p>
          </div>
        </div>

        {/* Instant Booking Chip */}
        {isInstantBooking && (
          <span className="shrink-0 text-[10px] font-bold uppercase tracking-wider bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded-full flex items-center gap-1">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 gn-pulse" />
            Instant Book
          </span>
        )}
      </div>

      {/* Ratings & Arrival ETA Bar with Fallback Indicator */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 py-2 px-3 rounded-gn-sm bg-gn-bg-secondary text-xs">
        <Rating score={ratingScore} reviewCount={reviewCount} size="sm" />

        <div className="flex items-center gap-2">
          {isFallbackLocation ? (
            <span
              className="font-medium text-amber-700 bg-amber-100/70 px-2 py-0.5 rounded flex items-center gap-1 text-[11px]"
              title={fallbackMessage || "Live map unreachable; approximate regional ETA displayed"}
            >
              ⚠️ ~{etaMinutes}m ETA (Fallback)
            </span>
          ) : (
            <span className="font-semibold text-emerald-700 flex items-center gap-1">
              <span className="h-2 w-2 rounded-full bg-emerald-500 gn-pulse" />
              {etaMinutes}m Arrival Estimate
            </span>
          )}

          <span className="text-gn-text-muted">•</span>
          <span className="text-[11px] font-medium text-gn-text-secondary">
            {availableSlotsCount} slots today
          </span>
        </div>
      </div>

      {/* Transparent Service Tier Prices */}
      <div className="space-y-1.5">
        <span className="text-[10px] font-semibold uppercase tracking-wider text-gn-text-tertiary">
          Transparent Service Tier Rates
        </span>
        <div className="grid grid-cols-3 gap-2 text-center">
          <div className="bg-gn-bg-secondary/60 p-2 rounded-gn-sm border border-gn-border-default/60">
            <span className="text-[10px] uppercase font-semibold text-gn-text-muted block">Basic</span>
            <span className="text-xs sm:text-sm font-bold text-gn-text-primary">
              ₹{Math.round(tierPrices.basic / 100)}
            </span>
          </div>
          <div className="bg-gn-accent-primary-subtle/50 p-2 rounded-gn-sm border border-gn-accent-primary/40">
            <span className="text-[10px] uppercase font-bold text-gn-accent-primary block">Standard</span>
            <span className="text-xs sm:text-sm font-bold text-gn-text-primary">
              ₹{Math.round(tierPrices.standard / 100)}
            </span>
          </div>
          <div className="bg-gn-accent-secondary-subtle/50 p-2 rounded-gn-sm border border-gn-accent-secondary/40">
            <span className="text-[10px] uppercase font-bold text-gn-accent-secondary block">Premium</span>
            <span className="text-xs sm:text-sm font-bold text-gn-text-primary">
              ₹{Math.round(tierPrices.premium / 100)}
            </span>
          </div>
        </div>
      </div>

      {/* Specialties Tags */}
      <div className="flex flex-wrap gap-1">
        {specialties.map((s) => (
          <Badge key={s} variant="outline" className="text-[10px] py-0 px-2 font-normal">
            {s}
          </Badge>
        ))}
      </div>

      {/* Portfolio Samples Preview */}
      {portfolioSamples && portfolioSamples.length > 0 && (
        <div className="space-y-1">
          <span className="text-[10px] font-semibold text-gn-text-tertiary block">
            Verified Portfolio Looks:
          </span>
          <div className="flex items-center gap-2">
            {portfolioSamples.slice(0, 3).map((img, i) => (
              <div
                key={i}
                className="h-12 w-12 rounded-gn-sm overflow-hidden bg-gn-bg-secondary border border-gn-border-default shrink-0"
              >
                <img
                  src={img}
                  alt={`Portfolio ${i}`}
                  className="h-full w-full object-cover"
                  loading="lazy"
                />
              </div>
            ))}
            <span className="text-[11px] text-gn-text-tertiary pl-1">+more looks</span>
          </div>
        </div>
      )}

      {/* Footer Action */}
      <div className="pt-3 border-t border-gn-border-default/80 flex items-center justify-between">
        <span className="text-xs text-gn-text-tertiary">
          No advance fees
        </span>
        <Link href={`/professionals/${id}`}>
          <Button variant="primary" size="sm" className="text-xs">
            View Profile &amp; Book Slots →
          </Button>
        </Link>
      </div>
    </div>
  );
}
