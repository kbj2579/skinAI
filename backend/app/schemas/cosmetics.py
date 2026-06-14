from datetime import datetime
from pydantic import BaseModel


class CosmeticCreate(BaseModel):
    product_name: str
    start_date: str  # YYYY-MM-DD


class CosmeticResponse(BaseModel):
    id: int
    product_name: str
    start_date: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SkinTypeUpdate(BaseModel):
    skin_type: str  # 지성 | 건성 | 복합성 | 민감성 | 중성
