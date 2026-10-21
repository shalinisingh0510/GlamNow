# ADR-0006: Idempotent Booking and Payment Workflows with Transactional Conflict Protection

## Status
Accepted

## Date
2026-10-21

## Context
In mobile and web marketplaces, network retries, double taps, or simultaneous checkout attempts can result in:
- Duplicate bookings for the same customer.
- Overlapping double-booking of a single professional.
- Double charges on UPI or credit card gateways.

## Decision
1. **Idempotency Keys:** Every mutating booking and payment request requires a client-supplied or generated `Idempotency-Key` header stored in Redis with a 24-hour TTL and transactional commit lock.
2. **Two-Phase Reservation:**
   - **Phase 1: Temporary Hold (TTL 10 mins).** The professional's slot is held with optimistic locking (`SELECT ... FOR UPDATE` or Redis distributed lock).
   - **Phase 2: Payment & Confirmation.** Upon gateway payment verification or COD confirmation, the hold transitions to `CONFIRMED`. If the timer expires before payment, the hold is released automatically.
3. **Database Constraints:** Exclusion constraints or unique composite indexes (`professional_id`, `scheduled_window`) prevent overlapping confirmed bookings in the database.

## Consequences
- **Positive:** Zero accidental double charges; zero conflicting professional double bookings; high resilience under spotty Indian mobile networks.
- **Negative:** Requires Redis dependency for fast distributed reservation holds.
