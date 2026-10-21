# GlamNow Target Architecture Specification

**Document Version:** 1.0.0  
**Status:** Approved  
**Last Updated:** October 21, 2026  

---

## 1. System Vision & Topology

GlamNow is engineered as a high-throughput, extensible Indian marketplace platform for quick-commerce at-home beauty, grooming, spa, and bespoke custom tailoring. 

The architecture balances two critical priorities:
1. **Low Latency & High Responsiveness:** 15–30 minute dispatch estimates, dynamic tier comparison, and immediate booking confirmation under mobile network constraints.
2. **Strict Domain Integrity & Auditability:** Versioned service catalogs, immutable booking price snapshots, and multi-step tailoring fulfillment state machines.

```mermaid
graph TD
    User([Customer Web / Mobile Browser]) -->|HTTPS / WSS| CDN[Edge CDN / Next.js Frontend]
    Admin([Operations / Dispatch Admin]) -->|HTTPS| CDN
    Pro([Professional / Tailor App]) -->|HTTPS| CDN

    subgraph Frontend [Next.js 16 App Router]
        UI[Tailwind v4 UI Components]
        State[TanStack Query Server State]
        Client[Typed API Client]
    end

    CDN --> Frontend
    Client -->|REST /api/v1/| Gateway[FastAPI Application Gateway]

    subgraph Backend [FastAPI Modular Monolith]
        MW[Request ID / Correlation Middleware]
        Auth[JWT & RBAC Security Layer]
        
        subgraph Domains [Bounded Domain Modules]
            Cat[Catalog & Tier Versioning]
            Serv[Serviceability & Geo]
            Avail[Availability & Dispatch]
            Book[Booking & Price Snapshots]
            Tail[Tailoring & Alteration Studio]
            Pay[Payments & Ledger]
            Rev[Reviews & Ratings]
            Ops[Operations & Support]
        end

        subgraph Ports [Integration Ports & Adapters]
            PayPort[PaymentGatewayPort] --> Razorpay[(Razorpay Adapter)]
            GeoPort[GeocodingPort] --> GoogleMaps[(Google Maps / OSM Adapter)]
            MsgPort[NotificationPort] --> SMS[(SMS / WhatsApp Adapter)]
            StoragePort[StoragePort] --> S3[(Encrypted S3 / R2 Adapter)]
        end
    end

    Gateway --> MW --> Auth --> Domains
    Domains --> Ports

    Domains -->|Async Engine| DB[(PostgreSQL 16 Primary)]
    Domains -->|Locks & Cache| Cache[(Redis 7 Cluster)]
```

---

## 2. Bounded Contexts & Domain Modules

The backend operates as a **Modular Monolith** (`backend/app/modules/`) where each module encapsulates its database models, schemas, repositories, and domain services. Cross-module database writes are strictly prohibited; inter-module communication occurs via explicit service interfaces or asynchronous domain events.

| Module | Core Responsibility | Key Invariants |
|:---|:---|:---|
| `catalog` | Categories, services, tiers (Basic, Standard, Premium), duration rules, and effective-dated pricing rules. | Historic versions are immutable. Catalog updates write new version records. |
| `serviceability` | Operating cities, geo-fenced delivery polygons, PIN code mappings, and travel time buffers. | Quick-booking is disabled for addresses outside active polygon boundaries. |
| `professionals` | Profiles, onboarding verification, skills, tier qualifications, and equipment kit status. | Unverified pros or expired background checks cannot be assigned to customer bookings. |
| `availability` | Working hours, slot generation, travel-time buffers, and real-time dispatch availability. | Buffer intervals (15–30 mins) prevent overlapping commitments. |
| `bookings` | Customer reservations, slot holds, pricing calculation, immutable snapshot generation, and order lifecycle. | Holds expire in 10 minutes without payment. Double booking impossible due to exclusion constraints. |
| `tailoring` | Garment specifications, measurement profiles, doorstep fabric collection tasks, workshop jobs, and alteration rework. | Individual garments track discrete workshop states. Measurements are field-encrypted. |
| `payments` | Gateway integrations (Razorpay), webhook signature validation, idempotency, refund calculation, and settlement records. | Zero charge execution without an active booking hold and valid idempotency key. |
| `reviews` | Customer ratings, verified review validation, and professional aggregate score recalculation. | Only customers with `COMPLETED` bookings can submit verified reviews. |
| `support` | Booking disputes, cancellation escalations, and satisfaction rework requests. | Rework tickets link directly to the originating order snapshot. |

