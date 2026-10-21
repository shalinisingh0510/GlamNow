# ADR-0005: Typed Tailoring Specifications and Explicit Fulfillment State Machines

## Status
Accepted

## Date
2026-10-21

## Context
Tailoring and custom garment care (blouse stitching, saree pico-fall, kurti alterations) differ fundamentally from standard 30-minute grooming appointments:
- They require physical fabric collection, master measurement recording, stitching workshop queues, trial fittings, and final doorstep delivery.
- Squeezing tailoring workflows into generic appointment fields causes ambiguity and fulfillment failures.

## Decision
1. **Dedicated Domain Entity:** Create first-class entities: `TailoringOrder`, `GarmentItem`, `MeasurementProfile`, and `FabricPickupTask`.
2. **Strict Fulfillment State Machine:**
   - `MEASUREMENT_SCHEDULED` -> `MEASURED` (or `SAMPLE_GARMENT_COLLECTED`)
   - `FABRIC_PICKUP_ASSIGNED` -> `FABRIC_COLLECTED` -> `IN_WORKSHOP`
   - `CUTTING` -> `STITCHING` -> `QUALITY_CHECKED`
   - `OUT_FOR_DELIVERY` -> `TRIAL_DELIVERED` -> `ACCEPTED` (or `REWORK_REQUESTED` -> `REWORK_IN_PROGRESS`)
3. **Discrete Garment Items:** Each order can contain multiple garments (e.g. 2 blouses, 1 saree pico-fall), each progressing through its own workshop state independently.

## Consequences
- **Positive:** Full visibility into multi-day workshop progress; handles rework loops without breaking payment records; clear logistics handover.
- **Negative:** Increased data modeling complexity compared to single-visit salon bookings.
