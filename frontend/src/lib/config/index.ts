/**
 * Environment configuration for the frontend.
 *
 * All runtime config is read from NEXT_PUBLIC_* env vars so the
 * backend URL and feature flags can change per deployment without
 * rebuilding the frontend.
 */

export const config = {
  /** Backend API base URL (no trailing slash). */
  apiBaseUrl: process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",

  /** API version prefix. */
  apiPrefix: process.env.NEXT_PUBLIC_API_PREFIX ?? "/api/v1",

  /** Full API URL. */
  get apiUrl(): string {
    return `${this.apiBaseUrl}${this.apiPrefix}`;
  },

  /** Application name. */
  appName: "GlamNow",

  /** Application tagline. */
  tagline: "Premium at-home beauty, grooming & tailoring",
} as const;
