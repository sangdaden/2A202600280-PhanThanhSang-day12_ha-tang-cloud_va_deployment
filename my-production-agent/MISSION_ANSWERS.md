# Day 12 Lab - Mission Answers

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found

1. Hardcoded secrets/keys in code or config.
2. Running app directly without health/readiness checks.
3. Keeping conversation state in memory (not stateless).
4. Missing graceful shutdown handling.

### Exercise 1.3: Develop vs Production comparison

| Feature | Develop | Production | Why Important? |
|---|---|---|---|
| Config | Local defaults | Environment variables | Easy and safe environment-specific config |
| Security | Often open endpoints | API key required | Prevent unauthorized usage |
| Reliability | No probes | Health + readiness | Better orchestration and uptime |
| State | In-memory | Redis-backed | Supports scaling without sticky state |

## Part 2: Docker

### Exercise 2.1: Dockerfile questions

1. Base image: `python:3.11-slim`
2. Working directory: `/app`
3. Runtime user: non-root user `app`

### Exercise 2.3: Image size comparison

- Develop image: built successfully in section `02-docker/develop`
- Production image: built successfully in section `02-docker/production`
- Observation: production image is slimmer and safer due to minimal base/runtime pattern.

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment

- URL: https://my-production-agent-production-8622.up.railway.app
- Status: deployed successfully
- Services in project:
  - `my-production-agent`
  - `Redis`

## Part 4: API Security

### Exercise 4.1-4.3: Test results

- `POST /ask` without API key -> `401` with `{"detail":"Invalid API key"}`
- `POST /ask` with valid API key -> `200` with valid answer JSON
- Rate limit test (same user): requests 1..10 -> `200`, request 11+ -> `429`

### Exercise 4.4: Cost guard implementation

- Cost guard tracks per-user monthly usage in Redis.
- Budget threshold controlled by `MONTHLY_BUDGET_USD`.
- Request is blocked when estimated usage exceeds configured monthly budget.

## Part 5: Scaling & Reliability

### Exercise 5.1-5.5: Implementation notes

- Implemented `/health` and `/ready` endpoints.
- Added graceful shutdown behavior for service termination.
- Converted conversation history to Redis for stateless scaling.
- Verified local scaling with Docker Compose (`agent=3`).
- Verified cloud deployment and endpoint behavior on Railway.

## Part 6: Final Project Summary

- Production-ready FastAPI service with:
  - API key auth
  - rate limit
  - monthly budget guard
  - Redis stateless history
  - Dockerized deploy
  - Railway deployment with public URL

## Repository Deliverables (for submission)

- `README.md`: setup + run + deploy guide
- `DEPLOYMENT.md`: live URL + test commands + results
- `MISSION_ANSWERS.md`: this file
