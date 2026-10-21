"use client";

import { useState } from "react";
import Link from "next/link";
import { Button } from "./button";

export interface NavItem {
  label: string;
  href: string;
  badge?: string;
}

export interface NavigationProps {
  items?: NavItem[];
}

const defaultNavItems: NavItem[] = [
  { label: "Salon for Women", href: "#services" },
  { label: "Men's Grooming", href: "#services" },
  { label: "Tailoring Studio", href: "#tailoring", badge: "POPULAR" },
  { label: "Verified Pros", href: "#professionals" },
  { label: "Catalog Engine", href: "/admin/catalog", badge: "ADMIN" },
];

export function Navigation({ items = defaultNavItems }: NavigationProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <>
      {/* Desktop Navigation Links */}
      <nav className="hidden lg:flex items-center gap-6 text-sm font-medium text-gn-text-secondary">
        {items.map((item) => (
          <Link
            key={item.href + item.label}
            href={item.href}
            className="hover:text-gn-accent-primary transition-colors flex items-center gap-1.5"
          >
            <span>{item.label}</span>
            {item.badge && (
              <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-gn-accent-secondary-subtle text-gn-accent-secondary-hover font-bold">
                {item.badge}
              </span>
            )}
          </Link>
        ))}
      </nav>

      {/* Mobile Hamburger Button */}
      <button
        onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
        className="lg:hidden p-2 rounded-gn-md text-gn-text-secondary hover:text-gn-text-primary hover:bg-gn-bg-secondary cursor-pointer gn-focus-ring"
        aria-label="Toggle navigation menu"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          {mobileMenuOpen ? (
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
          ) : (
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
          )}
        </svg>
      </button>

      {/* Mobile Drawer Menu */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 top-16 z-40 bg-gn-bg-card/95 backdrop-blur-md p-6 lg:hidden flex flex-col justify-between gn-fade-in border-b border-gn-border-default">
          <div className="space-y-4">
            <span className="text-xs uppercase tracking-wider font-semibold text-gn-text-tertiary">
              Menu
            </span>
            <div className="flex flex-col space-y-3">
              {items.map((item) => (
                <Link
                  key={item.label}
                  href={item.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className="text-lg font-medium text-gn-text-primary hover:text-gn-accent-primary flex items-center justify-between py-2 border-b border-gn-border-default/40"
                >
                  <span>{item.label}</span>
                  {item.badge && (
                    <span className="px-2 py-0.5 rounded-full text-xs bg-gn-accent-secondary-subtle text-gn-accent-secondary-hover font-bold">
                      {item.badge}
                    </span>
                  )}
                </Link>
              ))}
            </div>
          </div>

          <div className="pt-6 border-t border-gn-border-default space-y-3">
            <Button
              variant="primary"
              size="lg"
              className="w-full"
              onClick={() => setMobileMenuOpen(false)}
            >
              Book Service Now
            </Button>
          </div>
        </div>
      )}
    </>
  );
}
