import time

import redis
from fastapi import Depends, HTTPException

from app.auth import verify_api_key
from app.config import settings


r = redis.from_url(settings.redis_url, decode_responses=True)


def check_rate_limit(user_id: str = Depends(verify_api_key)):
    now = time.time()
    key = f"rate_limit:{user_id}"

    # Sliding window over 60 seconds.
    p = r.pipeline()
    p.zremrangebyscore(key, 0, now - 60)
    p.zadd(key, {str(now): now})
    p.zcard(key)
    p.expire(key, 70)
    _, _, count, _ = p.execute()

    if int(count) > settings.rate_limit_per_minute:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {settings.rate_limit_per_minute} req/min",
            headers={"Retry-After": "60"},
        )
