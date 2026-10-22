"""
Geocoding and travel-time estimation provider ports and adapters (ADR-0004).

Provides an abstract interface for location lookups and ETA calculations,
with explicit fallback handling so live locations or ETAs are never invented
when external map providers are unavailable.
"""

from __future__ import annotations

import math
from typing import Protocol, runtime_checkable
from pydantic import BaseModel, Field


class Coordinates(BaseModel):
    """Geographic coordinate pair."""
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)


class GeocodeResult(BaseModel):
    """Normalized geocoding response."""
    formatted_address: str
    latitude: float
    longitude: float
    city: str = "Bengaluru"
    state: str = "Karnataka"
    pincode: str | None = None
    is_fallback: bool = False
    provider_name: str = "default"
    fallback_message: str | None = None


class TravelEstimate(BaseModel):
    """
    Travel time and distance calculation result.

    If an external provider is unreachable, ``is_fallback`` is set to True
    and a clear explanatory notice is attached.
    """
    distance_km: float
    duration_minutes: int
    is_fallback: bool = False
    provider_name: str
    fallback_message: str | None = None


@runtime_checkable
class GeoRoutingPort(Protocol):
    """Port for geocoding and travel estimation."""

    async def geocode(self, address: str) -> GeocodeResult:
        """Resolve a street address to coordinates."""
        ...

    async def calculate_travel_estimate(
        self, origin: Coordinates, destination: Coordinates
    ) -> TravelEstimate:
        """Estimate distance and travel duration between two points."""
        ...


def haversine_distance_km(coord1: Coordinates, coord2: Coordinates) -> float:
    """Calculate the great-circle distance between two points in kilometers."""
    r = 6371.0  # Earth's radius in km

    lat1_rad = math.radians(coord1.latitude)
    lat2_rad = math.radians(coord2.latitude)
    dlat = math.radians(coord2.latitude - coord1.latitude)
    dlon = math.radians(coord2.longitude - coord1.longitude)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


class HaversineFallbackGeoAdapter:
    """
    Fallback implementation using Haversine calculation and standard urban driving speeds.

    Explicitly flags ``is_fallback = True`` so user interfaces can inform the customer
    that live traffic is unavailable and an estimated standard arrival time is displayed.
    """

    def __init__(self, avg_urban_speed_kmh: float = 20.0, prep_buffer_mins: int = 10) -> None:
        self.avg_speed_kmh = avg_urban_speed_kmh
        self.prep_buffer_mins = prep_buffer_mins

    async def geocode(self, address: str) -> GeocodeResult:
        # Standard fallback coordinates (e.g., Bengaluru central hub)
        return GeocodeResult(
            formatted_address=address,
            latitude=12.9716,
            longitude=77.5946,
            city="Bengaluru",
            state="Karnataka",
            pincode="560001",
            is_fallback=True,
            provider_name="HaversineFallback",
            fallback_message="Live geocoding provider offline; approximate city center used.",
        )

    async def calculate_travel_estimate(
        self, origin: Coordinates, destination: Coordinates
    ) -> TravelEstimate:
        straight_km = haversine_distance_km(origin, destination)
        # Indian urban routing multiplier (roads are ~1.35x straight-line distance)
        road_distance_km = round(straight_km * 1.35, 1)
        travel_mins = int(math.ceil((road_distance_km / self.avg_speed_kmh) * 60))
        total_arrival_minutes = max(15, travel_mins + self.prep_buffer_mins)

        return TravelEstimate(
            distance_km=road_distance_km,
            duration_minutes=total_arrival_minutes,
            is_fallback=True,
            provider_name="HaversineFallback",
            fallback_message=(
                "Live map provider unavailable. Displaying estimated arrival based on "
                "standard city transit buffer (~20 km/h + 10 min kit prep)."
            ),
        )


class MockGoogleMapsAdapter:
    """
    Simulated live Google Maps / MapmyIndia adapter with realistic routing and simulated outage mode.
    """

    def __init__(self, simulate_outage: bool = False) -> None:
        self.simulate_outage = simulate_outage
        self._fallback_adapter = HaversineFallbackGeoAdapter()

    async def geocode(self, address: str) -> GeocodeResult:
        if self.simulate_outage:
            fallback = await self._fallback_adapter.geocode(address)
            fallback.fallback_message = "Google Maps API unreachable; fallback geocoding engaged."
            return fallback

        # Deterministic simulation based on known localities
        known_localities: dict[str, tuple[float, float, str]] = {
            "koramangala": (12.9352, 77.6245, "560034"),
            "indiranagar": (12.9784, 77.6408, "560038"),
            "hsr": (12.9121, 77.6446, "560102"),
            "whitefield": (12.9698, 77.7500, "560066"),
            "jayanagar": (12.9308, 77.5838, "560041"),
        }
        lower_addr = address.lower()
        lat, lng, pin = (12.9716, 77.5946, "560001")
        for key, val in known_localities.items():
            if key in lower_addr:
                lat, lng, pin = val
                break

        return GeocodeResult(
            formatted_address=address.strip(),
            latitude=lat,
            longitude=lng,
            city="Bengaluru",
            state="Karnataka",
            pincode=pin,
            is_fallback=False,
            provider_name="GoogleMapsMatrix",
        )

    async def calculate_travel_estimate(
        self, origin: Coordinates, destination: Coordinates
    ) -> TravelEstimate:
        if self.simulate_outage:
            fallback = await self._fallback_adapter.calculate_travel_estimate(origin, destination)
            fallback.fallback_message = (
                "Live routing provider unreachable; fallback estimate active."
            )
            return fallback

        straight_km = haversine_distance_km(origin, destination)
        road_distance_km = round(straight_km * 1.3, 1)
        # 22 km/h average traffic speed + 8 min prep
        travel_mins = int(math.ceil((road_distance_km / 22.0) * 60)) + 8

        return TravelEstimate(
            distance_km=road_distance_km,
            duration_minutes=max(15, travel_mins),
            is_fallback=False,
            provider_name="GoogleMapsMatrix",
        )


_geo_provider_instance: GeoRoutingPort | None = None


def get_geo_provider() -> GeoRoutingPort:
    """Dependency injection factory for geocoding and travel estimate provider."""
    global _geo_provider_instance
    if _geo_provider_instance is None:
        _geo_provider_instance = MockGoogleMapsAdapter()
    return _geo_provider_instance


def set_geo_provider(provider: GeoRoutingPort) -> None:
    """Override provider (for testing or switching adapters)."""
    global _geo_provider_instance
    _geo_provider_instance = provider
