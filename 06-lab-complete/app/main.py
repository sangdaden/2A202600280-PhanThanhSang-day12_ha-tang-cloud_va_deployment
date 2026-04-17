"""Production-ready AI Agent for Part 6 final project."""
import json
import logging
import signal
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import redis
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.auth import verify_api_key
from app.config import settings
from app.cost_guard import charge_and_check_budget
from app.rate_limiter import check_rate_limit
from utils.mock_llm import ask as llm_ask


logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format='{"ts":"%(asctime)s","level":"%(levelname)s","message":%(message)s}',
)
logger = logging.getLogger(__name__)

START_TIME = time.time()
REQUEST_COUNT = 0
ERROR_COUNT = 0
IS_READY = False
ACCEPT_TRAFFIC = True
redis_client = redis.from_url(settings.redis_url, decode_responses=True)


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)


class AskResponse(BaseModel):
    user_id: str
    question: str
    answer: str
    turn: int
    model: str
    timestamp: str


def _estimate_cost_usd(question: str, answer: str) -> float:
    # Simple mock estimation for budget guard in this lab.
    tokens = max(1, (len(question) + len(answer)) // 4)
    return (tokens / 1000.0) * 0.01


def _history_key(user_id: str) -> str:
    return f"history:{user_id}"


@asynccontextmanager
async def lifespan(app: FastAPI):
    global IS_READY
    logger.info(json.dumps({"event": "startup", "app": settings.app_name, "version": settings.app_version}))
    redis_client.ping()
    IS_READY = True
    logger.info(json.dumps({"event": "ready"}))
    yield
    IS_READY = False
    logger.info(json.dumps({"event": "shutdown"}))


app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key", "X-User-Id"],
)


@app.middleware("http")
async def request_middleware(request: Request, call_next):
    global REQUEST_COUNT, ERROR_COUNT
    start = time.time()
    REQUEST_COUNT += 1

    if not ACCEPT_TRAFFIC and request.url.path not in ("/health", "/ready"):
        raise HTTPException(status_code=503, detail="Server is shutting down")

    try:
        response: Response = await call_next(request)
    except Exception:
        ERROR_COUNT += 1
        raise

    duration_ms = round((time.time() - start) * 1000, 1)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    logger.info(json.dumps({
        "event": "request",
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code,
        "duration_ms": duration_ms,
    }))
    return response


@app.get("/")
def root():
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "version": settings.app_version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/ready")
def ready():
    if not IS_READY:
        raise HTTPException(status_code=503, detail="Not ready")
    try:
        redis_client.ping()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Redis unavailable") from exc
    return {"ready": True}


@app.post("/ask", response_model=AskResponse)
def ask(
    body: AskRequest,
    user_id: str = Depends(verify_api_key),
    _rate_limit: None = Depends(check_rate_limit),
):
    history_key = _history_key(user_id)
    answer = llm_ask(body.question)

    estimated_cost = _estimate_cost_usd(body.question, answer)
    charge_and_check_budget(user_id, estimated_cost)

    # Stateless design: all conversation state lives in Redis.
    redis_client.rpush(history_key, json.dumps({"role": "user", "content": body.question}))
    redis_client.rpush(history_key, json.dumps({"role": "assistant", "content": answer}))
    turn = redis_client.llen(history_key)

    return AskResponse(
        user_id=user_id,
        question=body.question,
        answer=answer,
        turn=turn,
        model=settings.llm_model,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/history/{user_id}")
def get_history(user_id: str, _auth_user: str = Depends(verify_api_key)):
    items = redis_client.lrange(_history_key(user_id), 0, -1)
    return {"user_id": user_id, "messages": [json.loads(it) for it in items]}


@app.get("/metrics")
def metrics(_auth_user: str = Depends(verify_api_key)):
    return {
        "total_requests": REQUEST_COUNT,
        "error_count": ERROR_COUNT,
        "uptime_seconds": round(time.time() - START_TIME, 1),
    }


def handle_sigterm(signum, frame):
    global ACCEPT_TRAFFIC
    ACCEPT_TRAFFIC = False
    logger.info(json.dumps({"event": "signal", "name": "SIGTERM", "signum": signum}))


signal.signal(signal.SIGTERM, handle_sigterm)


if __name__ == "__main__":
    logger.info(json.dumps({"event": "server_start", "host": settings.host, "port": settings.port}))
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        timeout_graceful_shutdown=30,
    )
