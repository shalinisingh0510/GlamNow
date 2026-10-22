"""
Professional management, discovery engine, and transaction-safe availability slots.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
import uuid

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.integrations.geo import Coordinates, GeoRoutingPort, get_geo_provider
from app.modules.catalog.enums import ServiceTierType
from app.modules.catalog.models import PricingRule, Service, ServiceCategory, ServiceTier
from app.modules.identity.enums import UserRole
from app.modules.identity.models import User
from app.modules.professionals.enums import DayOfWeek, SlotStatus, VerificationStatus
from app.modules.professionals.models import (
    AppointmentSlot,
    ProfessionalBlockedDate,
    ProfessionalPortfolio,
    ProfessionalProfile,
    ProfessionalServiceOffering,
    ProfessionalSkill,
    ProfessionalWorkingHours,
)
from app.modules.professionals.schemas import (
    BlockedDateCreate,
    PortfolioItemCreate,
    ProfessionalCardResponse,
    ProfessionalDetailResponse,
    ProfessionalProfileCreate,
    ProfessionalProfileUpdate,
    ServiceOfferingCreate,
    SlotReservationResponse,
    WorkingHoursItem,
)


def _ensure_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class ProfessionalService:
    """Service layer for professionals, discovery, and availability."""

    def __init__(self, db: AsyncSession, geo_provider: GeoRoutingPort | None = None) -> None:
        self.db = db
        self.geo_provider = geo_provider or get_geo_provider()

    async def get_profile_by_user_id(self, user_id: uuid.UUID) -> ProfessionalProfile | None:
        stmt = (
            select(ProfessionalProfile)
            .where(ProfessionalProfile.user_id == user_id)
            .options(
                selectinload(ProfessionalProfile.user),
                selectinload(ProfessionalProfile.skills),
                selectinload(ProfessionalProfile.service_offerings),
                selectinload(ProfessionalProfile.portfolios),
                selectinload(ProfessionalProfile.working_hours),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_profile_by_id(self, professional_id: uuid.UUID) -> ProfessionalProfile:
        stmt = (
            select(ProfessionalProfile)
            .where(ProfessionalProfile.id == professional_id)
            .options(
                selectinload(ProfessionalProfile.user),
                selectinload(ProfessionalProfile.skills),
                selectinload(ProfessionalProfile.service_offerings),
                selectinload(ProfessionalProfile.portfolios),
                selectinload(ProfessionalProfile.working_hours),
            )
        )
        result = await self.db.execute(stmt)
        profile = result.scalar_one_or_none()
        if not profile:
            raise NotFoundError("Professional", str(professional_id))
        return profile

    async def create_profile(
        self, user_id: uuid.UUID, data: ProfessionalProfileCreate
    ) -> ProfessionalProfile:
        user = await self.db.get(User, user_id)
        if not user:
            raise NotFoundError("User", str(user_id))
        if user.role not in (UserRole.PROFESSIONAL, UserRole.ADMIN):
            raise ForbiddenError("Only users with PROFESSIONAL role can create a professional profile.")

        existing = await self.get_profile_by_user_id(user_id)
        if existing:
            raise ConflictError("A professional profile already exists for this user.")

        profile = ProfessionalProfile(
            user_id=user_id,
            bio=data.bio,
            experience_years=data.experience_years,
            base_zone_name=data.base_zone_name,
            latitude=data.latitude,
            longitude=data.longitude,
            service_radius_km=data.service_radius_km,
            is_accepting_instant_bookings=data.is_accepting_instant_bookings,
            verification_status=VerificationStatus.PENDING,
        )
        self.db.add(profile)
        await self.db.flush()

        # Add initial skills
        for skill_name in data.skills:
            clean_name = skill_name.strip()
            if clean_name:
                self.db.add(ProfessionalSkill(professional_id=profile.id, name=clean_name))

        # Initialize standard working hours (Mon-Sat 09:00 to 19:00 with lunch break 13:00-14:00)
        standard_days = [
            DayOfWeek.MONDAY,
            DayOfWeek.TUESDAY,
            DayOfWeek.WEDNESDAY,
            DayOfWeek.THURSDAY,
            DayOfWeek.FRIDAY,
            DayOfWeek.SATURDAY,
        ]
        for day in DayOfWeek:
            is_working = day in standard_days
            wh = ProfessionalWorkingHours(
                professional_id=profile.id,
                day_of_week=day,
                start_time="09:00",
                end_time="19:00",
                break_start_time="13:00" if is_working else None,
                break_end_time="14:00" if is_working else None,
                is_working=is_working,
            )
            self.db.add(wh)

        await self.db.commit()
        return await self.get_profile_by_id(profile.id)

    async def update_profile(
        self, professional_id: uuid.UUID, actor_id: uuid.UUID, data: ProfessionalProfileUpdate
    ) -> ProfessionalProfile:
        profile = await self.get_profile_by_id(professional_id)
        actor = await self.db.get(User, actor_id)
        if not actor or (actor.id != profile.user_id and actor.role != UserRole.ADMIN):
            raise ForbiddenError("You cannot modify another professional's profile.")

        if data.bio is not None:
            profile.bio = data.bio
        if data.experience_years is not None:
            profile.experience_years = data.experience_years
        if data.base_zone_name is not None:
            profile.base_zone_name = data.base_zone_name
        if data.latitude is not None:
            profile.latitude = data.latitude
        if data.longitude is not None:
            profile.longitude = data.longitude
        if data.service_radius_km is not None:
            profile.service_radius_km = data.service_radius_km
        if data.is_accepting_instant_bookings is not None:
            profile.is_accepting_instant_bookings = data.is_accepting_instant_bookings

        await self.db.commit()
        return await self.get_profile_by_id(profile.id)

    async def update_verification_status(
        self, professional_id: uuid.UUID, status: VerificationStatus, admin_user: User
    ) -> ProfessionalProfile:
        if admin_user.role != UserRole.ADMIN:
            raise ForbiddenError("Only administrators can update professional verification status.")

        profile = await self.get_profile_by_id(professional_id)
        profile.verification_status = status
        await self.db.commit()
        return profile

    async def add_skills(
        self, professional_id: uuid.UUID, skills: list[str], actor_id: uuid.UUID
    ) -> list[str]:
        profile = await self.get_profile_by_id(professional_id)
        actor = await self.db.get(User, actor_id)
        if not actor or (actor.id != profile.user_id and actor.role != UserRole.ADMIN):
            raise ForbiddenError("Unauthorized to modify skills.")

        existing_skills = {s.name.lower() for s in profile.skills}
        for name in skills:
            clean = name.strip()
            if clean and clean.lower() not in existing_skills:
                self.db.add(ProfessionalSkill(professional_id=profile.id, name=clean))
                existing_skills.add(clean.lower())

        await self.db.commit()
        refreshed = await self.get_profile_by_id(professional_id)
        return [s.name for s in refreshed.skills]

    async def set_service_offering(
        self, professional_id: uuid.UUID, offering: ServiceOfferingCreate, actor_id: uuid.UUID
    ) -> ProfessionalServiceOffering:
        profile = await self.get_profile_by_id(professional_id)
        actor = await self.db.get(User, actor_id)
        if not actor or (actor.id != profile.user_id and actor.role != UserRole.ADMIN):
            raise ForbiddenError("Unauthorized to modify offerings.")

        service = await self.db.get(Service, offering.service_id)
        if not service:
            raise NotFoundError("Service", str(offering.service_id))

        stmt = select(ProfessionalServiceOffering).where(
            ProfessionalServiceOffering.professional_id == professional_id,
            ProfessionalServiceOffering.service_id == offering.service_id,
            ProfessionalServiceOffering.tier_type == offering.tier_type,
        )
        existing = (await self.db.execute(stmt)).scalar_one_or_none()
        if existing:
            existing.custom_price_paise = offering.custom_price_paise
            existing.is_active = offering.is_active
            result = existing
        else:
            result = ProfessionalServiceOffering(
                professional_id=professional_id,
                service_id=offering.service_id,
                tier_type=offering.tier_type,
                custom_price_paise=offering.custom_price_paise,
                is_active=offering.is_active,
            )
            self.db.add(result)

        await self.db.commit()
        return result

    async def add_portfolio_item(
        self, professional_id: uuid.UUID, item: PortfolioItemCreate, actor_id: uuid.UUID
    ) -> ProfessionalPortfolio:
        profile = await self.get_profile_by_id(professional_id)
        actor = await self.db.get(User, actor_id)
        if not actor or (actor.id != profile.user_id and actor.role != UserRole.ADMIN):
            raise ForbiddenError("Unauthorized to add portfolio items.")

        portfolio = ProfessionalPortfolio(
            professional_id=professional_id,
            title=item.title,
            description=item.description,
            image_url=item.image_url,
            service_id=item.service_id,
            is_verified=True,
        )
        self.db.add(portfolio)
        await self.db.commit()
        return portfolio

    async def set_working_hours(
        self, professional_id: uuid.UUID, hours: list[WorkingHoursItem], actor_id: uuid.UUID
    ) -> list[ProfessionalWorkingHours]:
        profile = await self.get_profile_by_id(professional_id)
        actor = await self.db.get(User, actor_id)
        if not actor or (actor.id != profile.user_id and actor.role != UserRole.ADMIN):
            raise ForbiddenError("Unauthorized to modify working hours.")

        for item in hours:
            stmt = select(ProfessionalWorkingHours).where(
                ProfessionalWorkingHours.professional_id == professional_id,
                ProfessionalWorkingHours.day_of_week == item.day_of_week,
            )
            existing = (await self.db.execute(stmt)).scalar_one_or_none()
            if existing:
                existing.start_time = item.start_time
                existing.end_time = item.end_time
                existing.break_start_time = item.break_start_time
                existing.break_end_time = item.break_end_time
                existing.is_working = item.is_working
            else:
                self.db.add(
                    ProfessionalWorkingHours(
                        professional_id=professional_id,
                        day_of_week=item.day_of_week,
                        start_time=item.start_time,
                        end_time=item.end_time,
                        break_start_time=item.break_start_time,
                        break_end_time=item.break_end_time,
                        is_working=item.is_working,
                    )
                )

        await self.db.commit()
        refreshed = await self.get_profile_by_id(professional_id)
        return refreshed.working_hours

    async def add_blocked_date(
        self, professional_id: uuid.UUID, data: BlockedDateCreate, actor_id: uuid.UUID
    ) -> ProfessionalBlockedDate:
        profile = await self.get_profile_by_id(professional_id)
        actor = await self.db.get(User, actor_id)
        if not actor or (actor.id != profile.user_id and actor.role != UserRole.ADMIN):
            raise ForbiddenError("Unauthorized to add blocked dates.")

        if data.end_datetime <= data.start_datetime:
            raise ValidationError("End datetime must be strictly after start datetime.")

        blocked = ProfessionalBlockedDate(
            professional_id=professional_id,
            start_datetime=data.start_datetime,
            end_datetime=data.end_datetime,
            reason=data.reason,
        )
        self.db.add(blocked)
        await self.db.commit()
        return blocked

    # ─────────────────────────────────────────────────────────────
    # Availability Slot Generation and Transaction-Safe Reservation
    # ─────────────────────────────────────────────────────────────

    async def get_or_generate_slots_for_date(
        self, professional_id: uuid.UUID, target_date: date, slot_duration_minutes: int = 60
    ) -> list[AppointmentSlot]:
        """
        Calculates and synchronizes appointment slots for a given date.
        Accounts for:
        1. Professional working hours for the day of week.
        2. Breaks (e.g., lunch hour).
        3. Blocked dates (personal leaves).
        4. Preserves already RESERVED or BOOKED slots without duplicate slot creation.
        """
        profile = await self.get_profile_by_id(professional_id)
        weekday_name = target_date.strftime("%A").lower()
        try:
            day_enum = DayOfWeek(weekday_name)
        except ValueError:
            return []

        # Find schedule
        wh = next((h for h in profile.working_hours if h.day_of_week == day_enum), None)
        if not wh or not wh.is_working:
            return []

        # Check blocked dates for the day
        day_start = datetime.combine(target_date, time(0, 0), tzinfo=timezone.utc)
        day_end = datetime.combine(target_date, time(23, 59, 59), tzinfo=timezone.utc)

        blocked_stmt = select(ProfessionalBlockedDate).where(
            ProfessionalBlockedDate.professional_id == professional_id,
            ProfessionalBlockedDate.start_datetime <= day_end,
            ProfessionalBlockedDate.end_datetime >= day_start,
        )
        blocked_periods = (await self.db.execute(blocked_stmt)).scalars().all()

        # Existing slots
        slots_stmt = select(AppointmentSlot).where(
            AppointmentSlot.professional_id == professional_id,
            AppointmentSlot.start_time >= day_start,
            AppointmentSlot.start_time <= day_end,
        )
        existing_slots_dict = {
            s.start_time: s for s in (await self.db.execute(slots_stmt)).scalars().all()
        }

        # Parse shift boundaries
        start_h, start_m = map(int, wh.start_time.split(":"))
        end_h, end_m = map(int, wh.end_time.split(":"))
        shift_start = datetime.combine(target_date, time(start_h, start_m), tzinfo=timezone.utc)
        shift_end = datetime.combine(target_date, time(end_h, end_m), tzinfo=timezone.utc)

        # Parse break boundaries
        break_start = None
        break_end = None
        if wh.break_start_time and wh.break_end_time:
            bh_s, bm_s = map(int, wh.break_start_time.split(":"))
            bh_e, bm_e = map(int, wh.break_end_time.split(":"))
            break_start = datetime.combine(target_date, time(bh_s, bm_s), tzinfo=timezone.utc)
            break_end = datetime.combine(target_date, time(bh_e, bm_e), tzinfo=timezone.utc)

        curr = shift_start
        delta = timedelta(minutes=slot_duration_minutes)
        slots_to_return: list[AppointmentSlot] = []

        now_utc = datetime.now(timezone.utc)

        while curr + delta <= shift_end:
            slot_start = curr
            slot_end = curr + delta
            curr += delta

            # Check if existing slot exists
            if slot_start in existing_slots_dict:
                existing_slot = existing_slots_dict[slot_start]
                # Check for expired reservation
                expires_at = _ensure_utc(existing_slot.reservation_expires_at)
                if (
                    existing_slot.status == SlotStatus.RESERVED
                    and expires_at
                    and expires_at < now_utc
                ):
                    existing_slot.status = SlotStatus.AVAILABLE
                    existing_slot.reserved_by_user_id = None
                    existing_slot.reservation_expires_at = None
                slots_to_return.append(existing_slot)
                continue

            # Determine status based on breaks and blocked dates
            status = SlotStatus.AVAILABLE
            if break_start and break_end and not (slot_end <= break_start or slot_start >= break_end):
                status = SlotStatus.BLOCKED

            for bp in blocked_periods:
                bp_start = _ensure_utc(bp.start_datetime)
                bp_end = _ensure_utc(bp.end_datetime)
                if bp_start and bp_end and not (slot_end <= bp_start or slot_start >= bp_end):
                    status = SlotStatus.BLOCKED
                    break

            new_slot = AppointmentSlot(
                professional_id=professional_id,
                start_time=slot_start,
                end_time=slot_end,
                status=status,
            )
            self.db.add(new_slot)
            slots_to_return.append(new_slot)

        await self.db.commit()
        return sorted(slots_to_return, key=lambda s: s.start_time)

    async def reserve_slot(
        self,
        slot_id: uuid.UUID,
        user_id: uuid.UUID,
        service_id: uuid.UUID | None = None,
        hold_duration_minutes: int = 15,
    ) -> SlotReservationResponse:
        """
        Transaction-safe atomic slot reservation.
        Prevents double-booking via database row locking / concurrency checks.
        """
        # Lock slot row for concurrency protection
        stmt = (
            select(AppointmentSlot)
            .where(AppointmentSlot.id == slot_id)
            .with_for_update()
        )
        result = await self.db.execute(stmt)
        slot = result.scalar_one_or_none()

        if not slot:
            raise NotFoundError("AppointmentSlot", str(slot_id))

        now_utc = datetime.now(timezone.utc)

        # Expire stale reservation if hold window has passed
        slot_expires_at = _ensure_utc(slot.reservation_expires_at)
        if (
            slot.status == SlotStatus.RESERVED
            and slot_expires_at
            and slot_expires_at < now_utc
        ):
            slot.status = SlotStatus.AVAILABLE
            slot.reserved_by_user_id = None
            slot.reservation_expires_at = None

        if slot.status == SlotStatus.BOOKED:
            raise ConflictError("This appointment slot has already been booked by another client.")

        if slot.status == SlotStatus.BLOCKED:
            raise ConflictError("This appointment slot is unavailable due to working schedule or break.")

        if slot.status == SlotStatus.RESERVED:
            if slot.reserved_by_user_id != user_id:
                raise ConflictError(
                    "This appointment slot is currently held by another client. "
                    "Please choose another time slot or try again shortly."
                )

        # Grant reservation lock
        expires_at = now_utc + timedelta(minutes=hold_duration_minutes)
        slot.status = SlotStatus.RESERVED
        slot.reserved_by_user_id = user_id
        slot.reservation_expires_at = expires_at
        slot.service_id = service_id

        await self.db.commit()
        await self.db.refresh(slot)

        return SlotReservationResponse(
            slot_id=slot.id,
            professional_id=slot.professional_id,
            start_time=slot.start_time,
            end_time=slot.end_time,
            status=slot.status,
            reservation_expires_at=expires_at,
            message=f"Slot held for {hold_duration_minutes} minutes.",
        )

    async def release_slot(self, slot_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        stmt = (
            select(AppointmentSlot)
            .where(AppointmentSlot.id == slot_id)
            .with_for_update()
        )
        result = await self.db.execute(stmt)
        slot = result.scalar_one_or_none()
        if not slot:
            return False

        if slot.status == SlotStatus.RESERVED and slot.reserved_by_user_id == user_id:
            slot.status = SlotStatus.AVAILABLE
            slot.reserved_by_user_id = None
            slot.reservation_expires_at = None
            slot.service_id = None
            await self.db.commit()
            return True
        return False

    # ─────────────────────────────────────────────────────────────
    # Professional Discovery Engine with Geo Estimates & Fallbacks
    # ─────────────────────────────────────────────────────────────

    async def discover_professionals(
        self,
        category_slug: str | None = None,
        service_id: uuid.UUID | None = None,
        tier_type: ServiceTierType | None = None,
        skill: str | None = None,
        min_rating: float | None = None,
        max_price_paise: int | None = None,
        customer_lat: float | None = None,
        customer_lng: float | None = None,
        instant_only: bool = False,
        target_date: date | None = None,
    ) -> list[ProfessionalCardResponse]:
        """
        Discover eligible professionals matching filtering criteria,
        augmented with travel time estimates and explicit fallback notices.
        """
        # Fetch active professionals
        stmt = (
            select(ProfessionalProfile)
            .where(ProfessionalProfile.is_active.is_(True))
            .options(
                selectinload(ProfessionalProfile.user),
                selectinload(ProfessionalProfile.skills),
                selectinload(ProfessionalProfile.service_offerings),
                selectinload(ProfessionalProfile.portfolios),
                selectinload(ProfessionalProfile.working_hours),
            )
        )

        if min_rating is not None:
            stmt = stmt.where(ProfessionalProfile.rating >= min_rating)

        if instant_only:
            stmt = stmt.where(ProfessionalProfile.is_accepting_instant_bookings.is_(True))

        profiles = (await self.db.execute(stmt)).scalars().all()

        # If category_slug provided, resolve service IDs in that category
        category_service_ids: set[uuid.UUID] | None = None
        if category_slug:
            cat_stmt = (
                select(ServiceCategory)
                .where(ServiceCategory.slug == category_slug)
                .options(selectinload(ServiceCategory.services))
            )
            cat = (await self.db.execute(cat_stmt)).scalar_one_or_none()
            if cat:
                category_service_ids = {s.id for s in cat.services}
            else:
                return []

        # Load catalog base prices for fallbacks
        base_tier_prices: dict[tuple[uuid.UUID, ServiceTierType], int] = {}
        rule_stmt = (
            select(PricingRule, ServiceTier)
            .join(ServiceTier, PricingRule.tier_id == ServiceTier.id)
            .where(PricingRule.is_active.is_(True))
        )
        for rule, st in (await self.db.execute(rule_stmt)).all():
            if (st.service_id, st.tier) not in base_tier_prices:
                base_tier_prices[(st.service_id, st.tier)] = rule.base_price_paise

        date_for_slots = target_date or date.today()
        customer_coords = (
            Coordinates(latitude=customer_lat, longitude=customer_lng)
            if (customer_lat is not None and customer_lng is not None)
            else None
        )

        matched_cards: list[ProfessionalCardResponse] = []

        for p in profiles:
            # Skill filter
            if skill:
                has_skill = any(skill.lower() in s.name.lower() for s in p.skills)
                if not has_skill:
                    continue

            # Service/Category eligibility
            offerings = [o for o in p.service_offerings if o.is_active]
            if service_id:
                has_service = any(o.service_id == service_id for o in offerings)
                if not has_service:
                    continue
            elif category_service_ids is not None:
                has_cat_service = any(o.service_id in category_service_ids for o in offerings)
                if not has_cat_service:
                    continue

            # Compute effective tier prices for this professional
            tier_prices: dict[str, int] = {}
            for off in offerings:
                if service_id and off.service_id != service_id:
                    continue
                tier_key = off.tier_type.value
                price = off.custom_price_paise or base_tier_prices.get(
                    (off.service_id, off.tier_type), 79900
                )
                # Keep lowest price if multiple services match
                if tier_key not in tier_prices or price < tier_prices[tier_key]:
                    tier_prices[tier_key] = price

            # Default fallback tier prices if none explicitly overridden
            if not tier_prices:
                tier_prices = {
                    ServiceTierType.BASIC.value: 79900,
                    ServiceTierType.STANDARD.value: 129900,
                    ServiceTierType.PREMIUM.value: 199900,
                }

            # Filter by max price if requested
            if max_price_paise is not None:
                check_price = (
                    tier_prices.get(tier_type.value)
                    if tier_type
                    else min(tier_prices.values(), default=0)
                )
                if check_price > max_price_paise:
                    continue

            # Travel & Geo estimation
            distance_km = None
            arrival_mins = None
            is_fallback_loc = False
            fallback_msg = None

            if customer_coords:
                prof_coords = Coordinates(latitude=p.latitude, longitude=p.longitude)
                estimate = await self.geo_provider.calculate_travel_estimate(
                    origin=prof_coords, destination=customer_coords
                )
                distance_km = estimate.distance_km
                arrival_mins = estimate.duration_minutes
                is_fallback_loc = estimate.is_fallback
                fallback_msg = estimate.fallback_message

                # Exclude if professional is outside their service zone radius
                if distance_km > p.service_radius_km:
                    continue

            # Available slots count
            # Query active available slots for this date
            day_start = datetime.combine(date_for_slots, time(0, 0), tzinfo=timezone.utc)
            day_end = datetime.combine(date_for_slots, time(23, 59, 59), tzinfo=timezone.utc)
            avail_stmt = select(AppointmentSlot).where(
                AppointmentSlot.professional_id == p.id,
                AppointmentSlot.status == SlotStatus.AVAILABLE,
                AppointmentSlot.start_time >= day_start,
                AppointmentSlot.start_time <= day_end,
            )
            avail_slots = (await self.db.execute(avail_stmt)).scalars().all()

            matched_cards.append(
                ProfessionalCardResponse(
                    id=p.id,
                    user_id=p.user_id,
                    full_name=p.user.full_name if p.user else "Professional Partner",
                    bio=p.bio,
                    experience_years=p.experience_years,
                    verification_status=p.verification_status,
                    rating=p.rating,
                    review_count=p.review_count,
                    is_accepting_instant_bookings=p.is_accepting_instant_bookings,
                    base_zone_name=p.base_zone_name,
                    distance_km=distance_km,
                    estimated_arrival_minutes=arrival_mins,
                    is_fallback_location=is_fallback_loc,
                    fallback_message=fallback_msg,
                    skills=[s.name for s in p.skills],
                    tier_prices=tier_prices,
                    portfolio_samples=[item.image_url for item in p.portfolios[:4]],
                    available_slots_count=len(avail_slots),
                )
            )

        # Sort nearest first if coordinates provided, else by rating
        if customer_coords:
            matched_cards.sort(key=lambda c: (c.distance_km if c.distance_km is not None else 999))
        else:
            matched_cards.sort(key=lambda c: c.rating, reverse=True)

        return matched_cards
