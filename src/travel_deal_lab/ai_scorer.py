"""
Travel Deal AI — Smart Deal Scoring & Analysis
===============================================
Real AI-powered travel research.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent.parent / "mermicorn-commerce-ai" / "src"))
from commerce_ai.ai_core import MermicornAI, AIResult


@dataclass(slots=True)
class DealAnalysis:
    """AI-powered deal analysis."""
    destination: str
    deal_score: int  # 0-100
    value_rating: str  # excellent/good/fair/poor
    best_time_to_book: str
    price_breakdown: dict[str, Any]
    alternatives: list[dict[str, Any]]
    tips: list[str]
    confidence: float
    reasoning: str
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "destination": self.destination, "deal_score": self.deal_score,
            "value_rating": self.value_rating,
            "best_time_to_book": self.best_time_to_book,
            "price_breakdown": self.price_breakdown,
            "alternatives": self.alternatives, "tips": self.tips,
            "confidence": self.confidence, "reasoning": self.reasoning,
        }


class TravelAI:
    """
    AI-powered travel deal research.
    
    Capabilities:
    - Deal quality scoring
    - Price prediction
    - Destination analysis
    - Itinerary generation
    - Deal comparison
    - Booking recommendations
    """
    
    def __init__(self, api_key: str | None = None):
        self.ai = MermicornAI(api_key=api_key)
        self.analyses: list[DealAnalysis] = []
    
    def score_deal(self, deal_data: dict[str, Any]) -> AIResult:
        """Score a travel deal."""
        prompt = f"""Score this travel deal:

{json.dumps(deal_data, indent=2)}

Consider:
- Price vs. typical market rate
- Seasonality
- Flexibility
- Cancellation policy
- Included amenities
- Location quality
- Airline/hotel reputation

Provide JSON with:
- deal_score: 0-100
- value_rating: excellent/good/fair/poor
- price_vs_market: below/above/at market
- best_time_to_book: when to book
- savings_estimate: estimated savings
- risk_factors: things to watch out for
- recommendations: what to do
- confidence: 0-1"""
        
        return self.ai.analyze(prompt, task="research")
    
    def compare_deals(self, deals: list[dict[str, Any]]) -> AIResult:
        """Compare multiple deals."""
        prompt = f"""Compare these travel deals:

{json.dumps(deals, indent=2)}

Provide JSON with:
- best_overall: which is best overall
- best_value: best value for money
- best_luxury: best for luxury
- best_budget: best for budget
- comparison_table: side-by-side comparison
- hidden_fees: any hidden costs
- recommendation: final recommendation
- confidence: 0-1"""
        
        return self.ai.analyze(prompt, task="research")
    
    def analyze_destination(self, destination: str, travel_dates: str = "") -> AIResult:
        """Analyze a destination."""
        prompt = f"""Analyze this travel destination:

Destination: {destination}
{f"Travel dates: {travel_dates}" if travel_dates else ""}

Provide JSON with:
- overview: destination summary
- best_time_to_visit: when to go
- average_costs: typical daily costs
- must_see: top attractions
- hidden_gems: lesser-known spots
- local_tips: insider tips
- safety_notes: safety considerations
- cultural_notes: cultural etiquette
- budget_breakdown: estimated daily budget
- confidence: 0-1"""
        
        return self.ai.analyze(prompt, task="research")
    
    def generate_itinerary(self, destination: str, days: int = 7, budget: str = "moderate") -> AIResult:
        """Generate a travel itinerary."""
        prompt = f"""Generate a {days}-day itinerary for:

Destination: {destination}
Budget: {budget}

Provide JSON with:
- overview: trip summary
- daily_plan: list of days with activities
- accommodations: where to stay
- transportation: how to get around
- dining: restaurant recommendations
- total_estimate: total cost estimate
- packing_list: what to pack
- tips: general tips"""
        
        return self.ai.analyze(prompt, task="research")
    
    def predict_prices(self, destination: str, dates: str = "") -> AIResult:
        """Predict future prices."""
        prompt = f"""Predict price trends for:

Destination: {destination}
{f"Desired dates: {dates}" if dates else ""}

Provide JSON with:
- current_price_range: current prices
- predicted_range: future prices
- best_time_to_book: optimal booking window
- price_trend: rising/stable/falling
- seasonal_patterns: when prices change
- booking_tips: how to get best price
- confidence: 0-1"""
        
        return self.ai.analyze(prompt, task="research")
    
    def get_stats(self) -> dict[str, Any]:
        return {
            "analyses_performed": len(self.analyses),
            "ai_stats": self.ai.get_stats(),
        }
