import hashlib
import logging

import google.generativeai as genai

from app.core.config import settings
from app.schemas.analysis import ModelResult, SkinMetrics

logger = logging.getLogger(__name__)

# ── 메모리 캐시 ────────────────────────────────────────────────────
_cache: dict[str, str] = {}

FALLBACK_MESSAGE = (
    "현재 AI 설명 서비스를 일시적으로 이용할 수 없습니다. "
    "분석 결과의 위험도를 참고하여 주시고, 이상이 지속되면 전문의와 상담하세요. "
    "본 결과는 AI 보조 분석이며 의학적 진단이 아닙니다."
)

DISCLAIMER = (
    "본 결과는 AI 보조 분석이며 의학적 진단이 아닙니다. "
    "증상이 지속되거나 심해지면 전문의와 상담하세요."
)

SYSTEM_PROMPT = """당신은 피부·두피 건강 관리 보조 AI입니다.
분석 결과를 일반인이 쉽게 이해할 수 있는 언어로 설명하고, 실천 가능한 관리 방법을 안내합니다.
의학적 진단을 절대 내리지 않으며, 모든 설명 말미에 반드시 면책 문구를 포함합니다.
과거 이력이 있을 경우 상태 변화 추이를 친절하게 언급합니다."""

# ── 조건 키워드 → 피부 지표 영향도 매핑 ──────────────────────────────
# (키워드, 유분 delta, 수분 delta, 트러블 delta, 민감도 delta)
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

# risk_level 기준 베이스값 (유분, 수분, 트러블, 민감도)
_RISK_BASE: dict[str, tuple[float, float, float, float]] = {
    "normal":     (30, 60, 10, 15),
    "mild":       (45, 45, 30, 30),
    "suspicious": (60, 35, 55, 50),
    "danger":     (70, 25, 75, 65),
}


def compute_skin_metrics(model_result: ModelResult) -> SkinMetrics:
    """모델 분류 결과에서 정량화 피부 지표(0~100)를 산출합니다."""
    base = _RISK_BASE.get(model_result.risk_level, _RISK_BASE["mild"])
    oil, moist, trouble, sensitive = base

    for condition in model_result.conditions:
        label = condition.label.lower()
        weight = condition.score  # 0~1
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


def _make_cache_key(model_result: ModelResult, analysis_type: str) -> str:
    conditions_str = ",".join(
        f"{c.label}:{c.score:.2f}" for c in model_result.conditions
    )
    raw = f"{analysis_type}:{model_result.risk_level}:{conditions_str}"
    return hashlib.md5(raw.encode()).hexdigest()


def _build_prompt(
    model_result: ModelResult,
    metrics: SkinMetrics,
    analysis_type: str,
    recommend_visit: bool,
    db_history: str,
) -> str:
    conditions_str = ", ".join(
        f"{c.label}({c.score:.0%})" for c in model_result.conditions
    )
    type_label = {"skin": "안면피부", "scalp": "두피", "lesion": "병변"}.get(
        analysis_type, analysis_type
    )
    history_section = (
        f"\n과거 분석 이력 (최근 3건): {db_history}\n"
        "→ 과거 이력과 비교하여 상태 변화 추이를 간략히 언급해 주세요."
        if db_history
        else ""
    )
    visit_section = "\n3. 전문의 방문 권장 문구 (1문장, 반드시 포함)" if recommend_visit else ""
    final_num = "4" if recommend_visit else "3"

    return f"""분석 유형: {type_label}
감지된 상태: {conditions_str}
위험도: {model_result.risk_level}  |  신뢰도: {model_result.confidence:.0%}

[정량화 피부 지표]
- 유분도:  {metrics.oiliness}/100
- 수분도:  {metrics.moisture}/100
- 트러블:  {metrics.trouble}/100
- 민감도:  {metrics.sensitivity}/100
{history_section}
아래 항목을 순서대로 작성해 주세요:

1. 현재 {type_label} 상태 설명 (2~3문장)
   · 유분도·수분도·트러블 수치를 자연스럽게 녹여 설명할 것
2. 지금 바로 실천 가능한 관리 방법 3가지 (번호 목록, 구체적으로){visit_section}
{final_num}. 면책 문구 (마지막 줄 고정): "{DISCLAIMER}"
"""


def explain(
    model_result: ModelResult,
    analysis_type: str,
    recommend_visit: bool,
    db_history: str = "",
) -> tuple[str, SkinMetrics]:
    """
    Gemini 피부 상태 설명 + 정량화 지표 반환.
    Returns: (explanation_text, SkinMetrics)
    """
    metrics = compute_skin_metrics(model_result)
    cache_key = _make_cache_key(model_result, analysis_type)

    if cache_key in _cache:
        logger.debug("Gemini cache hit: %s", cache_key)
        return _cache[cache_key], metrics

    if not settings.gemini_api_key:
        return FALLBACK_MESSAGE, metrics

    try:
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=SYSTEM_PROMPT,
        )
        prompt = _build_prompt(
            model_result, metrics, analysis_type, recommend_visit, db_history
        )
        response = model.generate_content(prompt)
        result = response.text.strip()
        _cache[cache_key] = result
        logger.info("Gemini OK — %d chars", len(result))
        return result, metrics

    except Exception as e:
        logger.warning("Gemini failed (%s) — fallback", e)
        return FALLBACK_MESSAGE, metrics
