import asyncio
import json
import logging

import boto3
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.tables import Analysis, User, UserCosmetic
from app.schemas.analysis import ModelResult

logger = logging.getLogger(__name__)

DYNAMO_TABLE = "SkinReportTable"
POLL_INTERVAL = 3   # 초
POLL_MAX = 20       # 최대 60초 대기


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

    report_id = str(record_id)

    # Step Functions expects user_input + uuid
    user_input_data = {
        "analysis_result": {
            "risk_level": model_result.risk_level,
            "conditions": [c.model_dump() for c in model_result.conditions],
            "confidence": model_result.confidence,
        },
        "survey_data": {
            "body_part": body_part or "",
            "smoking": smoking,
            "drinking": drinking,
            "symptom_description": symptom_description or "",
        },
        "user_profile": {
            "skin_type": skin_type or "",
            "cosmetics": cosmetics,
        },
        "past_records": past_records,
    }

    payload = {
        "user_input": json.dumps(user_input_data, ensure_ascii=False),
        "uuid": report_id,
    }

    try:
        # 1. Step Functions 실행 시작
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(settings.sentencifier_url, json=payload)
            response.raise_for_status()
        logger.info("Sentencifier triggered (status=%s): %s", response.status_code, str(response.text)[:200])

        # 2. DynamoDB 폴링 — ReportId = str(record_id)
        dynamodb = boto3.resource(
            "dynamodb",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
        table = dynamodb.Table(DYNAMO_TABLE)

        for attempt in range(POLL_MAX):
            await asyncio.sleep(POLL_INTERVAL)
            result = await asyncio.to_thread(
                table.get_item,
                Key={"ReportId": report_id},
            )
            item = result.get("Item")
            if item and item.get("FinalReport"):
                report = str(item["FinalReport"]).strip()
                logger.info("DynamoDB report found (attempt %d) — %d chars", attempt + 1, len(report))
                return report or None
            logger.debug("DynamoDB polling %d/%d (ReportId=%s)...", attempt + 1, POLL_MAX, report_id)

        logger.warning("DynamoDB polling timed out after %ds (ReportId=%s)", POLL_INTERVAL * POLL_MAX, report_id)
        return None

    except Exception as exc:
        logger.warning("Sentencifier failed (%s) — using fallback", exc)
        return None
