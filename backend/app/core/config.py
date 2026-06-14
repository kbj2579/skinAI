from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR  = Path(__file__).resolve().parents[3]   # medical_ai_team3_new/
ENV_FILES = tuple(
    str(p) for p in (ROOT_DIR / ".env", ROOT_DIR / ".env.local") if p.exists()
)


class Settings(BaseSettings):
    # ── Database (PostgreSQL 필수) ─────────────────────────────
    database_url: str  # .env의 DATABASE_URL 필수

    # ── AWS 공통 자격증명 ────────────────────────────────────────
    aws_region:            str = "ap-northeast-2"   # 서울 리전
    aws_access_key_id:     str = ""
    aws_secret_access_key: str = ""

    # ── S3 이미지 저장소 ──────────────────────────────────────────
    # AWS S3: storage_endpoint 비워두면 네이티브 S3 사용
    # Cloudflare R2: https://[ID].r2.cloudflarestorage.com
    storage_endpoint:    str = ""
    storage_access_key:  str = ""
    storage_secret_key:  str = ""
    storage_bucket:      str = "skin-ai"
    storage_region:      str = "ap-northeast-2"

    # ── SageMaker ────────────────────────────────────────────────
    # 미설정 시 로컬 모델 서버 → Mock 순으로 fallback
    sagemaker_endpoint_name: str = ""

    # ── 로컬 모델 서버 (SageMaker 미사용 시) ──────────────────────
    ai_model_base_url: str = "http://127.0.0.1:8001"

    # ── ElastiCache Redis ────────────────────────────────────────
    # 미설정 시 메모리 캐시 fallback
    # 예: redis://[ENDPOINT]:6379
    redis_url: str = ""

    # ── Amazon Bedrock RAG ────────────────────────────────────────
    # Knowledge Base ID (미설정 시 Gemini fallback)
    bedrock_knowledge_base_id: str = ""
    # 생성에 사용할 Claude 모델 (기본: Haiku)
    bedrock_model_id: str = "anthropic.claude-3-haiku-20240307-v1:0"

    # ── Sentencifier Lambda ───────────────────────────────────────
    sentencifier_url: str = ""

    # ── JWT ───────────────────────────────────────────────────────
    jwt_secret:         str = "change-this-secret"
    jwt_expire_minutes: int = 60

    # ── CORS ──────────────────────────────────────────────────────
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    model_config = SettingsConfigDict(
        env_file=ENV_FILES,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def use_sagemaker(self) -> bool:
        return bool(self.sagemaker_endpoint_name)

    @property
    def use_redis(self) -> bool:
        return bool(self.redis_url)

    @property
    def use_native_s3(self) -> bool:
        """endpoint 없으면 AWS 네이티브 S3"""
        return not self.storage_endpoint

    @property
    def use_bedrock_rag(self) -> bool:
        return bool(self.bedrock_knowledge_base_id)

    @property
    def use_sentencifier(self) -> bool:
        return bool(self.sentencifier_url)


settings = Settings()
