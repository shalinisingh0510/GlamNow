# Implementation Plan

**Plan date:** October 21, 2026  
**Product:** GlamNow — quick commerce for at-home services  
**Repository state:** Greenfield Git repository; see [`repository-audit.md`](./repository-audit.md)

## 1. Delivery objective

Build a production-minded Indian marketplace in small, verifiable slices. Customers should be able to discover eligible at-home beauty, grooming, massage, clothing-care, and tailoring services; compare configurable service tiers; choose a professional; book a quick or scheduled service; pay safely; track fulfillment; request support; and review completed work.

Professionals need an understandable workflow for offerings, availability, assignments, service execution, and earnings. Operations staff need catalog, service-area, pricing, professional, booking, payment, support, and audit controls. Tailoring requires a separate fulfillment model for garments, measurements, quotes, custody, production, quality checks, delivery, and fitting adjustments.

The first implementation must keep the frontend and backend separate:

```text
/frontend   Next.js customer, professional, and operations interfaces
/backend    FastAPI modular monolith, database adapters, integrations, and workers
/docs       Architecture, decisions, API and operational documentation
```

The frontend must never be the source of truth for authorization, prices, eligibility, payment state, availability, arrival estimates, or booking state.

## 2. Assumptions and boundaries

### Confirmed from the product specification

- The product targets Indian at-home services and includes tailoring and garment care.
- Service categories, tiers, prices, add-ons, durations, serviceability, promotions, professionals, and feature flags are editable business data.
- Quick booking and preferred-professional scheduled booking are both required.
- Payment, maps, notifications, object storage, and background work are integration boundaries.
- The backend is a modular monolith rather than premature microservices.
- Historical prices, configuration versions, effective dates, idempotency, auditability, and server-side authorization are required.

### Greenfield assumptions to validate during foundation work

- PostgreSQL is the system of record.
- A managed object store will hold approved customer/professional uploads; the provider is not selected yet.
- Redis is available for short-lived coordination, queues, rate limits, and cached operational data; durable business state remains in PostgreSQL.
- A maintained Python worker library will be selected after checking current FastAPI/SQLAlchemy compatibility.
- Authentication provider and Indian payment provider are product decisions that should be represented by interfaces until selected.
- Development and sandbox modes are required; production integrations must never be silently simulated.

### Out of scope for the first foundation slice

- Real payment capture, live maps, dispatch optimization, or production notifications before their providers and secrets are configured.
- A universal arbitrary JSON rules engine.
- Microservices, event-sourcing, or a large shared utility framework without a concrete need.
- A full consumer launch before booking, payment, privacy, and operational failure paths are tested.

## 3. Proposed repository layout

```text
.
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   ├── src/
│   │   ├── app/                         # App Router shells and route composition only
│   │   │   ├── (customer)/
│   │   │   ├── (professional)/
│   │   │   ├── (operations)/
│   │   │   ├── api/                     # Only if a narrow Next boundary is justified
│   │   │   └── layout.tsx
│   │   ├── components/ui/               # Accessible, behavior-focused primitives
│   │   ├── features/
│   │   │   ├── catalog/
│   │   │   ├── discovery/
│   │   │   ├── booking/
│   │   │   ├── tailoring/
│   │   │   ├── payments/
│   │   │   ├── account/
│   │   │   ├── professional/
│   │   │   └── operations/
│   │   ├── lib/
│   │   │   ├── api/                     # Generated client and typed transport
│   │   │   ├── auth/
│   │   │   ├── analytics/
│   │   │   └── config/
│   │   └── test/
│   ├── tests/e2e/
│   └── public/
├── backend/
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/
│   ├── app/
│   │   ├── main.py                      # FastAPI composition and lifespan
│   │   ├── core/                         # Settings, auth primitives, errors, logging
│   │   ├── api/                          # Versioned HTTP routers and dependencies
│   │   ├── db/                           # Engine, session, transaction helpers
│   │   ├── modules/
│   │   │   ├── identity/
│   │   │   ├── catalog/
│   │   │   ├── professionals/
│   │   │   ├── serviceability/
│   │   │   ├── availability/
│   │   │   ├── bookings/
│   │   │   ├── tailoring/
│   │   │   ├── payments/
│   │   │   ├── fulfillment/
│   │   │   ├── reviews/
│   │   │   ├── support/
│   │   │   └── operations/
│   │   ├── integrations/                 # Payment, maps, notifications, storage
│   │   └── workers/                      # Retryable background jobs
│   └── tests/
├── docs/
│   ├── architecture/
│   ├── api/
│   ├── operations/
│   └── privacy/
├── .env.example                          # Names and safe placeholders only
├── compose.dev.yml                       # Local dependencies, if needed
└── README.md
```

The exact folders can be adjusted as implementation reveals real boundaries. The important constraints are independent frontend/backend manifests, feature-oriented frontend modules, backend domain ownership, and no direct cross-module database writes.

