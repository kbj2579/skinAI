import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.config import settings
from app.core.database import init_database, get_db
from app.routers import analysis, auth, records

logger = logging.getLogger(__name__)

# ── 앱 생명주기 ────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_database()
    logger.info("DB initialized")
    yield

# ── FastAPI 인스턴스 ───────────────────────────────────────────
app = FastAPI(
    title="Skin AI API",
    description="AI 기반 피부·두피·병변 분석 서비스",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# ── Request ID 미들웨어 ────────────────────────────────────────
@app.middleware("http")
async def attach_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# ── 전역 예외 핸들러 ──────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "?")
    logger.error(
        "[%s] Unhandled error on %s: %s",
        request_id, request.url.path, exc,
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
            "request_id": request_id,
        },
    )

# ── 라우터 ────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(analysis.router)
app.include_router(records.router)

# ── 기본 엔드포인트 ───────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def root():
    return {"service": "skin-ai-api", "version": "1.0.0"}


@app.get("/health", tags=["system"])
async def health():
    """DB 연결 포함 상태 체크."""
    db_status = "unknown"
    try:
        async for db in get_db():
            await db.execute(text("SELECT 1"))
            db_status = "ok"
            break
    except Exception as e:
        logger.warning("Health check DB error: %s", e)
        db_status = "error"

    overall = "ok" if db_status == "ok" else "degraded"
    return {
        "status": overall,
        "version": "1.0.0",
        "database": db_status,
    }
