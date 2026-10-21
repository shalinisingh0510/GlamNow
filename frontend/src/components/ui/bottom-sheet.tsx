"use client";

import { useEffect, type ReactNode } from "react";

export interface BottomSheetProps {
  open: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children: ReactNode;
  footer?: ReactNode;
}

export function BottomSheet({
  open,
  onClose,
  title,
  description,
  children,
  footer,
}: BottomSheetProps) {
  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && open) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open, onClose]);

  // Lock body scroll
  useEffect(() => {
    if (open) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center md:hidden"
      role="dialog"
      aria-modal="true"
      aria-labelledby="sheet-title"
    >
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-gn-text-primary/60 backdrop-blur-xs transition-opacity gn-fade-in"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Sheet Content */}
      <div className="relative w-full max-h-[85vh] rounded-t-gn-xl bg-gn-bg-card p-6 shadow-gn-xl border-t border-gn-border-default z-10 gn-slide-up flex flex-col">
        {/* Drag handle pill */}
        <div className="mx-auto mb-4 h-1.5 w-12 rounded-full bg-gn-border-strong cursor-grab" />

        {/* Header */}
        <div className="flex items-start justify-between pb-3 border-b border-gn-border-default">
          <div>
            <h3 id="sheet-title" className="text-lg font-bold font-serif text-gn-text-primary">
              {title}
            </h3>
            {description && (
              <p className="text-xs text-gn-text-secondary mt-0.5">{description}</p>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-gn-text-tertiary hover:text-gn-text-primary p-1 rounded-gn-sm hover:bg-gn-bg-secondary cursor-pointer gn-focus-ring"
            aria-label="Close sheet"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="py-4 overflow-y-auto flex-1">{children}</div>

        {/* Footer */}
        {footer && <div className="pt-3 border-t border-gn-border-default">{footer}</div>}
      </div>
    </div>
  );
}
