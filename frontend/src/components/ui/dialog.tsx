"use client";

import { useEffect, useRef, type ReactNode } from "react";

export interface DialogProps {
  open: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children: ReactNode;
  footer?: ReactNode;
  className?: string;
}

export function Dialog({
  open,
  onClose,
  title,
  description,
  children,
  footer,
  className = "",
}: DialogProps) {
  const dialogRef = useRef<HTMLDivElement>(null);

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

  // Lock body scroll when dialog is open
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
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 overflow-y-auto"
      role="dialog"
      aria-modal="true"
      aria-labelledby="dialog-title"
      aria-describedby={description ? "dialog-desc" : undefined}
    >
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-gn-text-primary/60 backdrop-blur-xs transition-opacity gn-fade-in"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Dialog Window */}
      <div
        ref={dialogRef}
        className={`
          relative w-full max-w-lg rounded-gn-xl bg-gn-bg-card p-6 shadow-gn-xl border border-gn-border-default
          z-10 gn-scale-in text-gn-text-primary
          ${className}
        `}
      >
        {/* Header */}
        <div className="flex items-start justify-between pb-4 border-b border-gn-border-default">
          <div>
            <h2 id="dialog-title" className="text-xl font-bold font-serif text-gn-text-primary">
              {title}
            </h2>
            {description && (
              <p id="dialog-desc" className="text-sm text-gn-text-secondary mt-1">
                {description}
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-gn-text-tertiary hover:text-gn-text-primary p-1.5 rounded-gn-sm hover:bg-gn-bg-secondary transition-colors gn-focus-ring cursor-pointer"
            aria-label="Close dialog"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="py-4 max-h-[70vh] overflow-y-auto">{children}</div>

        {/* Footer */}
        {footer && (
          <div className="pt-4 border-t border-gn-border-default flex items-center justify-end gap-3">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
}
