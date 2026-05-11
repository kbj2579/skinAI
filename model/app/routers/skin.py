"""
피부(얼굴) 분류 Mock 라우터
클래스: 피부염, 아토피, 건선, 주사, 지루성피부염, 정상 (6개)

실 모델 연동 시 이 파일의 predict() 내부만 교체:
  1. 이미지 bytes → 전처리
  2. 모델 추론
  3. 동일 포맷으로 반환
"""
import random
from fastapi import APIRouter, File, UploadFile

router = APIRouter()

SKIN_CLASSES = ["피부염", "아토피", "건선", "주사", "지루성피부염", "정상"]
RISK_MAP = {
    "피부염": "mild",
    "아토피": "mild",
    "건선": "suspicious",
    "주사": "mild",
    "지루성피부염": "normal",
    "정상": "normal",
}


@router.post("/predict/skin")
async def predict(file: UploadFile = File(...)):
    await file.read()  # 실 모델에서는 여기서 추론

    # Mock: 랜덤 결과 (정상 비중 높게)
    weights = [0.15, 0.15, 0.1, 0.1, 0.15, 0.35]
    top_label = random.choices(SKIN_CLASSES, weights=weights)[0]
    top_score = round(random.uniform(0.70, 0.95), 2)

    conditions = [{"label": top_label, "score": top_score}]
    if top_label != "정상":
        secondary = random.choice([c for c in SKIN_CLASSES if c != top_label])
        conditions.append({"label": secondary, "score": round(random.uniform(0.1, 0.4), 2)})

    risk_level = RISK_MAP[top_label]

    return {
        "conditions": conditions,
        "risk_level": risk_level,
        "confidence": top_score,
        "bounding_boxes": [],
    }
