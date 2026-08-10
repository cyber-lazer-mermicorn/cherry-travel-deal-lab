"""Deal + trip scoring with budget-fit and total-cost awareness."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass
class Deal:
    source: str
    title: str
    price: float
    kind: str = "flight"
    original_price: float = 0.0
    dates: str = ""
    url: str = ""
    destination: str = ""
    origin: str = "HNL"
    nights: int = 0
    travelers: int = 1
    meta: dict = field(default_factory=dict)
    id: str = ""

    @property
    def discount_pct(self) -> float:
        if self.original_price and self.original_price > 0:
            return round((1 - self.price / self.original_price) * 100, 1)
        return 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source": self.source,
            "title": self.title,
            "destination": self.destination,
            "origin": self.origin,
            "kind": self.kind,
            "price": self.price,
            "original_price": self.original_price,
            "discount_pct": self.discount_pct,
            "dates": self.dates,
            "url": self.url,
            "nights": self.nights,
            "travelers": self.travelers,
            "meta": self.meta,
        }

@dataclass
class DealScore:
    score: int
    verdict: str
    reasoning: str
    confidence: float = 0.7
    provider: str = "heuristic"
    latency_ms: float = 0.0
    budget_fit: str = "unknown"

    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "verdict": self.verdict,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "provider": self.provider,
            "latency_ms": self.latency_ms,
            "budget_fit": self.budget_fit,
        }

class DealScorer:
    def __init__(self) -> None:
        self.active_providers = [{"name": "heuristic"}]

    def _budget_fit(self, price: float, budget: float) -> str:
        if not budget or budget <= 0:
            return "no_budget"
        ratio = price / budget
        if ratio <= 0.85:
            return "under"
        if ratio <= 1.0:
            return "fits"
        if ratio <= 1.15:
            return "tight"
        return "over"

    def score(self, deal: Deal, budget: float = 0) -> DealScore:
        score = 50
        if deal.discount_pct >= 20:
            score += 20
        elif deal.discount_pct >= 10:
            score += 10
        fit = self._budget_fit(deal.price, budget)
        if fit == "under":
            score += 15
        elif fit == "fits":
            score += 10
        elif fit == "over":
            score -= 15
        score = max(0, min(100, score))
        verdict = "Strong" if score >= 75 else "Good" if score >= 60 else "Fair" if score >= 45 else "Weak"
        return DealScore(
            score=score,
            verdict=verdict,
            reasoning=f"{deal.kind} · disc {deal.discount_pct}% · {fit}",
            budget_fit=fit,
        )

    def score_trip(self, total: float, budget: float, savings_pct: float, components: int) -> DealScore:
        fit = self._budget_fit(total, budget)
        score = 45
        if savings_pct >= 25:
            score += 25
        elif savings_pct >= 15:
            score += 15
        elif savings_pct >= 8:
            score += 8
        if fit == "under":
            score += 20
        elif fit == "fits":
            score += 12
        elif fit == "tight":
            score += 4
        elif fit == "over":
            score -= 20
        score += min(10, components * 3)
        score = max(0, min(100, score))
        verdict = "Strong" if score >= 75 else "Good" if score >= 60 else "Fair" if score >= 45 else "Weak"
        return DealScore(
            score=score,
            verdict=verdict,
            reasoning=f"trip total ${total:.0f} · save {savings_pct}% · {fit}",
            budget_fit=fit,
        )
