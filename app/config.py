from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    bolna_api_key: str = Field(...)
    bolna_agent_id: str = Field(...)
    slack_webhook_url: str = Field(...)

    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5433/bolna_alerts",
    )

    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)
    app_env: str = Field(default="development")
    log_level: str = Field(default="INFO")

    bolna_webhook_ip: str = Field(default="13.203.39.153")
    enable_ip_whitelist: bool = Field(default=False)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
