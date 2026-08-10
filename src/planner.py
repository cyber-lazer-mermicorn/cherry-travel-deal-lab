"""Trip planner — packages flight+hotel into total-cost briefs."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from .scorer import Deal, DealScorer
from .searcher import DealSearcher


@dataclass
class TripPlan:
    origin: str
    destination: str
    budget: float
    nights: int
    travelers: int
    packages: list[dict] = field(default_factory=list)
    flights: list[dict] = field(default_factory=list)
    hotels: list[dict] = field(default_factory=list)
    money: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "origin": self.origin,
            "destination": self.destination,
            "budget": self.budget,
            "nights": self.nights,
            "travelers": self.travelers,
            "packages": self.packages,
            "flights": self.flights,
            "hotels": self.hotels,
            "money": self.money,
        }


class TripPlanner:
    def __init__(self) -> None:
        self.searcher = DealSearcher()
        self.scorer = DealScorer()

    def plan(
        self,
        destination: str,
        budget: float = 0,
        origin: str = "HNL",
        nights: int = 4,
        travelers: int = 1,
        flight_share: float = 0.55,
        include_activities: bool = True,
    ) -> TripPlan:
        nights = max(1, min(30, nights))
        travelers = max(1, min(8, travelers))
        origin = (origin or "HNL").upper()
        flights = self.searcher.search_flights(destination, budget if budget > 0 else 0, origin, travelers)
        hotels = self.searcher.search_hotels(destination, budget if budget > 0 else 0, nights, travelers)
        scored_flights = []
        for d in flights:
            s = self.scorer.score(d, budget)
            scored_flights.append({"deal": d.to_dict(), "score": s.to_dict()})
        scored_flights.sort(key=lambda x: x["score"]["score"], reverse=True)
        scored_hotels = []
        for d in hotels:
            s = self.scorer.score(d, budget)
            scored_hotels.append({"deal": d.to_dict(), "score": s.to_dict()})
        scored_hotels.sort(key=lambda x: x["score"]["score"], reverse=True)
        packages = self._packages(flights, hotels, budget, nights, travelers)
        packages.sort(key=lambda p: p["score"]["score"], reverse=True)
        money = self._money_summary(packages, budget, travelers, nights)
        _ = include_activities
        return TripPlan(
            origin=origin,
            destination=destination,
            budget=budget,
            nights=nights,
            travelers=travelers,
            packages=packages[:6],
            flights=scored_flights[:6],
            hotels=scored_hotels[:6],
            money=money,
        )

    def _packages(self, flights, hotels, budget, nights, travelers):
        if not flights or not hotels:
            return []
        out = []
        for f in flights[:3]:
            for h in hotels[:3]:
                total = round(f.price + h.price, 2)
                rack = round((f.original_price or f.price) + (h.original_price or h.price), 2)
                savings_pct = round((1 - total / rack) * 100, 1) if rack > 0 else 0
                buffer = round(35 * nights * travelers, 2)
                all_in = round(total + buffer, 2)
                trip_score = self.scorer.score_trip(total, budget, savings_pct, 2)
                out.append({
                    "label": f"{f.source} + hotel package",
                    "total": total,
                    "all_in_estimate": all_in,
                    "buffer_food_transit": buffer,
                    "rack_total": rack,
                    "savings_pct": savings_pct,
                    "per_person": round(total / max(1, travelers), 2),
                    "flight": f.to_dict(),
                    "hotel": h.to_dict(),
                    "score": trip_score.to_dict(),
                    "fits_budget": budget <= 0 or total <= budget,
                })
        return out

    def _money_summary(self, packages, budget, travelers, nights):
        if not packages:
            return {"best_total": None, "best_all_in": None, "budget": budget, "headroom": None, "tip": "Widen dates or raise budget slightly for more options."}
        best = min(packages, key=lambda p: p["total"])
        headroom = round(budget - best["total"], 2) if budget else None
        tip = "Strong value — book flexible fare + free-cancel hotel."
        if budget and best["total"] > budget:
            tip = "Over budget on total — trim nights or switch hotel tier."
        elif budget and headroom is not None and headroom > budget * 0.25:
            tip = "Solid discount vs rack — good candidate to lock."
        return {
            "best_total": best["total"],
            "best_all_in": best["all_in_estimate"],
            "best_per_person": best["per_person"],
            "budget": budget,
            "headroom": headroom,
            "nights": nights,
            "travelers": travelers,
            "tip": tip,
            "niche": "Honolulu-origin total-cost trip briefs — not bare fare screenshots.",
        }
