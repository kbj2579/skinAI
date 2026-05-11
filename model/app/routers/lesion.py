"""
병변/점 분류 Mock 라우터
클래스: 정상, 경미, 의심(suspicious), 위험(danger) (4개)

suspicious / danger → backend에서 recommend_visit=True 고정
"""
import random
from fastapi import APIRouter, File, UploadFile

router = APIRouter()

LESION_CLASSES = ["정상", "경미", "suspicious", "danger"]
RISK_MAP = {
    "정상": "normal",
    "경미": "mild",
    "suspicious": "suspicious",
    "danger": "danger",
}


@router.post("/predict/lesion")
async def predict(file: UploadFile = File(...)):
    await file.read()

    weights = [0.45, 0.30, 0.15, 0.10]
    top_label = random.choices(LESION_CLASSES, weights=weights)[0]
    top_score = round(random.uniform(0.70, 0.95), 2)

    bbox = []
    if top_label != "정상":
        bbox = [{"x": 120, "y": 80, "w": 40, "h": 40, "label": top_label}]

    return {
        "conditions": [{"label": top_label, "score": top_score}],
        "risk_level": RISK_MAP[top_label],
        "confidence": top_score,
        "bounding_boxes": bbox,
    }
