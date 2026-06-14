import logging

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.tables import Analysis, User, UserCosmetic
from app.schemas.analysis import ModelResult

logger = logging.getLogger(__name__)


async def get_final_report(
    model_result: ModelResult,
    record_id: int,
    user_id: int,
    db: AsyncSession,
) -> str | None:
    if not settings.use_sentencifier:
        return None

    # 이전 분석 기록 조회 (최근 5건)
    past_result = await db.execute(
        select(Analysis)
        .where(Analysis.user_id == user_id, Analysis.analysis_type == "skin")
        .order_by(Analysis.created_at.desc())
        .limit(5)
    )
    past_records = [
        {
            "photo_url": r.image_s3_key or "",
            "record_date": r.created_at.strftime("%Y-%m-%d"),
            "risk_level": r.risk_level,
            "conditions": r.conditions or [],
        }
        for r in past_result.scalars().all()
    ]

    # 화장품 목록 조회
    cosmetics_result = await db.execute(
        select(UserCosmetic)
        .where(UserCosmetic.user_id == user_id)
        .order_by(UserCosmetic.start_date.desc())
    )
    cosmetics = [
        {"product_name": c.product_name, "start_date": c.start_date}
        for c in cosmetics_result.scalars().all()
    ]

    # 사용자 피부타입 조회
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    skin_type = user.skin_type if user else None

    payload = {
        "agent_a_result": model_result.model_dump(),
        "agent_b_result": {
            "past_records": past_records,
            "cosmetics": cosmetics,
        },
        "agent_c_result": {
            "skin_type": skin_type or "",
            "cosmetics": cosmetics,
        },
        "uuid": str(record_id),
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(settings.sentencifier_url, json=payload)
            response.raise_for_status()
        data = response.json()
        report = data.get("final_report", "").strip()
        logger.info("Sentencifier OK — %d chars", len(report))
        return report or None
    except Exception as exc:
        logger.warning("Sentencifier failed (%s) — using fallback", exc)
        return None
