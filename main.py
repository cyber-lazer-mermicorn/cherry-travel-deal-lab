"""Cherry Travel Deal Lab v2.3 — HNL trip planner + polished UI."""
from __future__ import annotations
import time
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from src.planner import TripPlanner
from src.scorer import DealScorer
from src.searcher import DealSearcher
from src.users import TIERS, UserManager

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"

app = FastAPI(
    title="Cherry Travel Deal Lab",
    description="Honolulu-origin total-cost trip briefs, ranked packages, freemium",
    version="2.3.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
scorer = DealScorer()
searcher = DealSearcher()
planner = TripPlanner()
users = UserManager()

class SearchRequest(BaseModel):
    destination: str
    budget: float = 0
    origin: str = "HNL"
    user_id: str = ""

class PlanRequest(BaseModel):
    destination: str
    budget: float = 0
    origin: str = "HNL"
    nights: int = Field(default=4, ge=1, le=30)
    travelers: int = Field(default=1, ge=1, le=8)
    include_activities: bool = True
    user_id: str = ""

class RegisterRequest(BaseModel):
    email: str
    name: str
    password: str = ""

class UpgradeRequest(BaseModel):
    user_id: str
    tier: str

@app.get("/")
async def root():
    path = STATIC / "index.html"
    if path.is_file():
        return FileResponse(path, media_type="text/html")
    raise HTTPException(500, "UI missing")

@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "version": "2.3.0",
        "product": "cherry-travel-deal-lab",
        "default_origin": "HNL",
        "ai_providers": len(scorer.active_providers),
        "features": ["search", "plan", "packages", "total_cost", "freemium", "budget_fit", "pricing", "ui"],
    }

@app.get("/api/pricing")
async def pricing():
    return {
        "currency": "USD",
        "tiers": TIERS,
        "positioning": "Sell trip clarity: total cost from Honolulu, ranked packages, budget fit.",
        "value_props": [
            "True total-cost (flight + hotel + buffer)",
            "HNL-origin packages",
            "Budget headroom math",
            "Freemium upgrade path",
        ],
        "non_claims": [
            "Does not book tickets",
            "Sample inventory until live providers are connected",
            "Not a licensed travel agency",
        ],
    }

@app.post("/api/search")
async def search_deals(req: SearchRequest):
    if req.user_id:
        user = users.get(req.user_id)
        if user and not user.can_search():
            raise HTTPException(429, "Daily search limit reached. Upgrade to Pro for more.")
    start = time.time()
    origin = (req.origin or "HNL").upper()
    deals = searcher.search(req.destination, req.budget, origin)
    scored = [{"deal": d.to_dict(), "score": scorer.score(d, req.budget).to_dict()} for d in deals]
    scored.sort(key=lambda x: x["score"]["score"], reverse=True)
    if req.user_id:
        user = users.get(req.user_id)
        if user:
            user.use_search()
            users._save()
    return {
        "deals": scored,
        "count": len(scored),
        "destination": req.destination,
        "origin": origin,
        "latency_ms": round((time.time() - start) * 1000, 1),
    }

@app.post("/api/plan")
async def plan_trip(req: PlanRequest):
    if req.user_id:
        user = users.get(req.user_id)
        if user and not user.can_plan():
            raise HTTPException(429, "Daily plan limit reached. Upgrade to Pro for more plans.")
    start = time.time()
    plan = planner.plan(
        destination=req.destination,
        budget=req.budget,
        origin=req.origin or "HNL",
        nights=req.nights,
        travelers=req.travelers,
        include_activities=req.include_activities,
    )
    if req.user_id:
        user = users.get(req.user_id)
        if user:
            user.use_plan()
            users._save()
    payload = plan.to_dict()
    payload["latency_ms"] = round((time.time() - start) * 1000, 1)
    return payload

@app.post("/api/register")
async def register(req: RegisterRequest):
    user = users.register(req.email, req.name, req.password or "guest")
    if not user:
        raise HTTPException(400, "Email already registered")
    return user.to_dict()

@app.post("/api/upgrade")
async def upgrade(req: UpgradeRequest):
    if not users.upgrade(req.user_id, req.tier):
        raise HTTPException(404, "User not found or invalid tier")
    user = users.get(req.user_id)
    return user.to_dict() if user else {"success": True}

@app.get("/api/user/{user_id}")
async def get_user(user_id: str):
    user = users.get(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return user.to_dict()

if STATIC.is_dir():
    app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")
