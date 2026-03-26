import os
from dataclasses import dataclass
from functools import lru_cache
from typing import List

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    app_name: str = os.getenv("APP_NAME", "AI Resume Analyzer")
    app_env: str = os.getenv("APP_ENV", "dev")
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")
    app_port: int = int(os.getenv("APP_PORT", "8000"))
    cors_origins: List[str] = None  # type: ignore[assignment]

    llm_base_url: str = os.getenv("LLM_BASE_URL", "").strip()
    llm_api_key: str = os.getenv("LLM_API_KEY", "").strip()
    llm_model: str = os.getenv("LLM_MODEL", "").strip()

    redis_url: str = os.getenv("REDIS_URL", "").strip()
    cache_ttl_seconds: int = int(os.getenv("CACHE_TTL_SECONDS", "3600"))

    def __post_init__(self) -> None:
        origins_raw = os.getenv("CORS_ORIGINS", "http://localhost:5173")
        self.cors_origins = [item.strip() for item in origins_raw.split(",") if item.strip()]

    @property
    def llm_enabled(self) -> bool:
        return bool(self.llm_base_url and self.llm_api_key and self.llm_model)

    @property
    def redis_enabled(self) -> bool:
        return bool(self.redis_url)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

