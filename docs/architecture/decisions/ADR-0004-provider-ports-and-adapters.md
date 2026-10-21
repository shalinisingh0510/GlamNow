# ADR-0004: Provider Ports and Adapters for External Services

## Status
Accepted

## Date
2026-10-21

## Context
A quick-commerce marketplace requires multiple third-party integrations:
- Payment Gateways: Razorpay, Cashfree, UPI Deep-links.
- Geocoding & Travel Estimation: Google Maps, MapmyIndia, OpenStreetMap.
- Notifications: SMS (Twilio, Gupshup, Msg91), WhatsApp Business, push notifications.
- Object Storage: AWS S3, Cloudflare R2, MinIO for style references and garment photos.

Hardcoding direct SDK calls inside application routes or domain models locks the platform into specific vendors and complicates unit testing.

## Decision
Introduce a Ports and Adapters (Hexagonal) pattern within `backend/app/integrations/`:
1. **Ports (Abstract Interfaces):** Define typed Python protocols or abstract base classes (e.g., `PaymentGatewayPort`, `GeocodingPort`, `NotificationPort`, `StoragePort`).
2. **Adapters (Concrete Implementations):** Implement provider-specific adapters (e.g., `RazorpayPaymentAdapter`, `GoogleMapsAdapter`, `S3StorageAdapter`) alongside in-memory `MockPaymentAdapter` and `MockGeocodingAdapter` for local tests.
3. **Dependency Injection:** Provide active adapters via FastAPI dependency injection or application settings factory.

## Consequences
- **Positive:** Domain logic remains isolated from external SDK changes; deterministic unit and integration tests without network I/O or live API keys; ability to switch or fall back between gateways seamlessly.
- **Negative:** Requires boilerplate interface definitions and translation models for each external provider.
