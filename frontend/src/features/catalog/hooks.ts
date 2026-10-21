"use client";

import { useQuery, useMutation } from "@tanstack/react-query";
import {
  fetchCategories,
  fetchServices,
  fetchServiceDetail,
  calculateQuote,
  type CategoryDto,
  type ServiceSummaryDto,
  type ServiceDetailDto,
  type QuoteRequestDto,
  type QuoteResponseDto,
} from "./api";

export function useCategories() {
  return useQuery<CategoryDto[]>({
    queryKey: ["catalog", "categories"],
    queryFn: fetchCategories,
    staleTime: 5 * 60 * 1000,
  });
}

export function useServices(categoryId?: string, search?: string) {
  return useQuery<ServiceSummaryDto[]>({
    queryKey: ["catalog", "services", categoryId, search],
    queryFn: () => fetchServices(categoryId, search),
    staleTime: 60 * 1000,
  });
}

export function useServiceDetail(serviceIdOrSlug: string | null) {
  return useQuery<ServiceDetailDto | null>({
    queryKey: ["catalog", "service", serviceIdOrSlug],
    queryFn: () => (serviceIdOrSlug ? fetchServiceDetail(serviceIdOrSlug) : null),
    enabled: Boolean(serviceIdOrSlug),
    staleTime: 60 * 1000,
  });
}

export function useCalculateQuote() {
  return useMutation<QuoteResponseDto | null, Error, QuoteRequestDto>({
    mutationFn: (req: QuoteRequestDto) => calculateQuote(req),
  });
}
