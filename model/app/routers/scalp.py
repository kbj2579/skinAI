"""
두피 분류 Mock 라우터
클래스: 미세각질, 피지과다, 비듬, 탈모, 정상 (5개)
"""
import random
from fastapi import APIRouter, File, UploadFile

router = APIRouter()

SCALP_CLASSES = ["미세각질", "피지과다", "비듬", "탈모", "정상"]
RISK_MAP = {
    "미세각질": "mild",
    "피지과다": "mild",
    "비듬": "mild",
    "탈모": "suspicious",
    "정상": "normal",
}


@router.post("/predict/scalp")
async def predict(file: UploadFile = File(...)):
    await file.read()

    weights = [0.15, 0.15, 0.15, 0.1, 0.45]
    top_label = random.choices(SCALP_CLASSES, weights=weights)[0]
    top_score = round(random.uniform(0.70, 0.95), 2)

    conditions = [{"label": top_label, "score": top_score}]
    if top_label != "정상":
        secondary = random.choice([c for c in SCALP_CLASSES if c != top_label])
        conditions.append({"label": secondary, "score": round(random.uniform(0.1, 0.4), 2)})

    return {
        "conditions": conditions,
        "risk_level": RISK_MAP[top_label],
        "confidence": top_score,
        "bounding_boxes": [],
    }
