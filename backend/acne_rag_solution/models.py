from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


CLASS_DISPLAY_KO = {
    # Legacy MVP labels kept for backward compatibility.
    "Blackheads": "블랙헤드",
    "Whiteheads": "화이트헤드",
    "Papules": "구진",
    "Pustules": "농포",
    "Cyst": "낭종성 병변",
    # Hierarchical multi-head v1 labels.
    "blackhead": "블랙헤드",
    "whitehead": "화이트헤드",
    "papule": "구진",
    "pustule": "농포",
    "cystnnodule": "결절+낭종",
    "complexacne": "복합-미분류 여드름",
    "milia": "비립종",
    "rosacea": "주사",
    "seborrheic": "지루",
    "sebdermatitis": "지루성 피부염",
    "atopic": "아토피 피부염",
    "psoriasis": "건선",
    "normal": "정상",
    "abnormal": "비정상/미분류",
}

CLASS_GROUPS = {
    "Blackheads": "comedonal_acne",
    "Whiteheads": "comedonal_acne",
    "Papules": "inflammatory_acne",
    "Pustules": "inflammatory_acne",
    "Cyst": "deep_inflammatory_acne",
    "blackhead": "comedonal_acne",
    "whitehead": "comedonal_acne",
    "papule": "inflammatory_acne",
    "pustule": "inflammatory_acne",
    "cystnnodule": "deep_inflammatory_acne",
    "complexacne": "complex_acne",
    "milia": "milia",
    "rosacea": "rosacea",
    "seborrheic": "seborrheic_condition",
    "sebdermatitis": "seborrheic_dermatitis",
    "atopic": "atopic_dermatitis",
    "psoriasis": "psoriasis",
    "normal": "normal_skin",
    "abnormal": "abnormal_uncertain",
}

VALID_LABELS = set(CLASS_DISPLAY_KO)


@dataclass(frozen=True)
class Prediction:
    pred_label: str
    confidence: float | None = None
    pred_label_ko: str | None = None
    top_k_probabilities: dict[str, float] = field(default_factory=dict)
    model_version: str = "unknown"
    image_id: str = "unknown"

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Prediction":
        label = str(payload.get("pred_label") or payload.get("label") or "").strip()
        if label not in VALID_LABELS:
            raise ValueError(
                f"pred_label must be one of {sorted(VALID_LABELS)}; got {label!r}"
            )
        confidence_value = payload.get("confidence")
        confidence = None
        if confidence_value is not None:
            confidence = float(confidence_value)
            if not 0.0 <= confidence <= 1.0:
                raise ValueError("confidence must be between 0 and 1")
        top_k = payload.get("top_k_probabilities") or payload.get("probabilities") or {}
        return cls(
            pred_label=label,
            confidence=confidence,
            pred_label_ko=payload.get("pred_label_ko") or CLASS_DISPLAY_KO[label],
            top_k_probabilities={str(k): float(v) for k, v in top_k.items()},
            model_version=str(payload.get("model_version", "unknown")),
            image_id=str(payload.get("image_id", "unknown")),
        )

    def to_standard_dict(self) -> dict[str, Any]:
        return {
            "pred_label": self.pred_label,
            "pred_label_ko": self.pred_label_ko or CLASS_DISPLAY_KO[self.pred_label],
            "confidence": self.confidence,
            "top_k_probabilities": self.top_k_probabilities,
            "model_version": self.model_version,
            "image_id": self.image_id,
            "class_group": CLASS_GROUPS[self.pred_label],
        }


@dataclass(frozen=True)
class EvidenceChunk:
    id: str
    title: str
    source: str
    url: str
    license: str
    allowed_use: str
    last_checked: str
    class_tags: tuple[str, ...]
    topic_tags: tuple[str, ...]
    chunk_text: str
    citation_note: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "EvidenceChunk":
        required = [
            "id",
            "title",
            "source",
            "url",
            "license",
            "allowed_use",
            "last_checked",
            "class_tags",
            "topic_tags",
            "chunk_text",
            "citation_note",
        ]
        missing = [key for key in required if key not in payload]
        if missing:
            raise ValueError(f"evidence chunk missing required fields: {missing}")
        return cls(
            id=str(payload["id"]),
            title=str(payload["title"]),
            source=str(payload["source"]),
            url=str(payload["url"]),
            license=str(payload["license"]),
            allowed_use=str(payload["allowed_use"]),
            last_checked=str(payload["last_checked"]),
            class_tags=tuple(str(x) for x in payload["class_tags"]),
            topic_tags=tuple(str(x) for x in payload["topic_tags"]),
            chunk_text=str(payload["chunk_text"]),
            citation_note=str(payload["citation_note"]),
        )

    def citation(self) -> dict[str, str]:
        return {
            "id": self.id,
            "title": self.title,
            "source": self.source,
            "url": self.url,
            "license": self.license,
            "allowed_use": self.allowed_use,
            "note": self.citation_note,
        }
