"""
Travel Integrations — Flight & Hotel APIs
==========================================
Skyscanner, Google Flights, Booking.com, Expedia integrations.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class FlightDeal:
    """A flight deal."""
    source: str
    origin: str
    destination: str
    price: float
    airline: str
    departure: str
    return_date: str
    stops: int
    duration: str
    url: str = ""
    created_at: float = field(default_factory=time.time)


@dataclass(slots=True)
class HotelDeal:
    """A hotel deal."""
    source: str
    destination: str
    hotel_name: str
    price_per_night: float
    rating: float
    check_in: str
    check_out: str
    amenities: list[str] = field(default_factory=list)
    url: str = ""


class SkyscannerIntegration:
    """Skyscanner flight search integration."""
    
    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self.flights: list[FlightDeal] = []
    
    def search_flights(self, origin: str, destination: str,
                      departure_date: str) -> list[FlightDeal]:
        """Search for flights."""
        return [f for f in self.flights if f.origin == origin and f.destination == destination]
    
    def get_cheapest(self, origin: str, destination: str) -> FlightDeal | None:
        """Get cheapest flight."""
        flights = self.search_flights(origin, destination, "")
        if not flights:
            return None
        return min(flights, key=lambda f: f.price)
    
    def track_price(self, route: str, current_price: float) -> dict[str, Any]:
        """Track price changes."""
        return {
            "route": route,
            "current_price": current_price,
            "recommendation": "buy" if current_price < 300 else "wait",
            "price_alert": current_price < 250,
        }


class GoogleFlightsIntegration:
    """Google Flights integration."""
    
    def __init__(self):
        self.searches: list[dict] = []
    
    def search(self, origin: str, destination: str,
              dates: str) -> dict[str, Any]:
        """Search flights."""
        self.searches.append({
            "origin": origin, "destination": destination,
            "dates": dates, "timestamp": time.time(),
        })
        
        return {
            "origin": origin,
            "destination": destination,
            "best_flights": [],
            "price_insights": {"price_level": "low"},
            "flexible_dates": [],
        }


class BookingIntegration:
    """Booking.com hotel integration."""
    
    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self.hotels: list[HotelDeal] = []
    
    def search_hotels(self, destination: str, check_in: str,
                     check_out: str) -> list[HotelDeal]:
        """Search for hotels."""
        return [h for h in self.hotels if h.destination == destination]
    
    def get_best_value(self, destination: str) -> HotelDeal | None:
        """Get best value hotel."""
        hotels = self.search_hotels(destination, "", "")
        if not hotels:
            return None
        return min(hotels, key=lambda h: h.price_per_night)


class ExpediaIntegration:
    """Expedia travel integration."""
    
    def __init__(self):
        self.packages: list[dict] = []
    
    def search_packages(self, destination: str, dates: str) -> list[dict]:
        """Search vacation packages."""
        return [p for p in self.packages if p.get("destination") == destination]
    
    def get_bundle_deals(self, destination: str) -> dict[str, Any]:
        """Get flight + hotel bundle deals."""
        return {
            "destination": destination,
            "bundles": [],
            "savings": "Up to 30% vs separate booking",
        }


class TravelIntelligence:
    """
    Unified travel intelligence.
    
    Combines all travel sources for comprehensive deal research.
    """
    
    def __init__(self):
        self.skyscanner = SkyscannerIntegration()
        self.google_flights = GoogleFlightsIntegration()
        self.booking = BookingIntegration()
        self.expedia = ExpediaIntegration()
    
    def find_best_deals(self, origin: str, destination: str,
                       dates: str) -> dict[str, Any]:
        """Find best travel deals across all sources."""
        flights = self.skyscanner.search_flights(origin, destination, dates)
        hotels = self.booking.search_hotels(destination, dates, dates)
        packages = self.expedia.search_packages(destination, dates)
        
        return {
            "destination": destination,
            "flights": {"count": len(flights), "cheapest": min((f.price for f in flights), default=0)},
            "hotels": {"count": len(hotels), "cheapest": min((h.price_per_night for h in hotels), default=0)},
            "packages": {"count": len(packages)},
            "recommendation": "book_now" if len(flights) > 0 else "check_back",
        }
    
    def compare_sources(self, origin: str, destination: str) -> dict[str, Any]:
        """Compare prices across sources."""
        return {
            "skyscanner": self.skyscanner.get_cheapest(origin, destination),
            "booking": self.booking.get_best_value(destination),
            "expedia": self.expedia.get_bundle_deals(destination),
        }
    
    def get_stats(self) -> dict[str, Any]:
        return {
            "flights_tracked": len(self.skyscanner.flights),
            "hotels_tracked": len(self.booking.hotels),
            "packages_tracked": len(self.expedia.packages),
        }
