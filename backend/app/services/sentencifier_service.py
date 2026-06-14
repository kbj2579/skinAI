import asyncio
import json
import logging
import time

import boto3
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.tables import Analysis, User, UserCosmetic
from app.schemas.analysis import ModelResult

logger = logging.getLogger(__name__)

LABEL_KO = {
    'acne': '여드름', 'blackhead': '블랙헤드', 'whitehead': '화이트헤드',
    'papule': '구진', 'pustule': '농포', 'nodule': '결절',
    'cyst': '낭종', 'pigmentation': '색소침착', 'scar': '흉터',
    'normal': '정상', 'abnormal': '피부 이상',
}
RISK_KO = {'mild': '경미', 'moderate': '보통', 'suspicious': '의심', 'danger': '위험'}


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
    """Step Functions → 에이전트에 전달할 user_input 텍스트 구성"""
    conditions_text = ", ".join(
        f"{LABEL_KO.get(c.label, c.label)}({c.score:.0%})"
        for c in model_result.conditions
    ) or "감지 없음"

    lines = [
        "[피부 분석 결과]",
        f"위험도: {RISK_KO.get(model_result.risk_level, model_result.risk_level)}",
        f"감지 병변: {conditions_text}",
        f"신뢰도: {model_result.confidence:.0%}",
        f"분석 부위: {body_part or '미입력'}",
        f"증상 설명: {symptom_description or '없음'}",
        f"흡연: {'예' if smoking else '아니오'}, 음주: {'예' if drinking else '아니오'}",
        "",
        "[사용자 정보]",
        f"피부 타입: {skin_type or '미입력'}",
    ]

    lines.append("")
    lines.append("[사용 중인 화장품]")
    if cosmetics:
        for c in cosmetics:
            lines.append(f"- {c['product_name']} (사용 시작: {c.get('start_date', '')})")
    else:
        lines.append("- 없음")

    lines.append("")
    lines.append("[과거 분석 기록 (최근 5건)]")
    if past_records:
        for r in past_records:
            conds = r.get('conditions', [])
            cond_text = ", ".join(
                LABEL_KO.get(c.get('label', ''), c.get('label', '')) for c in conds
            ) if conds else '없음'
            lines.append(
                f"- {r['record_date']}: "
                f"{RISK_KO.get(r['risk_level'], r['risk_level'])} ({cond_text})"
            )
    else:
        lines.append("- 없음 (첫 분석)")

    return "\n".join(lines)


def _build_direct_payload(
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
    """직접 Lambda 호출용 payload (Step Functions 미사용 시 fallback)"""
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


async def _run_step_functions(user_input: str, record_id: int) -> str | None:
    """Step Functions 비동기 실행 후 DynamoDB 폴링으로 최종 리포트 수신"""
    sf = boto3.client(
        'stepfunctions',
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id or None,
        aws_secret_access_key=settings.aws_secret_access_key or None,
    )
    dynamo = boto3.resource(
        'dynamodb',
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id or None,
        aws_secret_access_key=settings.aws_secret_access_key or None,
    )
    table = dynamo.Table('SkinReportTable')

    execution_name = f"analysis-{record_id}-{int(time.time())}"
    sf.start_execution(
        stateMachineArn=settings.step_functions_arn,
        name=execution_name,
        input=json.dumps({
            "user_input": user_input,
            "uuid": str(record_id),
        }),
    )
    logger.info("Step Functions started: %s for record %d", execution_name, record_id)

    # 최대 120초 대기 (3초 간격 × 40회)
    for attempt in range(40):
        await asyncio.sleep(3)
        resp = await asyncio.to_thread(
            table.get_item, Key={"ReportId": str(record_id)}
        )
        item = resp.get("Item")
        if item and item.get("FinalReport"):
            logger.info(
                "Step Functions result received (attempt %d) for record %d",
                attempt + 1, record_id,
            )
            return item["FinalReport"]

    logger.warning("Step Functions polling timeout for record %d", record_id)
    return None


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

    # DB 조회
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

    cosmetics_result = await db.execute(
        select(UserCosmetic)
        .where(UserCosmetic.user_id == user_id)
        .order_by(UserCosmetic.start_date.desc())
    )
    cosmetics = [
        {"product_name": c.product_name, "start_date": str(c.start_date)}
        for c in cosmetics_result.scalars().all()
    ]

    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    skin_type = user.skin_type if user else None

    try:
        if settings.step_functions_arn:
            # Step Functions 경로
            user_input = _build_user_input(
                model_result, body_part, smoking, drinking,
                symptom_description, skin_type, cosmetics, past_records,
            )
            report = await _run_step_functions(user_input, record_id)
        else:
            # 직접 Lambda 호출 fallback
            payload = _build_direct_payload(
                model_result, body_part, smoking, drinking,
                symptom_description, skin_type, cosmetics, past_records, record_id,
            )
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(settings.sentencifier_url, json=payload)
                response.raise_for_status()
            report = response.json().get("final_report", "")

        if report and report.strip():
            logger.info("Final report received (%d chars) for record %d", len(report), record_id)
            return report.strip()

        logger.warning("Empty report for record %d", record_id)
        return None

    except Exception as exc:
        logger.warning("Sentencifier/StepFunctions failed (%s)", exc)
        return None
