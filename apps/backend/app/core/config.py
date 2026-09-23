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

    # e-barimt QR verification. ⛔ production access requires a tax-authority
    # API agreement — dev/stage point at a local mock (see app/core/e_barimt.py).
    e_barimt_use_mock: bool = True
    e_barimt_verify_url: str = "http://localhost:8080/mock-e-barimt/verify"
    e_barimt_max_receipt_age_days: int = 90

    uploads_bucket: str = "omnirate-dev-uploads"
    uploads_max_bytes: int = 10 * 1024 * 1024

    # P2-03: Ed25519 seed for hospital-visit QR signing, base64-encoded 32
    # bytes. The dev default below is fixed (NOT secret) purely so local runs
    # are reproducible — prod MUST override via env, generated with
    # `Ed25519PrivateKey.generate()` and stored in a secrets manager.
    hospital_qr_ed25519_seed_b64: str = "MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA="
    hospital_qr_ttl_hours: int = 72

    # P2-05: LLM moderation fallback endpoint. Unset in dev — see
    # app/ml/llm_moderation.py's _call_llm for what a real value needs to serve.
    llm_moderation_api_url: str | None = None
    llm_monthly_budget_usd: float = 500.0

    # P2-07: DuckDB's postgres_scanner wants a libpq DSN, not SQLAlchemy's
    # "+asyncpg" URL — kept as a separate setting rather than parsed from
    # database_url so the two can point at different roles (export uses a
    # read-only replica in prod).
    database_url_psycopg: str = "postgresql://omnirate:omnirate@localhost:5432/omnirate"
    analytics_bucket: str = "omnirate-dev-analytics"

    # P3-03: attendance/objective-data source. No specific government API has
    # been identified yet (SOW's own dependency note, not just this repo's).
    attendance_source_url: str | None = None
    takedown_default_sla_hours: int = 72
    law_enforcement_sla_hours: int = 4

    otel_exporter_endpoint: str | None = None
    sentry_dsn: str | None = None

    rate_limit_default_per_minute: int = 120

    # apps/web calls the API through Next.js's own server-side rewrite proxy
    # (same-origin, no CORS involved), but apps/mobile's Expo web target
    # calls it directly cross-origin — CORS has to be explicit for that to
    # work at all. Dev defaults cover both dev servers; override in
    # non-dev environments rather than widening this.
    cors_allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:8081", "http://localhost:19006"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
