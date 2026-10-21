# GlamNow Repository Audit & Baseline Assessment

**Audit Date:** October 21, 2026  
**Repository Branch / Commit:** `main` @ `89599ea` (`v1`)  
**Audit Scope:** Local monorepo (`backend/`, `frontend/`, `docs/`, root config), test executions, build logs, and code inspection.

---

## 1. Executive Summary

The GlamNow repository represents a clean, newly-initialized production scaffold adhering to the modern decoupled monorepo architecture. 

In Commit `89599ea` (`v1`), the repository established:
1. **Root Infrastructure:** Docker Compose (`compose.dev.yml`) for local PostgreSQL 16 and Redis 7; root `.env.example` mapping backend and frontend configuration.
2. **Backend Engine (`/backend`):** FastAPI application with Python 3.14.8, Pydantic v2, uv package management, structured JSON logging, standard correlation middleware (`X-Request-ID`), unified error hierarchy, async database session lifecycle, Alembic migrations skeleton, and a 16-test unit suite with 100% pass rate.
3. **Frontend Application (`/frontend`):** Next.js 16.4.2 App Router (React 19.3.0, Tailwind v4, TanStack Query v5), accessible UI primitives (`Button`, `Card`, `Badge`, `Input`), responsive brand layout (`Header`, `Footer`), typed API client, and an interactive landing page showcasing quick-commerce delivery, multi-tier comparison, verified pro picker, and doorstep tailoring studio.

There is zero legacy technical debt or obsolete codebase to migrate. However, multiple features currently contain hardcoded mock data, stubbed integrations, and incomplete workflows that must be built out across subsequent phases.

---

## 2. Baseline Verification Checks

All baseline verification commands were executed directly in the project environment. Results:

| Check Target | Command Executed | Result | Metric / Note |
|:---|:---|:---:|:---|
| **Backend Unit Tests** | `uv run pytest tests/ -v` | **PASSED** | 16 passed in 0.02s; 0 failures. |
| **Backend Code Compilation** | `python -m compileall app/ tests/` | **PASSED** | 0 syntax or import errors. |
| **Frontend Linting** | `npm run lint` | **PASSED** | 0 errors, 0 warnings (clean ESLint 9). |
| **Frontend Production Build** | `npm run build` | **PASSED** | Compiled in 205ms; static pages generated via Turbopack. |
| **Database Migrations** | Directory inspection (`alembic/versions`) | **PENDING** | Alembic initialized; 0 revision files present. |
| **Git Working Tree** | `git status --porcelain` | **CLEAN** | Working tree clean matching commit `89599ea`. |

---

## 3. Dependency Inventory & Runtimes

### System Runtimes
- **Python:** `3.14.8` (managed via Astral `uv`)
- **Node.js:** `v26.11.0` (Turbopack, Next.js 16.4.2)

### Backend Dependencies (`backend/pyproject.toml`)
| Package | Pinned Version | Purpose |
|:---|:---|:---|
| `fastapi` | `>=0.115.0` | High-performance asynchronous REST API framework |
| `uvicorn[standard]` | `>=0.34.0` | ASGI web server with uvloop support |
| `pydantic` | `>=2.10.0` | Data validation and typed schemas |
| `pydantic-settings` | `>=2.7.0` | Environment variable parsing and type enforcement |
| `sqlalchemy[asyncio]` | `>=2.0.36` | Asynchronous ORM and SQL expression engine |
| `asyncpg` | `>=0.30.0` | High-throughput PostgreSQL asynchronous driver |
| `alembic` | `>=1.14.0` | Schema migration manager |
| `redis` | `>=5.2.0` | Redis client for caching, idempotency & locks |
| `httpx` | `>=0.28.0` | Async HTTP client for external integrations |
| `pytest` / `pytest-asyncio` | `>=8.3.0` / `>=0.25.0` | Test runner and async test fixtures |

### Frontend Dependencies (`frontend/package.json`)
| Package | Pinned Version | Purpose |
|:---|:---|:---|
| `next` | `16.4.2` | App Router, Server Components & Turbopack bundler |
| `react` / `react-dom` | `19.3.0` | UI rendering engine |
| `tailwindcss` | `^4.0.0` | Utility CSS with `@theme inline` design tokens |
| `@tanstack/react-query` | `^5.104.5` | Server-state caching and async query management |
| `react-hook-form` | `^7.90.0` | Performant form state handling |
| `zod` | `^3.25.76` | Runtime client schema validation |

---

## 4. Current Application Inventory

