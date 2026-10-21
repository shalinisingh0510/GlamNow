"use client";

import Link from "next/link";
import { useState } from "react";
import { Button } from "./ui/button";

export function Header() {
  const [pincode] = useState("560038");
  const [area] = useState("Indiranagar, Bengaluru");
  const [isChangingLocation, setIsChangingLocation] = useState(false);

  return (
    <header className="sticky top-0 z-40 w-full border-b border-gn-border-default bg-gn-bg-card/95 backdrop-blur-md">
      {/* Top Banner: Quick Commerce Promise */}
      <div className="bg-gn-text-primary text-gn-bg-primary px-4 py-1.5 text-xs font-medium text-center flex items-center justify-center gap-2">
        <span className="inline-block h-2 w-2 rounded-full bg-emerald-400 gn-pulse" />
        <span>⚡ Quick At-Home Services: Stylists & Specialists arriving in <strong>15–30 mins</strong> in eligible zones</span>
        <span className="hidden sm:inline text-gn-text-muted">•</span>
        <span className="hidden sm:inline text-gn-accent-secondary">Doorstep Tailoring & Alterations with Free Measurement Pickup</span>
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
                At-Home Services & Tailoring
              </p>
            </div>
          </Link>

          {/* Location Pincode Selector */}
          <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-gn-full bg-gn-bg-secondary border border-gn-border-default text-xs text-gn-text-secondary">
            <svg className="w-4 h-4 text-gn-accent-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <span className="font-semibold text-gn-text-primary">{area}</span>
            <span className="text-gn-text-muted">({pincode})</span>
            <button
              onClick={() => setIsChangingLocation(!isChangingLocation)}
              className="text-gn-accent-primary hover:underline font-medium ml-1 cursor-pointer"
            >
              Change
            </button>
          </div>

          {/* Navigation Links */}
          <nav className="hidden lg:flex items-center gap-6 text-sm font-medium text-gn-text-secondary">
            <Link href="#services" className="hover:text-gn-accent-primary transition-colors">
              Beauty & Grooming
            </Link>
            <Link href="#tailoring" className="hover:text-gn-accent-primary transition-colors flex items-center gap-1.5">
              <span>Tailoring Studio</span>
              <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-gn-accent-secondary-subtle text-gn-accent-secondary-hover font-bold">
                POPULAR
              </span>
            </Link>
            <Link href="#professionals" className="hover:text-gn-accent-primary transition-colors">
              Verified Pros
            </Link>
            <Link href="#track" className="hover:text-gn-accent-primary transition-colors">
              Track Order
            </Link>
          </nav>

          {/* Action CTAs */}
          <div className="flex items-center gap-3">
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
  );
}
