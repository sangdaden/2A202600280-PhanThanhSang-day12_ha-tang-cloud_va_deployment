from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8000
    redis_url: str = "redis://localhost:6379/0"
    agent_api_key: str = "dev-key-change-me"
    openai_api_key: str = ""
    openai_base_url: str = ""
    log_level: str = "INFO"
    rate_limit_per_minute: int = 10
    monthly_budget_usd: float = 10.0
    llm_model: str = "gpt-4o-mini"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()