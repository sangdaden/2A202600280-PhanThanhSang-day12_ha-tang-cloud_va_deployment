from datetime import datetime, timezone

import redis
from fastapi import Depends, HTTPException

from app.auth import verify_api_key
from app.config import settings


r = redis.from_url(settings.redis_url, decode_responses=True)


def _budget_key(user_id: str) -> str:
	month = datetime.now(timezone.utc).strftime("%Y-%m")
	return f"budget:{user_id}:{month}"


def check_budget(user_id: str = Depends(verify_api_key)) -> None:
	current = float(r.get(_budget_key(user_id)) or 0.0)
	if current >= settings.monthly_budget_usd:
		raise HTTPException(status_code=402, detail="Monthly budget exceeded")


def charge_budget(user_id: str, estimated_cost: float) -> None:
	key = _budget_key(user_id)
	current = float(r.get(key) or 0.0)
	if current + estimated_cost > settings.monthly_budget_usd:
		raise HTTPException(status_code=402, detail="Monthly budget exceeded")

	p = r.pipeline()
	p.incrbyfloat(key, estimated_cost)
	p.expire(key, 32 * 24 * 3600)
	p.execute()

