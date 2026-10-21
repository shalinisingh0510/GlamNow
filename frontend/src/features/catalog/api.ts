/**
 * Typed Catalog and Pricing API calls.
 */

import { api } from "@/lib/api/client";
import {
  FIXTURE_CATEGORIES,
  FIXTURE_SERVICES,
} from "@/lib/fixtures";

export interface CategoryDto {
  id: string;
  slug: string;
  name: string;
  description: string | null;
  icon: string;
  display_order: number;
  is_active: boolean;
  service_count: number;
}

export interface ServiceSummaryDto {
  id: string;
  category_id: string;
  category_name?: string;
  slug: string;
  name: string;
  description: string;
  icon: string;
  workflow_type: string;
  starting_price_paise: number;
  duration_minutes: number;
  available_tiers: ("basic" | "standard" | "premium")[];
}

export interface ServiceTierDto {
  id: string;
  service_id: string;
  tier: "basic" | "standard" | "premium";
  name: string;
  description: string;
  brands: string;
  duration_minutes: number;
  inclusions: string[];
  exclusions: string[];
  is_popular: boolean;
  is_active: boolean;
  current_price_paise: number;
}

export interface ServiceDetailDto {
  id: string;
  category_id: string;
  slug: string;
  name: string;
  description: string;
  icon: string;
  workflow_type: string;
  display_order: number;
  is_active: boolean;
  tiers: ServiceTierDto[];
  add_ons: {
    id: string;
    service_id: string;
    name: string;
    description?: string;
    price_paise: number;
    duration_minutes: number;
    is_active: boolean;
  }[];
}

export interface QuoteRequestDto {
  service_id: string;
  tier: "basic" | "standard" | "premium";
  add_on_ids?: string[];
  discount_code?: string;
  professional_price_paise?: number;
  pincode?: string;
}

export interface QuoteResponseDto {
  quote_id: string;
  service_id: string;
  service_name: string;
  tier: "basic" | "standard" | "premium";
  tier_name: string;
  duration_minutes: number;
  brands: string;
  inclusions: string[];
  base_price_paise: number;
  add_ons: {
    id: string;
    name: string;
    price_paise: number;
    duration_minutes: number;
  }[];
  travel_fee_paise: number;
  pickup_delivery_fee_paise: number;
  subtotal_paise: number;
  discount_paise: number;
  tax_cgst_paise: number;
  tax_sgst_paise: number;
  tax_rate_percent: number;
  total_paise: number;
  expires_at: string;
  immutable_price_snapshot: Record<string, unknown>;
}

export async function fetchCategories(): Promise<CategoryDto[]> {
  const res = await api.get<CategoryDto[]>("/api/v1/catalog/categories");
  if (res.ok && res.data) {
    return res.data;
  }
  // Fallback to high-fidelity development fixtures if backend offline
  return FIXTURE_CATEGORIES.map((c, i) => ({
    id: c.id,
    slug: c.id,
    name: c.name,
    description: null,
    icon: c.icon,
    display_order: i + 1,
    is_active: true,
    service_count: parseInt(c.count) || 10,
  }));
}

export async function fetchServices(
  categoryId?: string,
  search?: string
): Promise<ServiceSummaryDto[]> {
  const params: Record<string, string> = {};
  if (categoryId && categoryId !== "all") params.category_id = categoryId;
  if (search) params.search = search;

  const res = await api.get<ServiceSummaryDto[]>("/api/v1/catalog/services", { params });
  if (res.ok && res.data && res.data.length > 0) {
    return res.data;
  }

  // Fallback to fixtures
  let list = FIXTURE_SERVICES;
  if (categoryId && categoryId !== "all") {
    list = list.filter((s) => s.categoryId === categoryId);
  }
  if (search) {
    const q = search.toLowerCase();
    list = list.filter((s) => s.name.toLowerCase().includes(q) || s.description.toLowerCase().includes(q));
  }
  return list.map((s) => ({
    id: s.id,
    category_id: s.categoryId,
    category_name: s.categoryName,
    slug: s.id,
    name: s.name,
    description: s.description,
    icon: s.icon,
    workflow_type: "at_home_visit",
    starting_price_paise: s.startingPricePaise,
    duration_minutes: s.durationMinutes,
    available_tiers: s.tiers.map((t) => t.tier),
  }));
}

export async function calculateQuote(req: QuoteRequestDto): Promise<QuoteResponseDto | null> {
  const res = await api.post<QuoteResponseDto>("/api/v1/catalog/quote", req);
  if (res.ok && res.data) {
    return res.data;
  }
  return null;
}

export async function fetchServiceDetail(serviceIdOrSlug: string): Promise<ServiceDetailDto | null> {
  const res = await api.get<ServiceDetailDto>(`/api/v1/catalog/services/${serviceIdOrSlug}`);
  if (res.ok && res.data) {
    return res.data;
  }

  // Fallback to fixtures
  const match = FIXTURE_SERVICES.find(
    (s) => s.id === serviceIdOrSlug || s.id.toLowerCase() === serviceIdOrSlug.toLowerCase()
  );
  if (!match) return null;

  return {
    id: match.id,
    category_id: match.categoryId,
    slug: match.id,
    name: match.name,
    description: match.description,
    icon: match.icon,
    workflow_type: "at_home_visit",
    display_order: 1,
    is_active: true,
    tiers: match.tiers.map((t) => ({
      id: `${match.id}-${t.tier}`,
      service_id: match.id,
      tier: t.tier,
      name: t.title,
      description: t.description || `${t.title} tier service using ${t.brands}`,
      brands: t.brands,
      duration_minutes: t.durationMinutes,
      inclusions: t.inclusions,
      exclusions: [],
      is_popular: t.isPopular || false,
      is_active: true,
      current_price_paise: t.pricePaise,
    })),
    add_ons: [
      {
        id: "addon-detan",
        service_id: match.id,
        name: "Express Sara De-Tan Pack",
        description: "Instant botanical glow treatment",
        price_paise: 29900,
        duration_minutes: 15,
        is_active: true,
      },
      {
        id: "addon-head-massage",
        service_id: match.id,
        name: "Aromatherapy Scalp Massage",
        description: "15 min relaxing warm oil head massage",
        price_paise: 34900,
        duration_minutes: 15,
        is_active: true,
      },
    ],
  };
}
