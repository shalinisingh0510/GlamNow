"use client";

import { useState } from "react";
import { Dialog } from "@/components/ui/dialog";

export interface PortfolioItem {
  id: string;
  title: string;
  description?: string;
  imageUrl: string;
  serviceName?: string;
  isVerified?: boolean;
}

export interface PortfolioGalleryProps {
  items: PortfolioItem[];
  title?: string;
}

export function PortfolioGallery({
  items,
  title = "Authentic Client Portfolio",
}: PortfolioGalleryProps) {
  const [activeItem, setActiveItem] = useState<PortfolioItem | null>(null);

  if (!items || items.length === 0) {
    return null;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-serif text-lg font-bold text-gn-text-primary">{title}</h3>
          <p className="text-xs text-gn-text-tertiary">
            Real transformations verified by GlamNow quality auditors
          </p>
        </div>
        <span className="text-xs font-semibold text-gn-accent-primary bg-gn-accent-primary-subtle px-2.5 py-1 rounded-full">
          {items.length} Verified Looks
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
        {items.map((item) => (
          <div
            key={item.id}
            onClick={() => setActiveItem(item)}
            className="group relative aspect-square rounded-gn-md overflow-hidden bg-gn-bg-secondary border border-gn-border-default hover:border-gn-accent-primary cursor-pointer transition-all shadow-gn-sm"
          >
            <img
              src={item.imageUrl}
              alt={item.title}
              className="h-full w-full object-cover group-hover:scale-105 transition-transform duration-300"
              loading="lazy"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex flex-col justify-end p-2.5 text-white">
              <span className="text-[10px] font-bold uppercase tracking-wider text-gn-accent-secondary">
                {item.serviceName || "Client Transformation"}
              </span>
              <p className="text-xs font-medium line-clamp-1">{item.title}</p>
            </div>
            {item.isVerified && (
              <span className="absolute top-2 right-2 bg-emerald-600/90 text-white text-[9px] font-bold px-1.5 py-0.5 rounded shadow-xs">
                ✓ Verified Look
              </span>
            )}
          </div>
        ))}
      </div>

      {/* Lightbox Dialog */}
      <Dialog
        open={Boolean(activeItem)}
        onClose={() => setActiveItem(null)}
        title={activeItem?.title || "Portfolio Look"}
        description={activeItem?.serviceName ? `Category: ${activeItem.serviceName}` : undefined}
      >
        {activeItem && (
          <div className="space-y-3">
            <div className="relative aspect-[4/3] w-full rounded-gn-md overflow-hidden bg-black/5 border border-gn-border-default">
              <img
                src={activeItem.imageUrl}
                alt={activeItem.title}
                className="h-full w-full object-contain"
              />
            </div>
            {activeItem.description && (
              <p className="text-sm text-gn-text-secondary leading-relaxed bg-gn-bg-secondary/60 p-3 rounded-gn-sm border border-gn-border-default/60">
                {activeItem.description}
              </p>
            )}
            <div className="flex items-center justify-between pt-2 text-xs text-gn-text-tertiary">
              <span className="flex items-center gap-1 text-emerald-700 font-semibold">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                Authentic customer session photo
              </span>
              <span className="italic">Standard quality verified</span>
            </div>
          </div>
        )}
      </Dialog>
    </div>
  );
}
