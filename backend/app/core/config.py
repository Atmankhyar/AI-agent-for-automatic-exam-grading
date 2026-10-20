from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

INSECURE_SECRET_KEYS = {"dev-secret-change-in-production", "changeme", "secret", ""}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    app_name: str = "exam-corrector"
    api_v1_prefix: str = "/api"
    environment: Literal["development", "test", "production"] = "development"
    log_level: str = "INFO"
    log_format: Literal["json", "text"] = "json"

    # --- Auth -------------------------------------------------------------
    secret_key: str = "dev-secret-change-in-production"  # noqa: S105 - dev default, refused in production
    access_token_expire_minutes: int = 60
    bcrypt_rounds: int = 12
    # Self-registration may create teacher/student accounts; admin is never self-assignable.
    allow_teacher_self_registration: bool = True
    cors_origins: str = "http://localhost:3000"
    # Creates demo accounts with known passwords. Never enable in production.
    seed_demo_data: bool = False

    # --- Database ---------------------------------------------------------
    database_url: str | None = None  # If set, used as-is (e.g. sqlite for local dev without Docker)
    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str = "exam"
    db_password: str = "exam"  # noqa: S105 - local docker-compose default
    db_name: str = "exam"

    # --- Files ------------------------------------------------------------
    file_storage_path: str = "./storage"
    max_upload_mb: int = 15
    max_pdf_pages: int = 30

    # --- Background processing -------------------------------------------
    redis_url: str = "redis://localhost:6379/0"
    # inline: FastAPI background task in the API process (dev/tests, no Redis needed)
    # celery: Celery worker via Redis (docker compose)
    grading_executor: Literal["inline", "celery"] = "inline"
    grading_task_soft_time_limit_s: int = 300
    grading_task_hard_time_limit_s: int = 360

    # --- LLM grading ------------------------------------------------------
    llm_provider: Literal["gemini", "fake"] = "gemini"
    gemini_api_key: SecretStr | None = None
    llm_model: str = "gemini-3.8-flash"
    llm_timeout_s: float = 60.0
    llm_max_retries: int = 5
    llm_max_concurrency: int = 4
    llm_samples: int = 1  # >1 enables self-consistency sampling (cost scales linearly)
    llm_temperature: float | None = None  # None = provider default
    llm_thinking_level: str | None = None  # MINIMAL|LOW|MEDIUM|HIGH; None = model default
    grading_prompt_version: str = "open_v2"
    # Normalised score spread across samples above which a grade is sent to review.
    review_spread_threshold: float = 0.15

    # --- Code execution sandbox -------------------------------------------
    code_sandbox: Literal["docker", "disabled"] = "disabled"
    sandbox_image: str = "python:3.12-slim"
    sandbox_runtime: str | None = None  # e.g. "runsc" for gVisor
    sandbox_memory_mb: int = 128
    sandbox_cpus: float = 0.5
    sandbox_test_timeout_s: float = 2.0
    sandbox_total_timeout_s: float = 20.0

    @property
    def database_url_resolved(self) -> str:
        """DATABASE_URL if set, otherwise PostgreSQL from the DB_* parts."""
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+psycopg2://{self.db_user}:"
            f"{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def validate_for_startup(self) -> None:
        """Refuse to start a production deployment with unsafe settings."""
        if self.environment != "production":
            return
        problems = []
        if self.secret_key in INSECURE_SECRET_KEYS or len(self.secret_key) < 32:
            problems.append("SECRET_KEY must be set to a random value of at least 32 characters")
        if self.seed_demo_data:
            problems.append("SEED_DEMO_DATA must be false in production")
        if "*" in self.cors_origin_list:
            problems.append("CORS_ORIGINS must list explicit origins in production")
        if problems:
            raise RuntimeError("Unsafe production configuration: " + "; ".join(problems))


@lru_cache
def get_settings() -> Settings:
    return Settings()
