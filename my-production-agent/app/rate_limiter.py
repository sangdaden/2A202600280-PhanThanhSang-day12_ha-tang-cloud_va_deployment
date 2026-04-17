import time

import redis
from fastapi import Depends, HTTPException

from app.auth import verify_api_key
from app.config import settings


r = redis.from_url(settings.redis_url, decode_responses=True)


def check_rate_limit(user_id: str = Depends(verify_api_key)) -> None:
	now = time.time()
	key = f"rate:{user_id}"

	pipe = r.pipeline()
	pipe.zremrangebyscore(key, 0, now - 60)
	pipe.zadd(key, {str(now): now})
	pipe.zcard(key)
	pipe.expire(key, 70)
	_, _, count, _ = pipe.execute()

	if int(count) > settings.rate_limit_per_minute:
		raise HTTPException(
			status_code=429,
			detail=f"Rate limit exceeded ({settings.rate_limit_per_minute} req/min)",
			headers={"Retry-After": "60"},
		)

