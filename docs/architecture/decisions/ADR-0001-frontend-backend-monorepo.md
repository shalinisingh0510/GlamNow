# ADR-0001: Separate Next.js Frontend and FastAPI Backend in Single Monorepo

## Status
Accepted

## Date
2026-10-21

## Context
GlamNow requires a high-performance customer-facing web application with modern typography, reactive UI, SEO capabilities, and fast delivery estimates. On the backend, it requires a robust, typed domain model with async database support, background worker queues, strict idempotency keys, and payment/geolocation integrations.

We evaluated three repository organization patterns:
1. Pure multi-repo (completely separate Git repositories).
2. Monorepo with unified tooling and polyglot workspaces.
3. Single Next.js full-stack app (using Route Handlers for all domain persistence and business logic).

## Decision
Adopt a single Git monorepo containing decoupled `/frontend` (Next.js 16 with App Router) and `/backend` (FastAPI with Python 3.14 and uv).
- The frontend and backend maintain their own dependency manifests (`package.json` vs `pyproject.toml`) and independent CI pipelines.
- Communication between frontend and backend is strictly via versioned HTTP APIs (`/api/v1/`) with typed schemas.
- Local development is orchestrated cleanly without coupling runtime build steps.

## Consequences
- **Positive:** Atomic pull requests spanning schema additions and client UI changes; single source of truth for architecture documents and ADRs; simplifies local developer onboarding.
- **Negative:** Requires developers working across stacks to have both Node.js and Python toolchains installed locally.
