import hashlib
import random

from app.schemas.analysis import BoundingBox, ConditionItem, ModelResult


MOCK_CONFIG: dict[str, list[dict[str, object]]] = {
    "skin": [
        {"label": "정상", "risk": "normal", "weight": 4.0},
        {"label": "여드름", "risk": "mild", "weight": 2.0},
        {"label": "민감성", "risk": "mild", "weight": 1.5},
        {"label": "건조", "risk": "mild", "weight": 1.5},
        {"label": "홍조", "risk": "suspicious", "weight": 1.0},
        {"label": "색소침착", "risk": "mild", "weight": 1.0},
    ],
    "scalp": [
        {"label": "정상", "risk": "normal", "weight": 4.5},
        {"label": "미세각질", "risk": "mild", "weight": 2.0},
        {"label": "지성두피", "risk": "mild", "weight": 2.0},
        {"label": "비듬", "risk": "mild", "weight": 1.5},
        {"label": "탈모", "risk": "suspicious", "weight": 1.0},
    ],
    "lesion": [
        {"label": "정상", "risk": "normal", "weight": 4.5},
        {"label": "경계성 병변", "risk": "mild", "weight": 2.5},
        {"label": "주의 병변", "risk": "suspicious", "weight": 1.5},
        {"label": "고위험 병변", "risk": "danger", "weight": 1.0},
    ],
}


def _seed_for(image_bytes: bytes, analysis_type: str) -> int:
    digest = hashlib.sha256(image_bytes + analysis_type.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def predict(image_bytes: bytes, analysis_type: str) -> ModelResult:
    candidates = MOCK_CONFIG.get(analysis_type)
    if not candidates:
        raise ValueError(f"Unsupported analysis type: {analysis_type}")

    rng = random.Random(_seed_for(image_bytes, analysis_type))
    labels = [str(candidate["label"]) for candidate in candidates]
    weights = [float(candidate["weight"]) for candidate in candidates]
    selected = rng.choices(candidates, weights=weights, k=1)[0]

    primary_label = str(selected["label"])
    risk_level = str(selected["risk"])
    confidence = round(rng.uniform(0.72, 0.94), 2)
    conditions = [ConditionItem(label=primary_label, score=confidence)]

    if primary_label != "정상":
        secondary_candidates = [label for label in labels if label != primary_label]
        secondary_label = rng.choice(secondary_candidates)
        secondary_score = round(rng.uniform(0.12, min(0.45, confidence - 0.1)), 2)
        conditions.append(ConditionItem(label=secondary_label, score=secondary_score))

    bounding_boxes: list[BoundingBox] = []
    if analysis_type == "lesion" and risk_level != "normal":
        bounding_boxes.append(
            BoundingBox(
                x=round(rng.uniform(80, 180), 1),
                y=round(rng.uniform(60, 160), 1),
                w=round(rng.uniform(30, 70), 1),
                h=round(rng.uniform(30, 70), 1),
                label=primary_label,
            )
        )

    return ModelResult(
        conditions=conditions,
        risk_level=risk_level,
        confidence=confidence,
        bounding_boxes=bounding_boxes,
    )
