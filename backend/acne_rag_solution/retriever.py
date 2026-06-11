from __future__ import annotations

import re
from dataclasses import dataclass

from .corpus import generation_allowed
from .models import CLASS_GROUPS, EvidenceChunk, Prediction

LABEL_TAG_ALIASES = {
    "Blackheads": {"blackhead", "blackheads"},
    "Whiteheads": {"whitehead", "whiteheads"},
    "Papules": {"papule", "papules"},
    "Pustules": {"pustule", "pustules"},
    "Cyst": {"cyst", "cysts", "cystnnodule", "nodule"},
    "blackhead": {"Blackheads", "blackheads"},
    "whitehead": {"Whiteheads", "whiteheads"},
    "papule": {"Papules", "papules"},
    "pustule": {"Pustules", "pustules"},
    "cystnnodule": {"Cyst", "cyst", "nodule", "nodular_acne"},
}

RED_FLAG_TERMS = {
    "통증",
    "아픔",
    "악화",
    "출혈",
    "피",
    "열",
    "발열",
    "부기",
    "붓기",
    "고름",
    "흉터",
    "빠르게",
    "퍼짐",
    "감염",
    "pain",
    "bleeding",
    "fever",
    "swelling",
    "scar",
    "worse",
    "infection",
}

INGREDIENT_TERMS = {
    "성분",
    "추천",
    "제품",
    "ingredient",
    "ingredients",
    "salicylic",
    "benzoyl",
    "peroxide",
    "adapalene",
    "retinoid",
    "azelaic",
    "niacinamide",
    "nicotinamide",
    "살리실산",
    "벤조일",
    "아다팔렌",
    "레티노이드",
    "아젤라익산",
    "나이아신아마이드",
}


@dataclass(frozen=True)
class RetrievedChunk:
    chunk: EvidenceChunk
    score: float
    matched_terms: tuple[str, ...]


def tokenize(text: str) -> set[str]:
    normalized = text.lower()
    return set(re.findall(r"[a-z0-9가-힣_]+", normalized))


def retrieve(
    prediction: Prediction,
    corpus: list[EvidenceChunk],
    user_symptoms: str = "",
    top_k: int = 5,
    include_citation_only: bool = False,
) -> list[RetrievedChunk]:
    label = prediction.pred_label
    class_group = CLASS_GROUPS[label]
    is_acne_group = class_group in {
        "comedonal_acne",
        "inflammatory_acne",
        "deep_inflammatory_acne",
        "complex_acne",
    }
    label_aliases = {label, label.lower(), *LABEL_TAG_ALIASES.get(label, set())}
    normalized_label_aliases = {item.lower() for item in label_aliases}
    symptoms_tokens = tokenize(user_symptoms)
    red_flags = symptoms_tokens & RED_FLAG_TERMS
    ingredient_terms = symptoms_tokens & INGREDIENT_TERMS
    query_terms = {*normalized_label_aliases, class_group, *symptoms_tokens}

    results: list[RetrievedChunk] = []
    for chunk in corpus:
        if not include_citation_only and not generation_allowed(chunk):
            continue

        score = 0.0
        matches: set[str] = set()
        tag_set = {tag.lower() for tag in (*chunk.class_tags, *chunk.topic_tags)}
        label_match = bool(tag_set & normalized_label_aliases)
        group_match = class_group in tag_set
        all_acne_match = is_acne_group and "all_acne_classes" in tag_set
        all_skin_match = "all_skin_classes" in tag_set
        relevant_to_prediction = label_match or group_match or all_acne_match or all_skin_match

        if label_match:
            score += 6.0
            matches.add(label)
        if group_match:
            score += 4.0
            matches.add(class_group)
        if all_acne_match:
            score += 1.5
            matches.add("all_acne_classes")
        if all_skin_match:
            score += 1.0
            matches.add("all_skin_classes")
        if red_flags and ("red_flags" in tag_set or "safety" in tag_set):
            score += 3.0
            matches.update(sorted(red_flags))
        if relevant_to_prediction and (
            "beneficial_ingredients" in tag_set or "active_ingredients" in tag_set
        ):
            score += 1.25
            matches.add("beneficial_ingredients")
            if label_match:
                score += 2.0
        if relevant_to_prediction and "ingredient_safety" in tag_set:
            score += 0.75
            matches.add("ingredient_safety")
        if ingredient_terms and relevant_to_prediction and (
            "beneficial_ingredients" in tag_set
            or "ingredient_safety" in tag_set
            or "active_ingredients" in tag_set
        ):
            score += 3.5
            matches.update(sorted(ingredient_terms))

        text_terms = tokenize(chunk.chunk_text)
        shared = query_terms & text_terms
        if shared and relevant_to_prediction:
            score += min(len(shared), 5) * 0.4
            matches.update(sorted(shared))

        if score > 0:
            results.append(RetrievedChunk(chunk=chunk, score=score, matched_terms=tuple(sorted(matches))))

    results.sort(key=lambda item: (-item.score, item.chunk.id))
    return results[:top_k]
