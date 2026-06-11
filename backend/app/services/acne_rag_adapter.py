from __future__ import annotations

import logging

from acne_rag_solution.models import Prediction, VALID_LABELS
from acne_rag_solution.service import generate_guidance_from_prediction

from app.schemas.analysis import ModelResult

logger = logging.getLogger(__name__)


LABEL_ALIASES: dict[str, str] = {
    "blackhead": "blackhead",
    "blackheads": "blackhead",
    "whitehead": "whitehead",
    "whiteheads": "whitehead",
    "papule": "papule",
    "papules": "papule",
    "pustule": "pustule",
    "pustules": "pustule",
    "cyst": "cystnnodule",
    "cysts": "cystnnodule",
    "nodule": "cystnnodule",
    "nodularacne": "cystnnodule",
    "cystnnodule": "cystnnodule",
    "complexacne": "complexacne",
    "acne": "complexacne",
    "milia": "milia",
    "rosacea": "rosacea",
    "seborrheic": "seborrheic",
    "sebdermatitis": "sebdermatitis",
    "atopic": "atopic",
    "psoriasis": "psoriasis",
    "normal": "normal",
    "abnormal": "abnormal",
    "여드름": "complexacne",
    "트러블": "complexacne",
    "면포": "blackhead",
    "블랙헤드": "blackhead",
    "화이트헤드": "whitehead",
    "구진": "papule",
    "농포": "pustule",
    "결절": "cystnnodule",
    "낭종": "cystnnodule",
    "비립종": "milia",
    "홍조": "rosacea",
    "주사": "rosacea",
    "지루": "seborrheic",
    "지루성피부염": "sebdermatitis",
    "아토피": "atopic",
    "건선": "psoriasis",
    "정상": "normal",
    "민감": "abnormal",
    "건조": "abnormal",
    "색소": "abnormal",
    "색소침착": "abnormal",
}


def _normalize_label(label: str) -> str | None:
    compact = "".join(ch for ch in label.strip().lower() if ch.isalnum())
    if not compact:
        return None
    if compact in VALID_LABELS:
        return compact
    if compact in LABEL_ALIASES:
        return LABEL_ALIASES[compact]

    for key, value in LABEL_ALIASES.items():
        if key in compact:
            return value
    return None


def _primary_label(model_result: ModelResult) -> str:
    for condition in sorted(model_result.conditions, key=lambda item: item.score, reverse=True):
        label = _normalize_label(condition.label)
        if label:
            return label

    if model_result.risk_level == "normal":
        return "normal"
    return "abnormal"


def generate_acne_guidance(
    model_result: ModelResult,
    user_symptoms: str = "",
    *,
    use_bedrock: bool = False,
) -> str | None:
    """Generate guidance through the bundled Acne RAG Solution package."""
    try:
        pred_label = _primary_label(model_result)
        probabilities = {
            normalized: condition.score
            for condition in model_result.conditions
            if (normalized := _normalize_label(condition.label))
        }
        prediction = Prediction.from_dict(
            {
                "pred_label": pred_label,
                "confidence": model_result.confidence,
                "top_k_probabilities": probabilities,
                "model_version": "skinAI-analysis",
                "image_id": "runtime-upload",
            }
        )
        result = generate_guidance_from_prediction(
            prediction,
            user_symptoms=user_symptoms or "",
            use_bedrock=use_bedrock,
        )
        return result.markdown
    except Exception as exc:
        logger.warning("Acne RAG generation failed (%s)", exc)
        return None
