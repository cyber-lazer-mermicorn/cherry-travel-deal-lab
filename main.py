"""Cherry Travel Deal Lab v2.2 — HNL trip planner, total-cost packages, freemium."""
from __future__ import annotations
import time
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from src.planner import TripPlanner
from src.scorer import DealScorer
from src.searcher import DealSearcher
from src.users import TIERS, UserManager

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
MINIMAL_HTML = """<!DOCTYPE html><html><head><meta charset=utf-8><title>Cherry Travel Deal Lab</title>
<style>body{font-family:system-ui;background:#0a0a0f;color:#eee;margin:0;padding:24px}
input,button{padding:10px;margin:4px;border-radius:8px;border:1px solid #333;background:#111;color:#fff}
button{background:linear-gradient(135deg,#7b2ff7,#00d4ff);border:0;font-weight:600}
.card{background:#12121a;border:1px solid #2a2a3a;border-radius:12px;padding:16px;margin:12px 0}
.price{color:#00d4ff;font-size:1.3rem;font-weight:700}.muted{color:#888}</style></head><body>
<h1>Cherry Travel Deal Lab</h1><p class=muted>HNL total-cost trip briefs · freemium</p>
<div class=card>
<label>Destination <input id=dest value=TYO></label>
<label>Budget <input id=budget type=number value=2500></label>
<label>Nights <input id=nights type=number value=5></label>
<button onclick=\"run()\">Plan trip</button></div><div id=out></div>
<script>
async function run(){
 const body={destination:dest.value,budget:+budget.value,nights:+nights.value,origin:'HNL',travelers:1};
 const r=await fetch('/api/plan',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
 const j=await r.json();
 if(!r.ok){out.innerHTML='<p>'+(j.detail||r.status)+'</p>';return;}
 const m=j.money||{};
 let h=`<div class=card><div class=price>$${m.best_total||'—'}</div><p class=muted>all-in ~$${m.best_all_in||'—'} · headroom $${m.headroom??'—'} · ${m.tip||''}</p></div>`;
 (j.packages||[]).forEach(p=>{h+=`<div class=card><b>$${p.total}</b> · ${p.label}<br><span class=muted>${(p.flight||{}).title||''} + ${(p.hotel||{}).title||''}</span></div>`;});
 out.innerHTML=h;
}
</script></body></html>"""

app = FastAPI(title="Cherry Travel Deal Lab", description="Honolulu-origin trip briefs, total-cost packages, freemium", version="2.2.0")
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
        return HTMLResponse(path.read_text(encoding="utf-8"))
    return HTMLResponse(MINIMAL_HTML)

@app.get("/api/health")
async def health():
    return {"status": "healthy", "version": "2.2.0", "ai_providers": len(scorer.active_providers), "default_origin": "HNL", "features": ["search", "plan", "packages", "total_cost", "freemium", "budget_fit"], "product": "cherry-travel-deal-lab"}

@app.get("/api/pricing")
async def pricing():
    return {"currency": "USD", "tiers": TIERS, "positioning": "Sell trip clarity: total cost from Honolulu, ranked packages, budget fit.", "value_props": ["True total-cost (flight + hotel + buffer)", "HNL-origin packages", "Budget headroom", "Freemium upgrade path"]}

@app.post("/api/search")
async def search_deals(req: SearchRequest):
    if req.user_id:
        user = users.get(req.user_id)
        if user and not user.can_search():
            raise HTTPException(429, "Daily search limit reached. Upgrade to Pro for more.")
    start = time.time()
    origin = (req.origin or "HNL").upper()
    deals = searcher.search_flights(req.destination, req.budget, origin)
    deals += searcher.search_hotels(req.destination, req.budget)
    scored = [{"deal": deal.to_dict(), "score": scorer.score(deal, req.budget).to_dict()} for deal in deals]
    scored.sort(key=lambda x: x["score"]["score"], reverse=True)
    if req.user_id:
        user = users.get(req.user_id)
        if user:
            user.use_search()
            users._save()
    return {"deals": scored, "count": len(scored), "destination": req.destination, "origin": origin, "latency_ms": round((time.time() - start) * 1000, 1)}

@app.post("/api/plan")
async def plan_trip(req: PlanRequest):
    if req.user_id:
        user = users.get(req.user_id)
        if user and not user.can_plan():
            raise HTTPException(429, "Daily plan limit reached. Upgrade to Pro for more plans.")
    start = time.time()
    plan = planner.plan(destination=req.destination, budget=req.budget, origin=req.origin or "HNL", nights=req.nights, travelers=req.travelers, include_activities=req.include_activities)
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