---

## 3. Data Model & Entity Relationship Architecture

```mermaid
erDiagram
    SERVICE_CATEGORY ||--o{ SERVICE_TYPE : contains
    SERVICE_TYPE ||--o{ SERVICE_TIER_VERSION : defines
    SERVICE_TIER_VERSION ||--o{ SERVICE_ADD_ON : offers
    
    CUSTOMER ||--o{ BOOKING : places
    CUSTOMER ||--o{ MEASUREMENT_PROFILE : saves
    PROFESSIONAL ||--o{ BOOKING : fulfills
    
    BOOKING ||--|| BOOKING_PRICE_SNAPSHOT : embeds
    BOOKING ||--o{ PAYMENT_TRANSACTION : settles
    BOOKING ||--o{ REVIEW : receives
    
    BOOKING ||--o| TAILORING_ORDER : specializes
    TAILORING_ORDER ||--o{ GARMENT_ITEM : includes
    GARMENT_ITEM ||--o{ WORKSHOP_JOB : undergoes
```

### 3.1 Immutable Booking Price Snapshot
To prevent pricing discrepancies, every booking stores a JSONB snapshot captured at reservation time:
```json
{
  "service_type_id": "srv_hair_spa",
  "tier": "standard",
  "tier_version_id": "v2_2026_10",
  "base_price_paise": 79900,
  "currency": "INR",
  "inclusions": [
    "Cheryl's Cosmeceuticals hair spa cream",
    "10-minute scalp & shoulder relaxer",
    "Steam & ozone treatment",
    "Blowdry styling"
  ],
  "estimated_duration_minutes": 45,
  "add_ons": [
    { "id": "addon_argan_mask", "title": "Argan Hair Mask", "price_paise": 19900 }
  ],
  "discount_paise": 0,
  "tax_breakdown": {
    "cgst_paise": 8982,
    "sgst_paise": 8982,
    "rate_percent": 18
  },
  "total_paise": 117764,
  "snapshot_timestamp": "2026-10-21T12:00:00Z"
}
```

---

## 4. State Machines

### 4.1 Quick Service Booking Lifecycle

```mermaid
stateDiagram-v2
    [*] --> HOLD_RESERVED: Customer creates reservation (10m TTL)
    HOLD_RESERVED --> EXPIRED: Hold TTL expires
    HOLD_RESERVED --> CONFIRMED: Payment authorized / COD verified
    HOLD_RESERVED --> CANCELLED: Customer cancels before payment
    
    CONFIRMED --> DISPATCHED: Pro assigned & en route (GPS live)
    DISPATCHED --> ARRIVED: Pro at customer doorstep
    ARRIVED --> OTP_VERIFIED: Customer verifies 4-digit start OTP
    OTP_VERIFIED --> IN_PROGRESS: Kit unsealed & service started
    
    IN_PROGRESS --> COMPLETED: Customer verifies completion OTP
    IN_PROGRESS --> ISSUE_RAISED: Customer / Pro reports issue
    
    CONFIRMED --> CANCELLED_REFUNDED: Cancelled within SLA
    COMPLETED --> [*]
    EXPIRED --> [*]
```

### 4.2 Doorstep Tailoring & Garment Care State Machine

Unlike standard home salon visits, custom tailoring spans physical material transport and workshop processing:

