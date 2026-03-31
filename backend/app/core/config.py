from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "exam-corrector"
    api_v1_prefix: str = "/api"
    secret_key: str = "dev-secret-change-in-production"
    access_token_expire_minutes: int = 60

    database_url: str | None = None  # Si défini, utilisé tel quel (ex: sqlite pour dev sans Docker)
    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str = "exam"
    db_password: str = "exam"
    db_name: str = "exam"

    redis_url: str = "redis://localhost:6379/0"
    openai_api_key: str | None = None
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    llm_model: str = "gpt-4.1-mini"
    file_storage_path: str = "./storage"

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def database_url_resolved(self) -> str:
        """URL de connexion DB : DATABASE_URL si défini, sinon PostgreSQL."""
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+psycopg2://{self.db_user}:"
            f"{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
