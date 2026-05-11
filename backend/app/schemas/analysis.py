from datetime import datetime
from pydantic import BaseModel


class ConditionItem(BaseModel):
    label: str
    score: float


class BoundingBox(BaseModel):
    x: float
    y: float
    w: float
    h: float
    label: str


class ModelResult(BaseModel):
    conditions: list[ConditionItem]
    risk_level: str          # normal | mild | suspicious | danger
    confidence: float
    bounding_boxes: list[BoundingBox] = []


class SkinMetrics(BaseModel):
    """분석 결과에서 도출된 정량화 피부 지표 (0~100)"""
    oiliness: float    # 유분도
    moisture: float    # 수분도
    trouble: float     # 트러블 정도
    sensitivity: float # 민감도


class AnalysisResponse(BaseModel):
    id: int
    analysis_type: str
    risk_level: str
    conditions: list[ConditionItem]
    confidence: float
    skin_metrics: SkinMetrics | None = None
    gemini_explanation: str | None
    recommend_visit: bool
    visit_message: str | None
    is_diagnostic: bool
    disclaimer: str
    created_at: datetime

    model_config = {"from_attributes": True}
