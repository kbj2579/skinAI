import asyncio
import logging

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.tables import Analysis, User, UserCosmetic
from app.schemas.analysis import ModelResult

logger = logging.getLogger(__name__)


def _build_agent_payload(
    model_result: ModelResult,
    body_part: str | None,
    smoking: bool | None,
    drinking: bool | None,
    symptom_description: str | None,
    skin_type: str | None,
    cosmetics: list,
    past_records: list,
    record_id: int,
) -> dict:
    conditions_text = ", ".join(
        f"{c.label}({c.score:.0%})" for c in model_result.conditions
    ) or "감지 없음"

    return {
        "agent_a_result": {
            "risk_level": model_result.risk_level,
            "conditions": [{"label": c.label, "score": c.score} for c in model_result.conditions],
            "confidence": model_result.confidence,
            "conditions_text": conditions_text,
        },
        "agent_b_result": {
            "past_records": past_records,
            "cosmetics": cosmetics,
        },
        "agent_c_result": {
            "skin_type": skin_type or "",
            "cosmetics": cosmetics,
            "body_part": body_part or "",
            "smoking": smoking,
            "drinking": drinking,
            "symptom_description": symptom_description or "",
        },
        "uuid": str(record_id),
    }


async def get_final_report(
    model_result: ModelResult,
    record_id: int,
    user_id: int,
    db: AsyncSession,
    body_part: str | None = None,
    smoking: bool | None = None,
    drinking: bool | None = None,
    symptom_description: str | None = None,
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

    payload = _build_agent_payload(
        model_result, body_part, smoking, drinking,
        symptom_description, skin_type, cosmetics, past_records, record_id,
    )

    try:
        # sentencifier Lambda URL 직접 호출
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(settings.sentencifier_url, json=payload)
            response.raise_for_status()

        data = response.json()
        report = data.get("final_report", "")
        if report and report.strip():
            logger.info("Sentencifier report received (%d chars) for record %d", len(report), record_id)
            return report.strip()

        logger.warning("Sentencifier returned empty report for record %d", record_id)
        return None

    except Exception as exc:
        logger.warning("Sentencifier failed (%s) — using fallback", exc)
        return None
