from __future__ import annotations

from functools import lru_cache

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    db_url: str = Field(default="", alias="DB_URL")
    app_secret: str = Field(default="kanvas-test-app-2026", alias="APP_SECRET")
    port: int = Field(default=5009, alias="PORT")

    # xAI Grok (default LLM)
    xai_api_key: str = Field(default="", alias="XAI_API_KEY")
    xai_base_url: str = Field(default="https://api.x.ai/v1", alias="XAI_BASE_URL")
    grok_model: str = Field(default="grok-4-1-fast-reasoning", alias="GROK_MODEL")
    xai_agent_model: str = Field(default="", alias="XAI_AGENT_MODEL")

    # OpenAI (optional fallback)
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o", alias="OPENAI_MODEL")

    # Provider switch: xai | openai
    llm_provider: str = Field(default="xai", alias="LLM_PROVIDER")

    # Exa (primary web search for artist research)
    exa_api_key: str = Field(default="", alias="EXA_API_KEY")

    # Feature flags
    login_enabled: bool = Field(default=True, alias="LOGIN")

    # News refresh interval (env fallback; params.yaml is primary)
    news_interval_seconds: int = Field(default=1800, alias="NEWS_INTERVAL_SECONDS")


@lru_cache(maxsize=1)
def settings() -> Settings:
    return Settings()


def get_news_interval() -> int:
    """Return news refresh interval in seconds.
    Primary: config/params.yaml  Fallback: NEWS_INTERVAL_SECONDS env var / default 1800.
    """
    import yaml
    from pathlib import Path

    params_path = Path(__file__).resolve().parents[1] / "config" / "params.yaml"
    if params_path.exists():
        try:
            data = yaml.safe_load(params_path.read_text())
            if data and "news_interval_seconds" in data:
                return int(data["news_interval_seconds"])
        except Exception:
            pass
    return settings().news_interval_seconds
