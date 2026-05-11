from datetime import datetime
from pydantic import BaseModel

from app.schemas.analysis import ConditionItem


class RecordSummary(BaseModel):
    id: int
    analysis_type: str
    risk_level: str
    confidence: float | None
    recommend_visit: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class RecordDetail(BaseModel):
    id: int
    analysis_type: str
    risk_level: str
    conditions: list[ConditionItem] | None
    confidence: float | None
    skin_metrics: dict | None = None
    gemini_explanation: str | None
    recommend_visit: bool
    is_diagnostic: bool
    disclaimer: str
    created_at: datetime

    model_config = {"from_attributes": True}


class RecordListResponse(BaseModel):
    total: int
    items: list[RecordSummary]


class LesionTrackCreate(BaseModel):
    track_name: str


class LesionTrackResponse(BaseModel):
    id: int
    track_name: str | None

    model_config = {"from_attributes": True}


class LesionAnalysisSummary(BaseModel):
    id: int
    risk_level: str | None
    asymmetry_score: float | None
    border_score: float | None
    color_variance: float | None
    size_mm: float | None
    created_at: datetime

    model_config = {"from_attributes": True}
