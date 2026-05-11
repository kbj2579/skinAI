from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[3]   # medical_ai_team3_new/
BACKEND_DIR = Path(__file__).resolve().parents[2]  # backend/
ENV_FILES = tuple(
    str(path) for path in (ROOT_DIR / ".env", ROOT_DIR / ".env.local") if path.exists()
)

# 절대경로: backend/skin_ai.db — 어느 디렉토리에서 실행해도 동일
_DEFAULT_DB = f"sqlite+aiosqlite:///{BACKEND_DIR / 'skin_ai.db'}"


class Settings(BaseSettings):
    database_url: str = _DEFAULT_DB

    storage_endpoint: str = "http://127.0.0.1:9000"
    storage_access_key: str = "minioadmin"
    storage_secret_key: str = "minioadmin"
    storage_bucket: str = "skin-ai"
    storage_region: str = "us-east-1"

    ai_model_base_url: str = "http://127.0.0.1:8001"

    gemini_api_key: str = ""

    jwt_secret: str = "change-this-secret"
    jwt_expire_minutes: int = 60

    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    model_config = SettingsConfigDict(
        env_file=ENV_FILES,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