## 4. Domain and data design direction

### Catalog and configuration

Use relational tables with explicit types and version records rather than UI constants or an unsafe rule engine. Initial concepts:

- `service_categories`
- `service_types`
- `service_tier_definitions`
- `service_tier_versions`
- `service_add_ons`
- `service_duration_rules`
- `service_price_rules`
- `service_area_coverage`
- `feature_flags`
- `professional_offerings`

Each editable definition should have status, effective dates, version identity, created/updated metadata, and audit history. Booking records must copy the effective service, tier, inclusion, duration, and price snapshot they used so later catalog edits cannot rewrite history.

Pricing and eligibility should be represented by typed, bounded structures such as geography, service type, tier, quantity, time window, surge/promotion references, and explicitly supported tailoring inputs. Do not accept executable expressions or arbitrary frontend-supplied formulas.

### Identity and authorization

Model users, roles, professional profiles, operations permissions, customer ownership, and service-area access explicitly. Every protected endpoint should enforce authentication, role permissions, and resource ownership or operational scope on the server. Role claims from the browser are advisory only.

### Discovery, availability, and booking

Separate:

1. **Discovery:** catalog, professional profiles, reviews, portfolio metadata, serviceability, and estimated arrival windows.
2. **Eligibility:** whether a service, location, customer, professional, time, and operational policy can be booked.
3. **Reservation:** an atomic hold/booking operation with idempotency and conflict protection.
4. **Fulfillment:** assignment, arrival, execution, completion, cancellation, refund, and support state.

Use database constraints and transactions to prevent overlapping professional assignments. Quick-booking estimates should be labeled as estimates and depend on current coverage, professional availability, travel time, and dispatch capacity. Ten minutes is an operational target, not a promise.

### Tailoring and garment care

Tailoring should not be forced into generic appointment fields. Model:

- garment types and typed specification schemas;
- separate garment items within one order;
- versioned measurement profiles and consent/access metadata;
- measurement appointments;
- reference uploads with access and retention policy;
- quote versions and customer approval;
- fabric pickup and item-count records;
- condition records and custody handovers;
- production stages, assigned work, quality checks, delivery, and fitting adjustments.

Every state transition should be explicit, authorized, timestamped, and auditable. Measurements and reference images are sensitive customer data: minimize access, define retention/deletion behavior, use signed object URLs, and avoid logging payloads.

## 5. Integration boundaries

Define small ports in the backend and keep provider code in adapters:

- `PaymentGateway`: create intent/order, verify webhook, capture/refund, query status.
- `MapsProvider`: geocode, serviceability, route/travel estimate.
- `NotificationSender`: SMS, email, push, and operational alerts.
- `ObjectStorage`: upload policy, signed URL, metadata, deletion.
- `Clock` and `IdGenerator`: deterministic tests and idempotency.
- `TaskQueue`: retryable asynchronous work.

Development adapters may expose deterministic sandbox behavior, but must be clearly labeled. They must not report a successful production payment, real-time ETA, or completed fulfillment without the corresponding integration state. Webhooks must verify signatures, deduplicate events, store provider references, and use bounded retries.

## 6. Phased delivery plan

### Phase 0 — Foundation and verification

**Deliverable:** runnable frontend and backend in separate folders with documented local setup.

- Add pinned manifests and lockfiles.
- Add environment parsing with safe startup validation and `.env.example`.
- Add FastAPI health/readiness endpoints, request IDs, structured error shape, and logging redaction.
- Add Next.js shell, design tokens, responsive layout, accessible primitives, and loading/error/empty states.
- Add PostgreSQL connection, Alembic baseline, and a local dependency strategy.
- Add OpenAPI export and the first generated TypeScript client path.
- Add formatting, linting, typechecking, unit-test, and smoke-test commands.
- Document an initial ADR for the modular monolith and frontend/backend boundary.

**Acceptance criteria:** a clean checkout can start both apps with documented commands; health checks respond; no secrets are committed; the frontend can call a typed backend health endpoint; all configured checks run and report their real status.

### Phase 1 — Catalog and service discovery

**Deliverable:** configuration-driven customer browsing.

- Create catalog, tier, add-on, price-version, service-area, and professional-offering schemas.
- Add authorized operations APIs for draft/publish/effective-date changes.
- Add public read APIs for categories, service details, tier comparison, and availability summary.
- Build customer category/detail views using API data only.
- Add empty, loading, unavailable, and stale-configuration states.

**Acceptance criteria:** changing a published catalog record changes rendered content without a frontend deployment; historical booking snapshots are designed before booking work begins; unauthorized catalog mutation is rejected.

### Phase 2 — Identity, professional discovery, and booking

**Deliverable:** safe quick and scheduled booking flow.

- Add authentication and role-aware sessions.
- Add professional profiles, verification, portfolios, reviews, service areas, and availability windows.
- Add serviceability and arrival estimate interfaces.
- Add booking quote, idempotent reservation, conflict prevention, cancellation, and state transitions.
- Implement customer and professional booking views.
- Add backend unit/integration tests and Playwright happy/error paths.

