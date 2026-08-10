"""Honolulu-origin aware search + sample inventory when APIs absent."""
from __future__ import annotations
import random
from .scorer import Deal

class DealSearcher:
    def search(self, destination: str, budget: float = 0, origin: str = "HNL") -> list[Deal]:
        origin = (origin or "HNL").upper()
        deals: list[Deal] = []
        deals.extend(self.search_flights(destination, budget, origin, 1))
        deals.extend(self.search_hotels(destination, budget, 4, 1))
        return deals

    def search_flights(self, destination: str, budget: float, origin: str, travelers: int) -> list[Deal]:
        deals: list[Deal] = []
        deals.extend(self._samples_flights(destination, budget, origin, travelers))
        return deals

    def search_hotels(self, destination: str, budget: float, nights: int, travelers: int) -> list[Deal]:
        deals: list[Deal] = []
        deals.extend(self._samples_hotels(destination, budget, nights, travelers))
        return deals

    def _samples_flights(self, destination: str, budget: float, origin: str, travelers: int) -> list[Deal]:
        dest = (destination or "TYO").upper()[:3]
        base = 450 if dest in {"LAX", "SFO", "SEA"} else 780 if dest in {"TYO", "NRT", "HND"} else 620
        if budget and budget < 900:
            base = min(base, budget * 0.55)
        out = []
        carriers = ["Hawaiian", "Japan Airlines", "United", "Delta", "ANA"]
        for i, carrier in enumerate(carriers[:4]):
            unit = round(base * random.uniform(0.72, 1.18), 2)
            price = round(unit * max(1, travelers), 2)
            rack = round(price * random.uniform(1.08, 1.35), 2)
            out.append(Deal(
                id=f"flt-{dest}-{i}",
                title=f"{carrier} {origin}→{dest}",
                price=price,
                original_price=rack,
                source=carrier,
                kind="flight",
                dates="flexible sample",
                url="",
                meta={"origin": origin, "destination": dest, "travelers": travelers},
            ))
        return out

    def _samples_hotels(self, destination: str, budget: float, nights: int, travelers: int) -> list[Deal]:
        dest = (destination or "TYO").upper()[:3]
        nights = max(1, nights)
        nightly = 95 if dest in {"LAX", "SFO"} else 140 if dest in {"TYO", "NRT", "HND"} else 110
        out = []
        names = ["City Center Inn", "Harbor View Hotel", "Station Boutique", "Garden Stay"]
        for i, name in enumerate(names):
            n = round(nightly * random.uniform(0.75, 1.25), 2)
            price = round(n * nights, 2)
            rack = round(price * random.uniform(1.1, 1.4), 2)
            out.append(Deal(
                id=f"htl-{dest}-{i}",
                title=f"{name} ({dest})",
                price=price,
                original_price=rack,
                source="sample-hotel",
                kind="hotel",
                dates=f"{nights} nights",
                url="",
                meta={"nights": nights, "travelers": travelers, "destination": dest},
            ))
        return out
