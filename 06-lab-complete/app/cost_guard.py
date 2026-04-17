from datetime import datetime, timezone

import redis
from fastapi import HTTPException

from app.config import settings


r = redis.from_url(settings.redis_url, decode_responses=True)


def _month_key() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def charge_and_check_budget(user_id: str, estimated_cost_usd: float) -> None:
    key = f"budget:{user_id}:{_month_key()}"
    current = float(r.get(key) or 0.0)
    next_total = current + estimated_cost_usd
    if next_total > settings.monthly_budget_usd:
        raise HTTPException(
            status_code=402,
            detail=f"Monthly budget exceeded (${settings.monthly_budget_usd})",
        )

    p = r.pipeline()
    p.incrbyfloat(key, estimated_cost_usd)
    p.expire(key, 32 * 24 * 3600)
    p.execute()