**Acceptance criteria:** a retry does not create duplicate bookings; two concurrent requests cannot reserve the same professional slot; all displayed price and eligibility values come from a validated server quote; an unavailable professional produces an explicit recoverable state.

### Phase 3 — Payments, notifications, and operational fulfillment

**Deliverable:** provider-backed payment and order lifecycle.

- Add payment intents, transaction references, webhook verification, refunds, and reconciliation state.
- Add notification outbox/jobs and retry handling.
- Add assignment/dispatch states and explicit ETA confidence/estimate labeling.
- Add customer tracking, support entry points, cancellation/refund status, and review eligibility.
- Add operations views for stuck, failed, and manually recoverable jobs.

**Acceptance criteria:** redirect URLs cannot mark an order paid; duplicate webhooks are harmless; partial provider failure is visible and recoverable; no private payment credential is stored or logged.

### Phase 4 — Tailoring and garment fulfillment

**Deliverable:** garment-aware order workflow.

- Add typed garment specifications for shirts, trousers, blouses, sarees, alterations, repairs, pico-fall, and hemming.
- Add measurement appointments, versioned profiles, uploads, quote approval, item counts, condition/custody events, and production stages.
- Add quality checks, delivery, fitting adjustments, and customer history.
- Add privacy/retention controls and restricted-access audit trails.

**Acceptance criteria:** one order can contain garments with different specifications and statuses; a changed measurement version cannot silently rewrite a production record; custody and quality events are attributable and queryable.

### Phase 5 — Professional and operations portals

**Deliverable:** role-focused workflows instead of generic dashboards.

- Professional onboarding, offerings, availability, assignment response, service execution, earnings, and issue reporting.
- Operations catalog/version management, professional verification, service areas, booking intervention, refunds, support, audit log, and feature flags.
- Permission matrices and audit views for sensitive actions.

**Acceptance criteria:** each action is available only to the required role/scope; operations can correct a recoverable failure without direct database edits; sensitive changes create audit records.

### Phase 6 — Hardening and launch readiness

**Deliverable:** measured reliability and deployment readiness.

- Add rate limiting, abuse controls, upload validation/scanning, backup/restore procedures, retention jobs, and security review.
- Add performance baselines for discovery, quote, booking, and operations queries.
- Add observability dashboards, alerts, correlation IDs, and runbooks.
- Exercise migrations, rollback/forward-fix strategy, sandbox provider failures, and disaster recovery.
- Verify responsive behavior and accessibility with keyboard, screen reader, contrast, and reduced-motion checks.

**Acceptance criteria:** release checks are reproducible from clean checkout; important failures have actionable logs and user-safe messages; production mode refuses missing critical secrets or provider verification configuration.

## 7. Quality gates for every phase

Before calling a phase complete:

1. Read the relevant files and define the slice's acceptance criteria.
2. Add unit tests for domain rules and boundary cases.
3. Add integration tests for persistence, authorization, idempotency, and provider adapters where relevant.
4. Add or update Playwright flows for user-visible critical paths.
5. Run formatting, linting, typechecking, migrations, backend tests, frontend tests, and relevant browser tests.
6. Review accessibility, responsive states, security, privacy, retries, timeouts, and partial failures.
7. Update API/client documentation, `.env.example`, operational notes, and ADRs.
8. Report exact commands, working directories, results, known limitations, and the next phase.

No feature is complete if its primary action is a dead button, a static mockup, a hardcoded success state, or a client-only validation path.

## 8. Initial architecture decisions to record as ADRs

Create these as short ADR files when the corresponding implementation begins:

- **ADR-0001:** Separate Next.js frontend and FastAPI backend in one repository.
- **ADR-0002:** Modular monolith with domain-owned persistence access.
- **ADR-0003:** Versioned, effective-dated catalog and immutable booking price snapshots.
- **ADR-0004:** Provider ports and adapters for payments, maps, notifications, storage, and queues.
- **ADR-0005:** Typed tailoring specifications and explicit garment-item fulfillment states.
- **ADR-0006:** Idempotent booking/payment workflows with transactional conflict protection.
- **ADR-0007:** Sensitive measurement and upload retention/access policy.

Each ADR should state context, decision, rejected alternatives, consequences, and the date. Avoid recording provider-specific decisions before the provider requirements are confirmed.

## 9. First implementation slice

After this audit, the next implementation slice should be **Phase 0 only**: scaffold the separate `/frontend` and `/backend` roots, establish pinned dependencies and environment examples, create health checks and the API/client boundary, and add the initial quality commands. Do not implement booking, payment, dispatch, or tailoring behavior in the foundation slice.

The empty Git state means there is no legacy code to migrate and no user work to overwrite. It does not mean external integrations are available; those should remain explicit configuration gaps until credentials and provider choices are supplied.
