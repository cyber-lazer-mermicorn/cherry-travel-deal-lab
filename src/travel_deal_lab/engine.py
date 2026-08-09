"""Cherry Travel Deal Lab — Deal Scanner & Comparison Engine."""

from __future__ import annotations
import hashlib, json, time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class Deal:
    destination: str
    price: float
    currency: str = "USD"
    dates: str = ""
    source: str = ""
    url: str = ""
    tags: list[str] = field(default_factory=list)
    score: float = 0.0
    created_at: float = field(default_factory=time.time)

    @property
    def id(self) -> str:
        return hashlib.sha256(f"{self.destination}:{self.price}:{self.dates}".encode()).hexdigest()[:12]

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "destination": self.destination, "price": self.price,
                "dates": self.dates, "source": self.source, "tags": self.tags, "score": self.score}


class TravelDealEngine:
    """Scan, score, and compare travel deals."""

    def __init__(self, output_dir: str = "./output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.deals: list[Deal] = []

    def add_deal(self, destination: str, price: float, dates: str = "", source: str = "", tags: list[str] | None = None) -> Deal:
        deal = Deal(destination=destination, price=price, dates=dates, source=source, tags=tags or [])
        deal.score = self._score(deal)
        self.deals.append(deal)
        return deal

    def _score(self, deal: Deal) -> float:
        score = 50.0
        if deal.price < 200: score += 20
        elif deal.price < 400: score += 10
        if "HOT" in deal.tags: score += 15
        if "NEW" in deal.tags: score += 10
        return min(score, 100.0)

    def top_deals(self, n: int = 5) -> list[Deal]:
        return sorted(self.deals, key=lambda d: d.score, reverse=True)[:n]

    def export(self) -> str:
        data = [d.to_dict() for d in self.deals]
        path = self.output_dir / "deals.json"
        path.write_text(json.dumps(data, indent=2))
        return str(path)

    def get_stats(self) -> dict[str, Any]:
        return {"total": len(self.deals), "avg_price": sum(d.price for d in self.deals) / max(len(self.deals), 1),
                "top_score": max((d.score for d in self.deals), default=0)}
