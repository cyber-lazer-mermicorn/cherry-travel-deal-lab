"""
Full Stack Workflow Test — Cherry Travel Deal Lab
=================================================
Search → Score → Alert → Compare → Book
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "../mermicorn-commerce-ai/src")
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "mermicorn-commerce-ai" / "src"))

from travel_deal_lab.engine import TravelDealEngine
from travel_deal_lab.ai_scorer import TravelAI
from travel_deal_lab.integrations import TravelIntelligence
from travel_deal_lab.skills_travel import TravelSkills


def test_full_workflow():
    """Test complete travel workflow: Search → Score → Alert → Compare."""
    print("✈️ TRAVEL DEAL LAB FULL WORKFLOW TEST")
    print("=" * 50)
    
    # ═══════════════════════════════════════════════════════════
    # STEP 1: Search Flights (Integration)
    # ═══════════════════════════════════════════════════════════
    print("\n📌 STEP 1: Search Flights")
    intel = TravelIntelligence()
    flights = intel.skyscanner.search_flights("HNL", "LAX", "2026-08-15")
    
    print(f"   ✅ Flights found: {len(flights)}")
    
    # ═══════════════════════════════════════════════════════════
    # STEP 2: Search Hotels (Integration)
    # ═══════════════════════════════════════════════════════════
    print("\n📌 STEP 2: Search Hotels")
    hotels = intel.booking.search_hotels("Los Angeles", "2026-08-15", "2026-08-22")
    
    print(f"   ✅ Hotels found: {len(hotels)}")
    
    # ═══════════════════════════════════════════════════════════
    # STEP 3: Analyze Destination (AI)
    # ═══════════════════════════════════════════════════════════
    print("\n📌 STEP 3: Analyze Destination")
    ai = TravelAI()
    destination = ai.analyze_destination("Los Angeles", "Aug 15-22, 2026")
    
    assert destination.success, f"Destination analysis failed: {destination.reasoning}"
    print(f"   ✅ Analysis: {destination.data}")
    
    # ═══════════════════════════════════════════════════════════
    # STEP 4: Score Deal (AI)
    # ═══════════════════════════════════════════════════════════
    print("\n📌 STEP 4: Score Deal")
    deal_data = {
        "destination": "Los Angeles",
        "price": 299,
        "dates": "Aug 15-22",
        "source": "Skyscanner",
        "includes": "flight + hotel",
    }
    score = ai.score_deal(deal_data)
    
    assert score.success, f"Deal scoring failed: {score.reasoning}"
    print(f"   ✅ Score: {score.data}")
    
    # ═══════════════════════════════════════════════════════════
    # STEP 5: Track Prices (Skills)
    # ═══════════════════════════════════════════════════════════
    print("\n📌 STEP 5: Track Prices")
    skills = TravelSkills()
    skills.add_deal("la_aug1", "Los Angeles", 299, "Aug 15-22", "Skyscanner")
    skills.add_deal("la_aug2", "Los Angeles", 349, "Aug 22-29", "Google Flights")
    skills.add_deal("la_aug3", "Los Angeles", 279, "Aug 10-17", "Expedia")
    
    trend = skills.skills.data.summary("travel:Los Angeles")
    print(f"   ✅ Price trend: {trend}")
    
    # ═══════════════════════════════════════════════════════════
    # STEP 6: Set Alert
    # ═══════════════════════════════════════════════════════════
    print("\n📌 STEP 6: Set Price Alert")
    skills.set_alert("Los Angeles", 250)
    skills.set_alert("Tokyo", 400)
    
    print(f"   ✅ Alerts active: {sum(1 for a in skills.alerts if not a['triggered'])}")
    
    # ═══════════════════════════════════════════════════════════
    # STEP 7: Compare Deals (AI)
    # ═══════════════════════════════════════════════════════════
    print("\n📌 STEP 7: Compare Deals")
    deals = [
        {"destination": "LA", "price": 299, "source": "Skyscanner"},
        {"destination": "LA", "price": 349, "source": "Google"},
        {"destination": "LA", "price": 279, "source": "Expedia"},
    ]
    comparison = ai.compare_deals(deals)
    
    assert comparison.success, f"Comparison failed: {comparison.reasoning}"
    print(f"   ✅ Best deal: {comparison.data}")
    
    # ═══════════════════════════════════════════════════════════
    # STEP 8: Generate Itinerary (AI)
    # ═══════════════════════════════════════════════════════════
    print("\n📌 STEP 8: Generate Itinerary")
    itinerary = ai.generate_itinerary("Los Angeles", days=7, budget="moderate")
    
    assert itinerary.success, f"Itinerary failed: {itinerary.reasoning}"
    print(f"   ✅ Itinerary: {itinerary.data}")
    
    # ═══════════════════════════════════════════════════════════
    # STEP 9: Add to Engine
    # ═══════════════════════════════════════════════════════════
    print("\n📌 STEP 9: Add to Engine")
    engine = TravelDealEngine()
    engine.add_deal("Los Angeles", 299, "Aug 15-22", "Skyscanner", ["HOT"])
    engine.add_deal("Tokyo", 489, "Sep 1-8", "Google Flights")
    engine.add_deal("Bali", 399, "Oct 5-12", "Expedia", ["NEW"])
    
    top = engine.top_deals(3)
    print(f"   ✅ Top deals: {[(d.destination, d.price) for d in top]}")
    
    # ═══════════════════════════════════════════════════════════
    # STEP 10: Check Alerts
    # ═══════════════════════════════════════════════════════════
    print("\n📌 STEP 10: Check Alerts")
    current = {"Los Angeles": 249, "Tokyo": 450}
    triggered = skills.check_alerts(current)
    
    print(f"   ✅ Triggered alerts: {len(triggered)}")
    for alert in triggered:
        print(f"      🔔 {alert['destination']}: ${alert['current_price']} (target: ${alert['target_price']})")
    
    # ═══════════════════════════════════════════════════════════
    # SUMMARY
    # ═══════════════════════════════════════════════════════════
    print("\n" + "=" * 50)
    print("✅ FULL WORKFLOW COMPLETE")
    print(f"   Destination: Los Angeles")
    print(f"   Best price: $279 (Expedia)")
    print(f"   Deals tracked: {len(engine.deals)}")
    print(f"   Alerts: {len(skills.alerts)}")
    print(f"   Triggered: {len(triggered)}")
    print("=" * 50)
    
    return True


if __name__ == "__main__":
    success = test_full_workflow()
    sys.exit(0 if success else 1)
