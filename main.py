"""Cherry Travel Deal Lab v2.2.1 — HNL trip planner, total-cost packages, freemium."""
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
MINIMAL_HTML = """<!DOCTYPE html><html><head><meta charset=utf-8><meta name=viewport content=\"width=device-width,initial-scale=1\">
<title>Cherry Travel Deal Lab</title>
<style>
*{box-sizing:border-box}body{font-family:system-ui,sans-serif;background:#0a0a0f;color:#eee;margin:0;padding:24px;max-width:720px;margin-inline:auto}
h1{background:linear-gradient(90deg,#00d4ff,#7b2ff7);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0 0 8px}
.muted{color:#888;font-size:.9rem}
.card{background:#12121a;border:1px solid #2a2a3a;border-radius:12px;padding:16px;margin:12px 0}
label{display:block;font-size:.75rem;color:#888;margin:8px 0 4px}
input{width:100%;padding:12px;border-radius:8px;border:1px solid #333;background:#111;color:#fff}
.row{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px}
button{margin-top:12px;padding:12px 18px;border-radius:10px;border:0;font-weight:600;cursor:pointer;background:linear-gradient(135deg,#7b2ff7,#00d4ff);color:#fff}
.price{color:#00d4ff;font-size:1.4rem;font-weight:700}
.tag{font-size:.7rem;color:#7b2ff7;text-transform:uppercase;letter-spacing:1px}
</style></head><body>
<h1>Cherry Travel Deal Lab</h1>
<p class=muted>Honolulu-origin total-cost trip briefs · not bare fares · freemium</p>
<div class=card>
<div class=row>
<div><label>Destination</label><input id=dest value=TYO placeholder=TYO></div>
<div><label>Budget USD</label><input id=budget type=number value=2500></div>
<div><label>Nights</label><input id=nights type=number value=5 min=1 max=30></div>
</div>
<button onclick=\"run()\">Plan trip from HNL</button>
</div>
<div id=out></div>
<script>
async function run(){
 const body={destination:dest.value.trim()||'TYO',budget:+budget.value||0,nights:+nights.value||5,origin:'HNL',travelers:1};
 out.innerHTML='<p class=muted>Planning…</p>';
 const r=await fetch('/api/plan',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
 const j=await r.json();
 if(!r.ok){out.innerHTML='<div class=card>'+(j.detail||r.status)+'</div>';return;}
 const m=j.money||{};
 let h=`<div class=card><div class=tag>Money</div><div class=price>$${m.best_total??'—'}</div>
 <p class=muted>all-in ~$${m.best_all_in??'—'} · headroom $${m.headroom??'—'} · ${j.origin}→${j.destination} · ${j.nights}n</p>
 <p class=muted>${m.tip||''}</p></div>`;
 (j.packages||[]).forEach(p=>{
  const sc=p.score||{};
  h+=`<div class=card><div class=tag>${p.label||'package'}</div><div class=price>$${p.total}</div>
  <p class=muted>${(p.flight||{}).title||''} + ${(p.hotel||{}).title||''}</p>
  <p class=muted>score ${sc.score??'—'}/100 ${sc.verdict||''} · ${p.fits_budget?'fits budget':'over budget'}</p></div>`;
 });
 out.innerHTML=h;
}
</script></body></html>"""

app = FastAPI(
    title="Cherry Travel Deal Lab",
    description="Honolulu-origin total-cost trip briefs, ranked packages, freemium",
    version="2.2.1",
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
        return HTMLResponse(path.read_text(encoding="utf-8"))
    return HTMLResponse(MINIMAL_HTML)

@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "version": "2.2.1",
        "product": "cherry-travel-deal-lab",
        "default_origin": "HNL",
        "ai_providers": len(scorer.active_providers),
        "features": ["search", "plan", "packages", "total_cost", "freemium", "budget_fit", "pricing"],
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
