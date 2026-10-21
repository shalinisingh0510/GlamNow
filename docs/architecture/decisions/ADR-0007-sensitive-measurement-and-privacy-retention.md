# ADR-0007: Sensitive Measurement Data and Customer Privacy Policy

## Status
Accepted

## Date
2026-10-21

## Context
Custom tailoring requires collecting intimate customer measurements (bust, waist, hip, inseam, shoulder-to-apex) and reference fitting photos. Under India's Digital Personal Data Protection Act (DPDP Act 2023) and standard privacy best practices:
- Measurement records and reference photos constitute sensitive personal data.
- Unrestricted access by all platform staff or tailors creates severe privacy risks.
- Data must be retained only as long as needed for order fulfillment unless explicitly saved by the customer as a reusable profile.

## Decision
1. **Field-Level Encryption & RBAC:** Measurement records are encrypted at rest with dedicated customer encryption keys and accessible strictly to the assigned master tailor during the active fulfillment window.
2. **Ephemeral Photo Retention:** Fabric reference or trial photos uploaded by customers are stored in private S3 buckets with signed URLs (15-minute expiration) and automatically purged 30 days after completed order delivery.
3. **Explicit Consent & Right to Erasure:** Customers have full UI controls to view, edit, or purge their saved measurement profiles at any time.

## Consequences
- **Positive:** Full compliance with DPDP Act 2023; high customer trust for home tailoring services; minimal data liability surface.
- **Negative:** Requires cryptographic key management and automated lifecycle expiration policies on cloud storage.
