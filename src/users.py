"""Freemium limits — money niche gate for Cherry Travel Deal Lab."""
from __future__ import annotations
import hashlib, json, os, time
from dataclasses import dataclass, field
from typing import Optional

TIERS = {
    "free": {"searches_limit": 5, "plans_limit": 2, "price_usd": 0, "label": "Free", "blurb": "Try the HNL trip engine — 2 plans/day"},
    "pro": {"searches_limit": 60, "plans_limit": 30, "price_usd": 9.99, "label": "Pro", "blurb": "Serious planners — 30 trip briefs/day + priority scoring"},
    "premium": {"searches_limit": 9999, "plans_limit": 9999, "price_usd": 19.99, "label": "Premium", "blurb": "Unlimited plans, all destinations, activity packages"},
}

@dataclass
class User:
    user_id: str
    email: str
    name: str
    tier: str = "free"
    searches_today: int = 0
    plans_today: int = 0
    searches_limit: int = 5
    plans_limit: int = 2
    created_at: float = field(default_factory=time.time)
    last_search: float = 0

    def _roll_day(self) -> None:
        if time.time() - self.last_search > 86400:
            self.searches_today = 0
            self.plans_today = 0

    def can_search(self) -> bool:
        self._roll_day()
        return self.searches_today < self.searches_limit

    def can_plan(self) -> bool:
        self._roll_day()
        return self.plans_today < self.plans_limit

    def use_search(self) -> None:
        self._roll_day()
        self.searches_today += 1
        self.last_search = time.time()

    def use_plan(self) -> None:
        self._roll_day()
        self.plans_today += 1
        self.last_search = time.time()

    def to_dict(self) -> dict:
        return {"user_id": self.user_id, "email": self.email, "name": self.name, "tier": self.tier, "searches_today": self.searches_today, "searches_limit": self.searches_limit, "plans_today": self.plans_today, "plans_limit": self.plans_limit, "can_search": self.can_search(), "can_plan": self.can_plan(), "tier_price_usd": TIERS.get(self.tier, TIERS["free"])["price_usd"], "tier_label": TIERS.get(self.tier, TIERS["free"]).get("label", self.tier)}

class UserManager:
    def __init__(self, db_path: str | None = None) -> None:
        if db_path is None:
            if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
                db_path = "/tmp/deal_finder_users.json"
            else:
                db_path = "data/users.json"
        self.db_path = db_path
        parent = os.path.dirname(db_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        self.users: dict[str, User] = {}
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self.db_path):
            return
        try:
            with open(self.db_path) as f:
                data = json.load(f)
            for uid, udata in data.items():
                allowed = {k: v for k, v in udata.items() if k in User.__dataclass_fields__}
                self.users[uid] = User(**allowed)
        except Exception:
            pass

    def _save(self) -> None:
        try:
            payload = {uid: {"user_id": u.user_id, "email": u.email, "name": u.name, "tier": u.tier, "searches_today": u.searches_today, "plans_today": u.plans_today, "searches_limit": u.searches_limit, "plans_limit": u.plans_limit, "created_at": u.created_at, "last_search": u.last_search} for uid, u in self.users.items()}
            with open(self.db_path, "w") as f:
                json.dump(payload, f, indent=2)
        except Exception:
            pass

    def _hash(self, email: str) -> str:
        return hashlib.sha256(email.lower().strip().encode()).hexdigest()[:16]

    def register(self, email: str, name: str, password: str = "") -> Optional[User]:
        uid = self._hash(email)
        if uid in self.users:
            return None
        t = TIERS["free"]
        user = User(user_id=uid, email=email, name=name, tier="free", searches_limit=t["searches_limit"], plans_limit=t["plans_limit"])
        self.users[uid] = user
        self._save()
        return user

    def get(self, user_id: str) -> Optional[User]:
        return self.users.get(user_id)

    def upgrade(self, user_id: str, tier: str) -> bool:
        user = self.users.get(user_id)
        if not user or tier not in TIERS:
            return False
        user.tier = tier
        user.searches_limit = TIERS[tier]["searches_limit"]
        user.plans_limit = TIERS[tier]["plans_limit"]
        self._save()
        return True
