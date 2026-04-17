from openai import OpenAI

from app.config import settings


AGENT_PROMPTS = {
    "general": "You are a concise and helpful AI assistant for software deployment questions.",
    "devops": "You are a senior DevOps engineer. Focus on reliability, observability, CI/CD, and incident prevention.",
    "backend": "You are a senior backend engineer. Focus on API design, data modeling, error handling, and maintainable code.",
    "security": "You are an application security engineer. Focus on secrets management, auth, input validation, and least privilege.",
    "cost": "You are a cloud cost optimization specialist. Focus on efficient architecture, scaling policy, and budget-safe tradeoffs.",
}


def list_agents() -> list[str]:
    return sorted(AGENT_PROMPTS.keys())


def _pick_agent(user_question: str, requested_agent: str) -> str:
    requested = (requested_agent or "auto").strip().lower()
    if requested != "auto":
        if requested not in AGENT_PROMPTS:
            raise RuntimeError(
                f"Unknown agent '{requested}'. Supported agents: {', '.join(list_agents())}, auto"
            )
        return requested

    q = user_question.lower()
    if any(k in q for k in ("security", "x-api-key", "auth", "jwt", "secret", "vulnerability")):
        return "security"
    if any(k in q for k in ("cost", "budget", "optimize", "pricing", "expense")):
        return "cost"
    if any(k in q for k in ("docker", "kubernetes", "deploy", "railway", "render", "ci/cd", "pipeline")):
        return "devops"
    if any(k in q for k in ("api", "fastapi", "redis", "database", "backend", "python")):
        return "backend"
    return "general"


def _build_client() -> OpenAI:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    if settings.openai_base_url:
        return OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url, timeout=30.0)

    return OpenAI(api_key=settings.openai_api_key, timeout=30.0)


def ask_llm(question: str, requested_agent: str = "auto") -> tuple[str, str]:
    client = _build_client()
    agent_used = _pick_agent(question, requested_agent)
    system_prompt = AGENT_PROMPTS[agent_used]
    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {"role": "user", "content": question},
        ],
        temperature=0.2,
        max_tokens=400,
    )

    content = response.choices[0].message.content if response.choices else ""
    if not content:
        raise RuntimeError("LLM returned empty content")
    return content.strip(), agent_used
