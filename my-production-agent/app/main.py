import json
import logging
import signal
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import redis
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from app.auth import verify_api_key
from app.config import settings
from app.cost_guard import charge_budget, check_budget
from app.llm_client import ask_llm, list_agents
from app.rate_limiter import check_rate_limit


logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
logger = logging.getLogger(__name__)

redis_client = redis.from_url(settings.redis_url, decode_responses=True)
START_TIME = time.time()
IS_READY = False
ACCEPT_TRAFFIC = True


class AskRequest(BaseModel):
	question: str = Field(..., min_length=1, max_length=2000)
	agent: str = Field(default="auto", description="auto|general|devops|backend|security|cost")


class AskResponse(BaseModel):
	user_id: str
	question: str
	answer: str
	agent_used: str
	turn: int
	model: str
	timestamp: str


def _log(event: str, **kwargs):
	payload = {"event": event, **kwargs}
	logger.info(json.dumps(payload, ensure_ascii=True))


def _history_key(user_id: str) -> str:
	return f"history:{user_id}"


def _estimate_cost(question: str, answer: str) -> float:
	tokens = max(1, (len(question) + len(answer)) // 4)
	return (tokens / 1000.0) * 0.01


@asynccontextmanager
async def lifespan(_: FastAPI):
	global IS_READY
	_log("startup", port=settings.port)
	redis_client.ping()
	IS_READY = True
	yield
	IS_READY = False
	_log("shutdown")


app = FastAPI(
	title="My Production Agent",
	version="1.1.0",
	lifespan=lifespan,
	openapi_tags=[
		{"name": "Ops", "description": "Health and readiness endpoints"},
		{"name": "Agent", "description": "LLM ask endpoint and available agents"},
		{"name": "History", "description": "Conversation history endpoints"},
	],
)


@app.middleware("http")
async def middleware(request: Request, call_next):
	if not ACCEPT_TRAFFIC and request.url.path not in ("/health", "/ready"):
		raise HTTPException(status_code=503, detail="Server is shutting down")
	start = time.time()
	response = await call_next(request)
	response.headers["X-Content-Type-Options"] = "nosniff"
	response.headers["X-Frame-Options"] = "DENY"
	_log(
		"request",
		method=request.method,
		path=request.url.path,
		status=response.status_code,
		duration_ms=round((time.time() - start) * 1000, 1),
	)
	return response


@app.get("/health", tags=["Ops"])
def health():
	return {
		"status": "ok",
		"uptime_seconds": round(time.time() - START_TIME, 1),
		"timestamp": datetime.now(timezone.utc).isoformat(),
	}


@app.get("/ready", tags=["Ops"])
def ready():
	if not IS_READY:
		raise HTTPException(status_code=503, detail="Not ready")
	redis_client.ping()
	return {"ready": True}


@app.get("/agents", tags=["Agent"])
def agents_catalog():
	return {"agents": list_agents(), "default": "auto"}


@app.post("/ask", response_model=AskResponse, tags=["Agent"])
def ask(
	body: AskRequest,
	user_id: str = Depends(verify_api_key),
	_rate_limit: None = Depends(check_rate_limit),
	_budget: None = Depends(check_budget),
):
	try:
		answer, agent_used = ask_llm(body.question, body.agent)
	except RuntimeError as exc:
		raise HTTPException(status_code=503, detail=str(exc)) from exc
	except Exception as exc:
		raise HTTPException(status_code=502, detail=f"LLM provider error: {exc}") from exc
	charge_budget(user_id, _estimate_cost(body.question, answer))

	key = _history_key(user_id)
	redis_client.rpush(key, json.dumps({"role": "user", "content": body.question}))
	redis_client.rpush(key, json.dumps({"role": "assistant", "content": answer}))
	turn = redis_client.llen(key)

	return AskResponse(
		user_id=user_id,
		question=body.question,
		answer=answer,
		agent_used=agent_used,
		turn=turn,
		model=settings.llm_model,
		timestamp=datetime.now(timezone.utc).isoformat(),
	)


@app.get("/history/{user_id}", tags=["History"])
def history(user_id: str, _auth: str = Depends(verify_api_key)):
	items = redis_client.lrange(_history_key(user_id), 0, -1)
	return {"user_id": user_id, "messages": [json.loads(item) for item in items]}


def _handle_sigterm(signum, _frame):
	global ACCEPT_TRAFFIC
	ACCEPT_TRAFFIC = False
	_log("signal", signum=signum, signal="SIGTERM")


signal.signal(signal.SIGTERM, _handle_sigterm)


if __name__ == "__main__":
	uvicorn.run("app.main:app", host=settings.host, port=settings.port, timeout_graceful_shutdown=30)

