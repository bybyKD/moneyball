"""Application settings — validated, typed, loaded from env/.env.

Never expose secrets to the browser. The web app only talks to this API via
HTTP; secrets live here, server-side only (spec §36).
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    api_name: str = "moneyball-api"
    api_version: str = "0.1.0"
    api_root_path: str = "/api"
    api_env: str = "development"  # development | test | production
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_log_level: str = "INFO"
    api_cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Auth
    auth_secret_key: str = "insecure-change-me"
    auth_algorithm: str = "HS256"
    auth_access_token_minutes: int = 480
    auth_cookie_name: str = "moneyball_session"
    auth_cookie_secure: bool = False  # True only behind HTTPS in production
    auth_cookie_secure_same_site: str = "lax"

    # Database
    database_url: str = (
        "postgresql+psycopg://moneyball:moneyball@localhost:54320/moneyball"
    )
    test_database_url: str = (
        "postgresql+psycopg://moneyball:moneyball@localhost:54321/moneyball_test"
    )

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Embeddings (pgvector)
    embedding_dim: int = 512

    # Data provider
    default_provider: str = "statsbomb"  # statsbomb | demo — cohort reads default here

    # Demo seed scale
    seed_players: int = 5000
    seed_clubs: int = 220
    seed_leagues: int = 18
    seed_seasons: int = 5
    seed_uniform_seed: int = 42

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.api_cors_origins.split(",") if o.strip()]

    @property
    def is_test(self) -> bool:
        return self.api_env == "test"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
