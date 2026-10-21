/**
 * Typed API client for the GlamNow backend.
 *
 * Uses fetch with typed error handling. In later phases this will
 * be replaced by an OpenAPI-generated client.
 */

import { config } from "@/lib/config";

export interface ApiError {
  ok: false;
  request_id?: string;
  errors: Array<{
    code: string;
    message: string;
    field?: string;
    meta?: Record<string, unknown>;
  }>;
}

export interface HealthResponse {
  ok: boolean;
  environment: string;
  version: string;
  timestamp: string;
}

export interface ReadinessCheck {
  name: string;
  ok: boolean;
  latency_ms?: number;
  error?: string;
}

export interface ReadinessResponse {
  ok: boolean;
  checks: ReadinessCheck[];
}

class ApiClientError extends Error {
  constructor(
    public status: number,
    public body: ApiError,
  ) {
    super(body.errors?.[0]?.message ?? "Unknown API error");
    this.name = "ApiClientError";
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${config.apiUrl}${path}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!response.ok) {
    let errorBody: ApiError;
    try {
      errorBody = await response.json();
    } catch {
      errorBody = {
        ok: false,
        errors: [{ code: "NETWORK_ERROR", message: "Failed to parse error response" }],
      };
    }
    throw new ApiClientError(response.status, errorBody);
  }

  return response.json();
}

export interface ApiResponse<T> {
  ok: boolean;
  status: number;
  data?: T;
  error?: string;
}

/** API client methods — thin wrappers over typed fetch. */
export const api = {
  health: {
    check: () => request<HealthResponse>("/health"),
    readiness: () => request<ReadinessResponse>("/readiness"),
  },
  get: async <T>(path: string, options?: { params?: Record<string, string> }): Promise<ApiResponse<T>> => {
    let url = path;
    if (options?.params) {
      const q = new URLSearchParams(options.params).toString();
      if (q) url += `?${q}`;
    }
    try {
      const fullUrl = `${config.apiUrl}${url}`;
      const res = await fetch(fullUrl, { headers: { "Content-Type": "application/json" } });
      if (!res.ok) {
        return { ok: false, status: res.status, error: res.statusText };
      }
      const data = await res.json();
      return { ok: true, status: res.status, data };
    } catch (e: unknown) {
      return { ok: false, status: 0, error: e instanceof Error ? e.message : "Network error" };
    }
  },
  post: async <T>(path: string, body?: unknown): Promise<ApiResponse<T>> => {
    try {
      const fullUrl = `${config.apiUrl}${path}`;
      const res = await fetch(fullUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: body ? JSON.stringify(body) : undefined,
      });
      if (!res.ok) {
        return { ok: false, status: res.status, error: res.statusText };
      }
      const data = await res.json();
      return { ok: true, status: res.status, data };
    } catch (e: unknown) {
      return { ok: false, status: 0, error: e instanceof Error ? e.message : "Network error" };
    }
  },
};

export { ApiClientError };
