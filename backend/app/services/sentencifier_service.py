import asyncio
import json
import logging

import boto3
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.tables import Analysis, User, UserCosmetic
from app.schemas.analysis import ModelResult

logger = logging.getLogger(__name__)

DYNAMO_TABLE = "SkinReportTable"
POLL_INTERVAL = 5   # 초
POLL_MAX = 24       # 최대 120초 대기


def _build_user_input(
    model_result: ModelResult,
    body_part: str | None,
    smoking: bool | None,
    drinking: bool | None,
    symptom_description: str | None,
    skin_type: str | None,
    cosmetics: list,
    past_records: list,
) -> str:
    conditions_text = ", ".join(
        f"{c.name}({c.confidence:.0%})" for c in model_result.conditions
    ) or "감지 없음"

    cosmetics_text = "; ".join(
        f"{c['product_name']} (사용 시작: {c['start_date']})" for c in cosmetics
    ) or "없음"

    past_lines = "\n".join(
        f"- {r['record_date']}: 위험도={r['risk_level']}, 상태={r['conditions']}"
        for r in past_records
    ) or "없음"

    return (
        f"[피부 AI 분석 결과]\n"
        f"위험도: {model_result.risk_level}\n"
        f"감지 상태: {conditions_text}\n"
        f"신뢰도: {model_result.confidence:.1%}\n"
        f"\n"
        f"[사용자 설문]\n"
        f"분석 부위: {body_part or '미지정'}\n"
        f"흡연: {'예' if smoking else '아니오'}\n"
        f"음주: {'예' if drinking else '아니오'}\n"
        f"증상: {symptom_description or '없음'}\n"
        f"\n"
        f"[피부 프로필]\n"
        f"피부 타입: {skin_type or '미지정'}\n"
        f"사용 화장품: {cosmetics_text}\n"
        f"\n"
        f"[과거 분석 이력]\n"
        f"{past_lines}\n"
    )


def _make_boto_client(service: str):
    return boto3.client(
        service,
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id or None,
        aws_secret_access_key=settings.aws_secret_access_key or None,
    )


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
    user_input = _build_user_input(
        model_result, body_part, smoking, drinking,
        symptom_description, skin_type, cosmetics, past_records,
    )

    try:
        # Step Functions 직접 실행
        sfn = _make_boto_client("stepfunctions")
        execution = await asyncio.to_thread(
            sfn.start_execution,
            stateMachineArn=settings.step_functions_arn,
            input=json.dumps({"user_input": user_input, "uuid": report_id}, ensure_ascii=False),
        )
        execution_arn = execution["executionArn"]
        logger.info("Step Functions started (uuid=%s): %s", report_id, execution_arn)

        # DynamoDB 폴링 — Step Functions가 완료되면 ReportId=record_id 로 저장
        dynamodb = boto3.resource(
            "dynamodb",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id or None,
            aws_secret_access_key=settings.aws_secret_access_key or None,
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
