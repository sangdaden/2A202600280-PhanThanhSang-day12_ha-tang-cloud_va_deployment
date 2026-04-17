# Deployment Information

## Public URL

- https://my-production-agent-production-8622.up.railway.app

## Platform

- Railway

## Services

- App service: `my-production-agent`
- Redis service: `Redis`

## Deployment Status

- App deployment status: SUCCESS
- Redis deployment status: ONLINE

## Environment Variables (App Service)

- `AGENT_API_KEY`
- `OPENAI_API_KEY`
- `LLM_MODEL`
- `OPENAI_BASE_URL` (optional, only for OpenAI-compatible providers)
- `LOG_LEVEL`
- `RATE_LIMIT_PER_MINUTE`
- `MONTHLY_BUDGET_USD`
- `REDIS_URL`

## Test Commands

```bash
PUBLIC_URL='https://my-production-agent-production-8622.up.railway.app'

# 1) Health
curl -sS "$PUBLIC_URL/health"

# 2) Readiness
curl -sS "$PUBLIC_URL/ready"

# 3) Auth required (expect 401)
curl -sS -o /tmp/no_key.out -w '%{http_code}' \
  -X POST "$PUBLIC_URL/ask" \
  -H 'Content-Type: application/json' \
  -d '{"question":"hello"}'
cat /tmp/no_key.out

# 4) Ask with API key (expect 200)
curl -sS -X POST "$PUBLIC_URL/ask" \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: your-strong-key' \
  -H 'X-User-Id: user1' \
  -d '{"question":"hello"}'

# If OPENAI_API_KEY is missing, /ask will return 503

# 5) Rate limit (expect 429 after 10 req/min)
for i in $(seq 1 12); do
  code=$(curl -s -o /tmp/rate.out -w '%{http_code}' \
    -X POST "$PUBLIC_URL/ask" \
    -H 'Content-Type: application/json' \
    -H 'X-API-Key: your-strong-key' \
    -H 'X-User-Id: rate-user' \
    -d '{"question":"rate test"}')
  echo "$i:$code"
done
cat /tmp/rate.out
```

## Latest Verified Results

- `/health` -> `{"status":"ok",...}`
- `/ready` -> `{"ready":true}`
- `/ask` without key -> `401`, body: `{"detail":"Invalid API key"}`
- `/ask` with key -> `200`, valid JSON response
- Rate limit -> `429` from request 11 onward for same user in same minute

## Notes

- Redis service already exists as `Redis` in Railway project.
- App Dockerfile updated to bind to Railway `PORT` dynamically.
