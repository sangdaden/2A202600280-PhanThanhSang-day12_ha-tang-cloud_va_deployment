# My Production Agent

FastAPI production agent with real LLM integration (OpenAI-compatible), API key auth, rate limiting, budget guard, Redis-backed stateless history, health/readiness endpoints, and Railway deployment.

## Features

- API key authentication via `X-API-Key`
- Real LLM response via OpenAI-compatible API
- Per-user rate limit (`10 req/min`)
- Per-user monthly budget guard
- Health endpoint: `GET /health`
- Readiness endpoint: `GET /ready`
- Stateless conversation history in Redis
- Dockerized deployment for local and cloud

## Project Structure

```text
my-production-agent/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── auth.py
│   ├── rate_limiter.py
│   └── cost_guard.py
├── app/
│   └── llm_client.py
├── Dockerfile
├── docker-compose.yml
├── nginx.conf
├── requirements.txt
├── .env.example
└── .dockerignore
```

## Local Run (Docker Compose)

```bash
cd my-production-agent
cp .env.example .env

docker compose up --build --scale agent=3 -d

docker compose ps
curl -sS http://localhost:8090/health
curl -sS http://localhost:8090/ready
```

### Local API test

```bash
curl -sS -X POST http://localhost:8090/ask \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: dev-key-change-me' \
  -H 'X-User-Id: user1' \
  -d '{"question":"Redis dung de lam gi?"}'
```

## Railway Deployment

Current project is linked to Railway project `sangphan-demo-lab12`.

```bash
cd my-production-agent

# (already created) set required variables for app service
railway variable set AGENT_API_KEY=your-strong-key --service my-production-agent
railway variable set OPENAI_API_KEY='sk-...' --service my-production-agent
railway variable set LLM_MODEL='gpt-4o-mini' --service my-production-agent
# optional for OpenAI-compatible providers:
# railway variable set OPENAI_BASE_URL='https://.../v1' --service my-production-agent
railway variable set LOG_LEVEL=INFO --service my-production-agent
railway variable set RATE_LIMIT_PER_MINUTE=10 --service my-production-agent
railway variable set MONTHLY_BUDGET_USD=10.0 --service my-production-agent

# ensure REDIS_URL points to Redis service URL
railway variable list --service Redis
railway variable set REDIS_URL='<redis-url-from-Redis-service>' --service my-production-agent

# deploy
railway up --service my-production-agent
railway domain --service my-production-agent
```

## Public URL

- `https://my-production-agent-production-8622.up.railway.app`

## Production smoke tests

```bash
PUBLIC_URL='https://my-production-agent-production-8622.up.railway.app'

curl -sS "$PUBLIC_URL/health"
curl -sS "$PUBLIC_URL/ready"

# should return 401 without API key
curl -sS -o /tmp/no_key.out -w '%{http_code}' \
  -X POST "$PUBLIC_URL/ask" \
  -H 'Content-Type: application/json' \
  -d '{"question":"hello"}'

# should return 200 with API key
curl -sS -X POST "$PUBLIC_URL/ask" \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: your-strong-key' \
  -H 'X-User-Id: user1' \
  -d '{"question":"hello"}'
```
