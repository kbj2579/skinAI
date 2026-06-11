import logging
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings
from app.schemas.analysis import ModelResult, SkinMetrics
from app.services.acne_rag_adapter import generate_acne_guidance

logger = logging.getLogger(__name__)

FALLBACK_MESSAGE = (
    "현재 AI 설명 서비스를 일시적으로 이용할 수 없습니다. "
    "분석 결과의 위험도를 참고하여 주시고, 이상이 지속되면 전문의와 상담하세요. "
    "본 결과는 AI 보조 분석이며 의학적 진단이 아닙니다."
)

DISCLAIMER = (
    "본 결과는 AI 보조 분석이며 의학적 진단이 아닙니다. "
    "증상이 지속되거나 심해지면 전문의와 상담하세요."
)

# ── 피부 지표 계산 ─────────────────────────────────────────────────

_CONDITION_MAP: list[tuple[str, float, float, float, float]] = [
    ("지루",   +35, -10, +20, +15),
    ("여드름",  +30,  -5, +40, +20),
    ("모낭염",  +20,  -5, +35, +20),
    ("건조",   -20, -35, +10, +25),
    ("각질",   -15, -30,  +5, +20),
    ("건성",   -20, -35,  +5, +20),
    ("홍반",    +5, -10, +15, +35),
    ("민감",    +5, -10, +10, +40),
    ("색소",     0,  -5,  +5, +10),
    ("기미",     0,  -5,  +5, +10),
    ("주름",    -5, -15,   0, +10),
    ("탈모",   +10, -10, +10, +15),
    ("비듬",   +20, -15, +15, +20),
    ("정상",     0,   0,   0,   0),
    ("양호",     0,  +5,  -5,  -5),
]

_RISK_BASE: dict[str, tuple[float, float, float, float]] = {
    "normal":     (30, 60, 10, 15),
    "mild":       (45, 45, 30, 30),
    "suspicious": (60, 35, 55, 50),
    "danger":     (70, 25, 75, 65),
}


def compute_skin_metrics(model_result: ModelResult) -> SkinMetrics:
    base = _RISK_BASE.get(model_result.risk_level, _RISK_BASE["mild"])
    oil, moist, trouble, sensitive = base

    for condition in model_result.conditions:
        label = condition.label.lower()
        weight = condition.score
        for keyword, d_oil, d_moist, d_trouble, d_sens in _CONDITION_MAP:
            if keyword in label:
                oil += d_oil * weight
                moist += d_moist * weight
                trouble += d_trouble * weight
                sensitive += d_sens * weight
                break

    def clamp(v: float) -> float:
        return round(max(0.0, min(100.0, v)), 1)

    return SkinMetrics(
        oiliness=clamp(oil),
        moisture=clamp(moist),
        trouble=clamp(trouble),
        sensitivity=clamp(sensitive),
    )


# ── Bedrock 클라이언트 ─────────────────────────────────────────────

_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client
    _client = boto3.client(
        "bedrock-agent-runtime",
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id or None,
        aws_secret_access_key=settings.aws_secret_access_key or None,
    )
    return _client


def _build_query(
    model_result: ModelResult,
    analysis_type: str,
    body_part: Optional[str],
    smoking: Optional[bool],
    drinking: Optional[bool],
    symptom_description: Optional[str],
    db_history: str,
) -> str:
    type_label = {"skin": "안면피부", "lesion": "병변"}.get(analysis_type, analysis_type)
    conditions_str = ", ".join(
        f"{c.label}({c.score:.0%})" for c in model_result.conditions
    )
    lifestyle = []
    if smoking is True:
        lifestyle.append("흡연자")
    if drinking is True:
        lifestyle.append("음주자")
    lifestyle_str = ", ".join(lifestyle) if lifestyle else "해당 없음"
    history_part = f"\n과거 분석 이력: {db_history}" if db_history else ""

    return f"""피부 분석 결과를 바탕으로 환자에게 설명을 제공해주세요.

[분석 정보]
- 분석 유형: {type_label}
- 부위: {body_part or "미입력"}
- 감지된 상태: {conditions_str}
- 위험도: {model_result.risk_level}
- 신뢰도: {model_result.confidence:.0%}
- 생활 습관: {lifestyle_str}
- 사용자가 입력한 증상 설명: {symptom_description or "미입력"}
{history_part}

[요청 사항]
1. 현재 피부 상태를 일반인이 이해할 수 있게 설명해주세요 (2~3문장).
2. 지금 바로 실천 가능한 관리 방법 3가지를 알려주세요.
3. 다음 면책 문구를 마지막에 반드시 포함하세요: "{DISCLAIMER}"
""".strip()


# ── RAG 설명 생성 ──────────────────────────────────────────────────

def explain_with_rag(
    model_result: ModelResult,
    analysis_type: str,
    recommend_visit: bool,
    db_history: str = "",
    body_part: Optional[str] = None,
    smoking: Optional[bool] = None,
    drinking: Optional[bool] = None,
    symptom_description: Optional[str] = None,
) -> tuple[str, SkinMetrics]:
    """
    Bedrock Knowledge Base RAG로 설명 생성.
    KB 미설정 또는 실패 시 FALLBACK_MESSAGE 반환.
    """
    metrics = compute_skin_metrics(model_result)

    if analysis_type == "skin":
        acne_guidance = generate_acne_guidance(
            model_result,
            user_symptoms=symptom_description or "",
            use_bedrock=False,
        )
        if acne_guidance:
            return acne_guidance, metrics

    if not settings.use_bedrock_rag:
        return FALLBACK_MESSAGE, metrics

    region = settings.aws_region
    model_arn = (
        f"arn:aws:bedrock:{region}::foundation-model/{settings.bedrock_model_id}"
    )
    query = _build_query(
        model_result, analysis_type, body_part, smoking, drinking, symptom_description, db_history
    )

    try:
        client = _get_client()
        response = client.retrieve_and_generate(
            input={"text": query},
            retrieveAndGenerateConfiguration={
                "type": "KNOWLEDGE_BASE",
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": settings.bedrock_knowledge_base_id,
                    "modelArn": model_arn,
                    "retrievalConfiguration": {
                        "vectorSearchConfiguration": {
                            "numberOfResults": 5,
                        }
                    },
                    "generationConfiguration": {
                        "promptTemplate": {
                            "textPromptTemplate": (
                                "당신은 피부 건강 관리 보조 AI입니다. "
                                "아래 검색된 의학 문서를 참고하여 분석 결과를 설명해주세요.\n\n"
                                "$search_results$\n\n"
                                "$output_format_instructions$"
                            )
                        }
                    },
                },
            },
        )
        text = response["output"]["text"].strip()
        logger.info("Bedrock RAG OK — %d chars", len(text))
        return text, metrics

    except ClientError as e:
        logger.warning("Bedrock RAG ClientError (%s)", e.response["Error"]["Code"])
        return FALLBACK_MESSAGE, metrics
    except Exception as e:
        logger.warning("Bedrock RAG failed (%s)", e)
        return FALLBACK_MESSAGE, metrics
