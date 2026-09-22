from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="OMNIRATE_", extra="ignore")

    env: str = "dev"
    database_url: str = "postgresql+asyncpg://omnirate:omnirate@localhost:5432/omnirate"
    redis_url: str = "redis://localhost:6379/0"
    opensearch_url: str = "http://localhost:9200"

    jwt_secret: str = Field(default="dev-only-change-me")
    jwt_algorithm: str = "HS256"
    jwt_access_ttl_seconds: int = 900

    # HMAC key for hashing national-ID (РД) before storage — never store raw РД.
    rd_hmac_secret: str = Field(default="dev-only-change-me")

    # ДАН (national e-auth) OAuth2+PKCE client. In dev/stage these point at the
    # local mock provider (see app/core/dan_auth.py); production values require
    # a signed agreement with ДАН — see docs/PROGRESS.md.
    dan_client_id: str = "omnirate-dev"
    dan_authorize_url: str = "http://localhost:8080/mock-dan/authorize"
    dan_token_url: str = "http://localhost:8080/mock-dan/token"
    dan_use_mock: bool = True

    otel_exporter_endpoint: str | None = None
    sentry_dsn: str | None = None

    rate_limit_default_per_minute: int = 120


@lru_cache
def get_settings() -> Settings:
    return Settings()
