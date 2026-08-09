"""
Travel Deal Lab — Platform Integration
========================================
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "mermicorn-client"))

from mermicorn_client import MermicornClient


def get_client() -> MermicornClient:
    return MermicornClient(
        api_url=os.environ.get("MERMICORN_API_URL", "http://localhost:8000"),
        api_key=os.environ.get("MERMICORN_API_KEY", ""),
    )


def sync_deals(deals: list[dict]) -> dict:
    """Sync travel deals to central platform."""
    client = get_client()
    results = []
    for d in deals:
        result = client.deals.add(
            destination=d["destination"], price=d["price"],
            dates=d["dates"], source=d.get("source", ""),
        )
        results.append(result)
    return {"synced": len(results), "results": results}
