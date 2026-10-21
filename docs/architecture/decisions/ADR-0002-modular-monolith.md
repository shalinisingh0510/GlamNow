# ADR-0002: Modular Monolith with Domain-Owned Persistence Access

## Status
Accepted

## Date
2026-10-21

## Context
Early-stage quick commerce platforms frequently fall into two traps:
1. An unconstrained monolith with cross-domain database queries and tangled business logic.
2. Premature microservices introducing distributed transaction overhead, network latency, and operational fragility.

GlamNow spans multiple interrelated domains: catalog, availability, identity, bookings, fulfillment, tailoring, payments, reviews, and support.

## Decision
Implement a **Modular Monolith** architecture within `/backend/app/modules/`.
- Each domain module owns its entity models, repositories, and domain services.
- Cross-domain operations must call public module interfaces or dispatch domain events rather than executing direct SQL joins across unowned tables.
- Database access is managed through domain-scoped repositories.
- If a domain (such as dispatch matching or notifications) requires dedicated scaling later, its cleanly separated module boundary facilitates extraction into an independent service with minimal friction.

## Consequences
- **Positive:** Single deployment target; zero distributed transaction failures; clear ownership boundaries and testability.
- **Negative:** Requires continuous code-review discipline and linting to avoid illicit cross-module database imports.