```mermaid
stateDiagram-v2
    [*] --> MEASUREMENT_PENDING: Tailoring order placed
    
    state MeasurementMode {
        MEASUREMENT_PENDING --> MASTER_TAILOR_VISIT: Mode = Home Visit
        MEASUREMENT_PENDING --> SAMPLE_GARMENT_PICKUP: Mode = Replicate Existing
        MEASUREMENT_PENDING --> PROFILE_ATTACHED: Mode = Use Saved Measurements
    }
    
    MASTER_TAILOR_VISIT --> MEASUREMENTS_RECORDED
    SAMPLE_GARMENT_PICKUP --> SAMPLE_COLLECTED
    PROFILE_ATTACHED --> FABRIC_PICKUP_ASSIGNED
    MEASUREMENTS_RECORDED --> FABRIC_PICKUP_ASSIGNED
    SAMPLE_COLLECTED --> FABRIC_PICKUP_ASSIGNED
    
    FABRIC_PICKUP_ASSIGNED --> FABRIC_COLLECTED: Rider receives material
    FABRIC_COLLECTED --> WORKSHOP_RECEIVED: Received at central studio
    
    state WorkshopLifecycle {
        WORKSHOP_RECEIVED --> CUTTING
        CUTTING --> STITCHING
        STITCHING --> EMBROIDERY_FINISHING
        EMBROIDERY_FINISHING --> STEAM_PRESS
        STEAM_PRESS --> QC_INSPECTION
    }
    
    QC_INSPECTION --> QC_FAILED: Deviation detected
    QC_FAILED --> STITCHING: Rectification
    QC_INSPECTION --> PACKAGED: QC passed
    
    PACKAGED --> OUT_FOR_DELIVERY: Dispatched to doorstep
    OUT_FOR_DELIVERY --> TRIAL_FITTED: Customer tries on garment
    
    TRIAL_FITTED --> COMPLETED_ACCEPTED: Perfect fit confirmed
    TRIAL_FITTED --> REWORK_REQUESTED: Minor alteration needed
    REWORK_REQUESTED --> WORKSHOP_RECEIVED: Free alteration cycle
    
    COMPLETED_ACCEPTED --> [*]
```

---

## 5. Security & Sensitive Privacy Architecture (DPDP Act Compliance)

1. **Measurement Privacy:**
   - Body measurements (chest, waist, hips, inseam) are categorized as Sensitive Personal Data under India's Digital Personal Data Protection (DPDP) Act 2023.
   - Storage uses field-level symmetric AES-256 encryption. Encryption keys are managed securely and rotated.
   - Tailors only receive decrypted measurements for orders actively assigned to them, restricted to the active work window.
2. **Ephemeral Image Access:**
   - Style reference images and sample garment fitting photos are stored in private object storage.
   - Browsers access images exclusively via short-lived pre-signed URLs (15-minute TTL).
   - Reference images are automatically purged 30 days after order completion unless explicitly saved by the customer.
3. **Idempotency Protection:**
   - All financial and booking mutations require an `Idempotency-Key` header (UUIDv4).
   - Keys are tracked in Redis using atomic `SET NX EX` commands to prevent double-charges and race conditions.

---

## 6. Integration Architecture (Ports & Adapters)

To ensure zero vendor lock-in and testability without external network access, all external providers implement strict abstract interfaces:

```python
# Payment Port Interface
class PaymentGatewayPort(Protocol):
    async def create_payment_order(self, amount_paise: int, currency: str, idempotency_key: str) -> PaymentOrderResult: ...
    async def verify_webhook_signature(self, payload: bytes, signature: str) -> bool: ...
    async def process_refund(self, payment_id: str, amount_paise: int, reason: str) -> RefundResult: ...

# Geocoding & Travel Estimation Port
class GeocodingPort(Protocol):
    async def validate_pincode_serviceability(self, pincode: str) -> ServiceabilityResult: ...
    async def estimate_travel_eta(self, origin_lat: float, origin_lng: float, dest_lat: float, dest_lng: float) -> TravelEtaResult: ...

# Notification Port
class NotificationPort(Protocol):
    async def send_otp(self, mobile_number: str, otp_code: str, context: str) -> bool: ...
    async def send_booking_update(self, mobile_number: str, template_id: str, parameters: dict) -> bool: ...
```

---

## 7. Quality Gates & Non-Negotiable Engineering Standards

- **Zero Untyped Persistence Writes:** No raw dictionaries or unstructured mutations to business records.
- **Client Formula Rejection:** All pricing, tax rates, surge multipliers, and discount deductions are strictly evaluated on the server.
- **Deterministic Testing:** Test suites run locally with zero network I/O; external ports are mocked using faithful memory adapters.
- **Aesthetic Excellence:** Accessible WCAG AA compliant colors, Outfit typography, responsive mobile-first views, and smooth micro-interactions.
