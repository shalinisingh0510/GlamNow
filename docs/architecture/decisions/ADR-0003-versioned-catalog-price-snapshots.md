# ADR-0003: Versioned, Effective-Dated Catalog and Immutable Booking Price Snapshots

## Status
Accepted

## Date
2026-10-21

## Context
In service marketplaces with varying tiers (Basic, Standard, Premium), catalog managers frequently adjust pricing, add-on inclusions, and seasonal promotions. If a booking entity merely stores foreign keys to mutable catalog rows:
- Price changes alter historic revenue and invoice audits.
- In-flight checkouts might bill an unexpected amount if prices shift midway.
- Disputes over included items or duration cannot be resolved definitively.

## Decision
1. **Catalog Versioning:** All catalog definitions (`service_types`, `service_tier_definitions`, `pricing_rules`) include version identifiers, status flags, and effective date ranges (`valid_from`, `valid_to`). Modifying a tier or price creates a new version record rather than mutating existing rows in place.
2. **Immutable Booking Snapshots:** When a reservation or order is created, the system copies an explicit JSON snapshot of the effective tier details, base price, applied add-ons, estimated duration, and taxes into the booking record.
3. **Idempotent Checkout:** Booking checkouts validate against the snapshot created during the reservation hold window (e.g., 10 minutes) to guarantee deterministic billing.

## Consequences
- **Positive:** Uncompromised financial auditability; immune to pricing drift during active checkout; zero risk of retroactive invoice alterations.
- **Negative:** Marginal increase in storage volume due to versioned records and embedded snapshot JSON columns.
