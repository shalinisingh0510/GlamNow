# GlamNow (ग्लैमनाऊ)

> **Quick Commerce for At-Home Services & Doorstep Tailoring in India**  
> Luxury beauty, grooming, spa & bespoke custom tailoring delivered in 15–30 minutes across eligible urban zones.

---

## 🌟 Overview

GlamNow is a production-minded marketplace application built specifically for the Indian market, addressing:
- **Instant At-Home Salon & Spa:** On-demand booking of verified stylists and aestheticians arriving in 15–30 minutes with single-use, sterile kits.
- **Multi-Tier Transparent Pricing:** Comparison across **Basic**, **Standard**, and **Premium** tiers with explicit brand inclusions and duration.
- **Specific Professional Selection:** Direct choice of professionals based on real reviews, rating, portfolio, pricing snapshot, and live arrival ETA.
- **Doorstep Tailoring & Garment Care:** Custom blouse/kurti tailoring, saree draping, pico-fall, and alterations with home measurement visits and doorstep fabric pickup.
- **Extensible Modular Architecture:** Category pluggability enabling future service expansion without refactoring core booking and payment pipelines.

---

## 🏛️ System Architecture

The project is structured as a monorepo housing decoupled frontend and backend applications:

```text
GlamNow/
├── frontend/               # Next.js 16 App Router (React 19, Tailwind v4, TanStack Query)
│   ├── src/
│   │   ├── app/            # App router pages, layouts, and global design tokens
│   │   ├── components/ui/  # Reusable primitives (Button, Card, Badge, Input)
│   │   ├── features/       # Feature domains (catalog, discovery, booking, tailoring)
│   │   └── lib/api/        # Typed API client and TanStack Query provider
├── backend/                # FastAPI application (Python 3.14, Pydantic v2, uv, SQLAlchemy)
│   ├── app/
│   │   ├── api/v1/         # Versioned REST endpoints (health, catalog, bookings)
│   │   ├── core/           # Config, structured logging, middleware, typed errors
│   │   ├── modules/        # Domain modules (catalog, availability, tailoring, etc.)
│   │   └── integrations/   # Provider ports & adapters (payments, maps, SMS)
│   └── tests/              # Pytest test suite (unit and integration tests)
├── docs/                   # Architecture decision records and implementation specs
├── compose.dev.yml         # Local Postgres & Redis development stack
└── .env.example            # Canonical environment variable references
```

---

## 🚀 Getting Started

### Prerequisites
- **Node.js**: v20 or later
- **Python**: 3.12+ (tested on Python 3.14)
- **uv**: Fast Python package manager (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- **Docker / Podman** (optional, for local Postgres & Redis)

---

### Running the Backend

```bash
cd backend

# Create virtualenv and install dependencies
uv sync

# Run tests with coverage
uv run pytest tests/ -v

# Start development server
uv run uvicorn app.main:app --reload --port 8000
```

The OpenAPI documentation is accessible at `http://localhost:8000/docs`.  
Health check endpoint: `http://localhost:8000/api/v1/health`.

---

### Running the Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run type check and linter
npm run lint

# Build production bundle
npm run build

# Start Next.js development server
npm run dev
```

Visit `http://localhost:3000` in your browser.

---

## 🛡️ Architecture Decisions (ADRs)

Key architectural choices documented under [docs/architecture/](docs/architecture/):
- **ADR-0001**: Separate Next.js frontend and FastAPI backend in one repository.
- **ADR-0002**: Modular monolith with domain-owned persistence access.
- **ADR-0003**: Versioned, effective-dated catalog and immutable booking price snapshots.

---

## 📄 License

Proprietary © 2026 GlamNow Technologies Pvt. Ltd. All rights reserved.
