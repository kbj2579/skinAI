import asyncio
import logging

import boto3
from botocore.exceptions import ClientError
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

DISCLAIMER = (
    "본 결과는 AI 보조 분석이며 의학적 진단이 아닙니다. "
    "증상이 지속되거나 심해지면 전문의와 상담하세요."
)


def _build_prompt(
    model_result: ModelResult,
    past_records: list,
    cosmetics: list,
    skin_type: str | None,
    body_part: str | None,
    smoking: bool | None,
    drinking: bool | None,
    symptom_description: str | None,
) -> str:
    conditions_str = ", ".join(
        f"{LABEL_KO.get(c.label, c.label)}({c.score:.0%})"
        for c in model_result.conditions
    ) or "감지 없음"
    risk_ko = RISK_KO.get(model_result.risk_level, model_result.risk_level)
    lifestyle = []
    if smoking:
        lifestyle.append("흡연자")
    if drinking:
        lifestyle.append("음주자")
    lifestyle_str = ", ".join(lifestyle) if lifestyle else "해당 없음"

    lines = [
        "당신은 피부 전문 AI 상담사입니다.",
        "아래 피부 분석 데이터를 바탕으로 사용자에게 맞춤형 피부 케어 리포트를 한국어로 작성해주세요.",
        "",
        "[피부 분석 데이터]",
        f"- 추정 병변: {conditions_str}",
        f"- 위험도: {risk_ko}",
        f"- 신뢰도: {model_result.confidence:.0%}",
        f"- 분석 부위: {body_part or '미입력'}",
        f"- 사용자 증상: {symptom_description or '없음'}",
        f"- 피부 타입: {skin_type or '미입력'}",
        f"- 생활 습관: {lifestyle_str}",
    ]

    if past_records:
        lines += ["", "[과거 분석 기록 (최근 5건)]"]
        for r in past_records:
            conds = r.get('conditions', [])
            cond_text = ", ".join(
                LABEL_KO.get(c.get('label', ''), c.get('label', '')) for c in conds
            ) if conds else "없음"
            lines.append(
                f"- {r['record_date']}: {RISK_KO.get(r['risk_level'], r['risk_level'])} ({cond_text})"
            )
    else:
        lines += ["", "[과거 분석 기록]", "- 없음 (첫 분석)"]

    if cosmetics:
        lines += ["", "[현재 사용 중인 화장품]"]
        for c in cosmetics:
            lines.append(f"- {c['product_name']} (사용 시작: {c.get('start_date', '')})")
    else:
        lines += ["", "[현재 사용 중인 화장품]", "- 등록된 화장품 없음"]

    lines += [
        "",
        "[리포트 작성 지침]",
        "아래 4개 항목을 순서대로 작성하세요. 각 항목은 제목을 포함하고 친절하고 이해하기 쉬운 말투로 작성하세요.",
        "",
        "1. 병변 분석",
        "   - 감지된 병변이 무엇인지, 어떤 상태인지 일반인이 이해하기 쉽게 설명 (2~3문장)",
        "   - 해당 병변의 발생 원인과 특징 설명",
        "   - 이 피부 상태에서 피해야 할 성분이나 제품 유형 1~2가지 언급 (예: 스크럽, 고농도 레티놀 등)",
        "   - 위험도가 suspicious 또는 danger이면 병원 방문 권장 문구 포함",
        "",
        "2. 과거 기록 비교 (과거 기록이 있는 경우에만 작성, 없으면 이 항목 전체 생략)",
        "   - 과거 기록과 현재 상태를 비교하여 개선/악화/유지 여부 설명",
        "   - 상태 변화 표현은 '붉은기 증가', '병변 감소' 등 정성적 표현만 사용, 수치 금지",
        "   - 화장품 사용 시작일과 상태 변화 사이에 연관성이 보이면 언급 (추측임을 명시)",
        "   - 근거 없이 특정 제품을 지목하거나 임의의 성분을 생성하지 않음",
        "",
        "3. 화장품 주의사항 (사용 중인 화장품이 있는 경우에만 작성, 없으면 이 항목 전체 생략)",
        "   - 현재 피부 상태와 피부 타입을 고려했을 때 주의가 필요한 성분 유형 안내",
        "   - 등록된 화장품 중 해당 성분이 포함됐을 가능성이 있는 제품 언급 (단정 금지, 추측 표현 사용)",
        "   - 대안으로 고려할 수 있는 성분 유형 제안",
        "",
        "4. 관리 방법",
        "   - 지금 바로 실천 가능한 피부 관리 방법 3가지를 구체적으로 작성",
        "",
        f"마지막 줄에 반드시 다음 문구를 그대로 포함하세요: \"{DISCLAIMER}\"",
    ]

    return "\n".join(lines)


def _call_bedrock(prompt: str) -> str | None:
    if not settings.use_bedrock_rag:
        return None

    region = settings.aws_region
    model_arn = f"arn:aws:bedrock:{region}::foundation-model/{settings.bedrock_model_id}"

    client = boto3.client(
        "bedrock-agent-runtime",
        region_name=region,
        aws_access_key_id=settings.aws_access_key_id or None,
        aws_secret_access_key=settings.aws_secret_access_key or None,
    )

    try:
        response = client.retrieve_and_generate(
            input={"text": prompt},
            retrieveAndGenerateConfiguration={
                "type": "KNOWLEDGE_BASE",
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": settings.bedrock_knowledge_base_id,
                    "modelArn": model_arn,
                    "retrievalConfiguration": {
                        "vectorSearchConfiguration": {"numberOfResults": 5}
                    },
                    "generationConfiguration": {
                        "promptTemplate": {
                            "textPromptTemplate": (
                                "당신은 피부 전문 AI 상담사입니다. "
                                "아래 의학 문서를 참고하여 사용자의 피부 분석 리포트를 작성해주세요.\n\n"
                                "$search_results$\n\n"
                                "사용자 분석 데이터:\n$query$\n\n"
                                "$output_format_instructions$"
                            )
                        }
                    },
                },
            },
        )
        return response["output"]["text"].strip()
    except ClientError as e:
        logger.warning("Bedrock RAG ClientError: %s", e.response["Error"]["Code"])
        return None
    except Exception as e:
        logger.warning("Bedrock RAG failed: %s", e)
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

    prompt = _build_prompt(
        model_result, past_records, cosmetics, skin_type,
        body_part, smoking, drinking, symptom_description,
    )

    try:
        report = await asyncio.to_thread(_call_bedrock, prompt)
        if report and report.strip():
            logger.info("Final report generated (%d chars) for record %d", len(report), record_id)
            return report.strip()
        logger.warning("Empty report for record %d", record_id)
        return None
    except Exception as exc:
        logger.warning("Final report generation failed: %s", exc)
        return None
