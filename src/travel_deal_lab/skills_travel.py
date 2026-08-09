"""
Travel Skills — Deal Intelligence
==================================
Specialized skills for travel deal research.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "mermicorn-commerce-ai" / "src"))
from commerce_ai.skills import MermicornSkills


class TravelSkills:
    """
    Specialized travel deal skills.
    
    Provides:
    - Price tracking
    - Deal scoring
    - Destination intelligence
    - Booking optimization
    - Alert system
    """
    
    def __init__(self, storage_dir: str = "./travel_data"):
        self.skills = MermicornSkills(storage_dir)
        self.deals: dict[str, dict] = {}
        self.price_history: dict[str, list] = {}
        self.alerts: list[dict] = []
    
    def add_deal(self, deal_id: str, destination: str, price: float,
                dates: str, source: str = "") -> dict[str, Any]:
        """Add a travel deal."""
        deal = {
            "id": deal_id, "destination": destination, "price": price,
            "dates": dates, "source": source, "added": time.time(),
        }
        self.deals[deal_id] = deal
        
        # Track price
        key = f"travel:{destination}"
        self.skills.data.add_point(key, price, source)
        
        if destination not in self.price_history:
            self.price_history[destination] = []
        self.price_history[destination].append(deal)
        
        return deal
    
    def score_deal(self, destination: str, price: float) -> dict[str, Any]:
        """Score a deal against history."""
        key = f"travel:{destination}"
        summary = self.skills.data.summary(key)
        
        if summary.get("count", 0) < 2:
            return {"score": 50, "rating": "new", "reasoning": "First deal for this destination"}
        
        avg = summary["mean"]
        min_price = summary["min"]
        
        score = 100
        if price < min_price:
            score = 100
        elif price < avg * 0.8:
            score = 90
        elif price < avg:
            score = 75
        elif price < avg * 1.2:
            score = 50
        else:
            score = 25
        
        return {
            "score": score,
            "rating": "excellent" if score >= 90 else "good" if score >= 75 else "fair" if score >= 50 else "poor",
            "vs_average": f"{(price - avg) / avg * 100:+.1f}%",
            "vs_lowest": f"{(price - min_price) / min_price * 100:+.1f}%",
            "average_price": avg,
            "lowest_price": min_price,
        }
    
    def set_alert(self, destination: str, target_price: float) -> None:
        """Set price alert."""
        self.alerts.append({
            "destination": destination, "target_price": target_price,
            "created": time.time(), "triggered": False,
        })
    
    def check_alerts(self, current_deals: dict[str, float]) -> list[dict]:
        """Check for triggered alerts."""
        triggered = []
        for alert in self.alerts:
            dest = alert["destination"]
            if dest in current_deals and current_deals[dest] <= alert["target_price"]:
                triggered.append({
                    **alert,
                    "current_price": current_deals[dest],
                    "savings": alert["target_price"] - current_deals[dest],
                })
        return triggered
    
    def destination_intelligence(self, destination: str) -> dict[str, Any]:
        """Get intelligence on a destination."""
        price_data = self.skills.data.summary(f"travel:{destination}")
        deals = self.price_history.get(destination, [])
        
        return {
            "destination": destination,
            "price_data": price_data,
            "recent_deals": deals[-5:],
            "best_time_to_book": self._best_time(deals),
            "recommendation": self._recommend(price_data),
        }
    
    def _best_time(self, deals: list) -> str:
        """Determine best booking time."""
        if not deals:
            return "insufficient_data"
        return "book_now" if deals[-1].get("price", 0) < 300 else "wait_for_deal"
    
    def _recommend(self, price_data: dict) -> str:
        """Generate recommendation."""
        if price_data.get("count", 0) < 2:
            return "Track prices to build intelligence"
        if price_data.get("trend") == "falling":
            return "Prices dropping — wait for better deal"
        elif price_data.get("trend") == "rising":
            return "Prices rising — book soon"
        return "Prices stable — book when ready"
    
    def get_stats(self) -> dict[str, Any]:
        return {
            "skills": self.skills.get_stats(),
            "deals_tracked": len(self.deals),
            "destinations": len(self.price_history),
            "alerts_active": sum(1 for a in self.alerts if not a["triggered"]),
        }