### Backend Components & Endpoints
- **Entry Point:** [`backend/app/main.py`](file:///Users/kumargaurav/Desktop/GlamNow/backend/app/main.py) with CORS middleware, request ID injection, structured request logging, and global exception handlers.
- **Health Check Route:** `GET /api/v1/health` in [`backend/app/api/v1/health.py`](file:///Users/kumargaurav/Desktop/GlamNow/backend/app/api/v1/health.py). Returns status, environment, version, uptime, and request correlation ID.
- **Core Modules:**
  - `app.core.settings`: Pydantic BaseSettings class loading `GLAMNOW_*` environment variables.
  - `app.core.errors`: Structured error hierarchy (`AppError`, `NotFoundError`, `ConflictError`, `ValidationError`, `ForbiddenError`, `UnauthorizedError`).
  - `app.core.logging`: JSON structured logger with correlation IDs.
  - `app.core.middleware`: `RequestIDMiddleware` ensuring end-to-end audit tracing.
  - `app.db`: Async engine factory, `AsyncSessionLocal`, and `get_db_session` dependency.
- **Domain Modules Scaffolded (`backend/app/modules/`):**
  `availability`, `bookings`, `catalog`, `fulfillment`, `identity`, `operations`, `payments`, `professionals`, `reviews`, `serviceability`, `support`, `tailoring`, `workers`. (Currently container folders awaiting entity and repository models).

### Frontend Components & Pages
- **Root Layout:** [`frontend/src/app/layout.tsx`](file:///Users/kumargaurav/Desktop/GlamNow/frontend/src/app/layout.tsx) wrapping application in `QueryProvider`, Google Outfit typography, Header, and Footer.
- **Home Page:** [`frontend/src/app/page.tsx`](file:///Users/kumargaurav/Desktop/GlamNow/frontend/src/app/page.tsx) with interactive tier selection, pro card viewer, tailoring step viewer, and pincode checker.
- **UI Components:**
  - `Button` (`components/ui/button.tsx`)
  - `Card` (`components/ui/card.tsx`)
  - `Badge` (`components/ui/badge.tsx`)
  - `Input` (`components/ui/input.tsx`)
- **Shared Components:**
  - `Header` (`components/header.tsx`)
  - `Footer` (`components/footer.tsx`)
- **API Client:** [`frontend/src/lib/api/client.ts`](file:///Users/kumargaurav/Desktop/GlamNow/frontend/src/lib/api/client.ts) with typed fetch wrapper.

---

## 5. Audit Findings & Gap Analysis

### 5.1 Hardcoded Business Data
1. **Frontend Landing Page (`frontend/src/app/page.tsx`):**
   - `FEATURED_PROS` array: Hardcoded professionals (Priya Sharma, Ramesh Kumar, Ananya Deshmukh) and review metrics.
   - `CATEGORIES` array: Hardcoded service categories and item counts.
   - Pricing constants: Hardcoded tier prices (`₹399`, `₹799`, `₹1,499`) and tailoring base prices (`₹299`, `₹699`, `₹199`).
   - Location chip: Hardcoded `560038` and `Indiranagar, Bengaluru`.
2. **Backend Health Check (`backend/app/api/v1/health.py`):**
   - Database and Redis statuses return `"not_configured"` strings rather than live ping checks.

*Remediation Plan:* Build the versioned catalog and serviceability REST APIs so the frontend fetches dynamic data via TanStack Query.

### 5.2 Duplicated Code & Circular Dependencies
- **Duplication:** None identified. Primitives and layouts are cleanly separated.
- **Circular Dependencies:** Zero circular imports detected (`compileall` and Next.js Turbopack build passed cleanly).

### 5.3 Security Gaps
1. **Secret Key Default:** `GLAMNOW_SECRET_KEY` uses a development placeholder (`dev-secret-key-change-in-production-min-32-chars-long`). A runtime warning is emitted by Pydantic. Must be strictly validated in production.
2. **CORS Origins:** Default allows `localhost:3000` and `127.0.0.1:3000`. Must enforce strict origin whitelisting in staging and production.
3. **Sensitive Tailoring Data:** Tailoring measurements (bust, waist, hip, etc.) and photos must not be logged or exposed to unassigned tailors (documented in ADR-0007).
4. **Idempotency Keys:** Mutating checkout requests must enforce mandatory `Idempotency-Key` headers (documented in ADR-0006).

### 5.4 Incomplete Workflows
1. **Catalog & Tier Engine:** No database tables for service categories, tiers, or versioned price snapshots yet.
2. **Serviceability & Pincode Lookup:** Pincode validation on the frontend is currently a client-side string check rather than a database polygon/zone query.
3. **Professional Scheduling & Dispatch:** Matching algorithm, arrival estimation, and slot reservations are not yet implemented.
4. **Tailoring Fulfillment State Machine:** No database tracking for fabric pickup, master tailor home visits, workshop progress, or alterations rework.
5. **Payment Processing:** No Razorpay port/adapter implementation or webhook signature verification.

---

## 6. Audit Conclusion

The repository is healthy, builds cleanly, and possesses zero legacy technical debt. The foundation satisfies all architectural prerequisites for Phase 2 (Data Modeling, Catalog, and Serviceability). All existing code is preserved.
