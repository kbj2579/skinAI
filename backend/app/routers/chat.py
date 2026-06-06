import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.core.config import settings
from app.models.tables import Analysis
from app.schemas.chat import ChatRequest, ChatResponse
from app.services import chat_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    if not settings.use_bedrock_rag:
        raise HTTPException(status_code=503, detail="챗봇 서비스를 사용할 수 없습니다.")

    analysis_context = None
    if req.analysis_id:
        result = await db.execute(
            select(Analysis).where(
                Analysis.id == req.analysis_id,
                Analysis.user_id == user_id,
            )
        )
        record = result.scalar_one_or_none()
        if record:
            analysis_context = {
                "analysis_type": record.analysis_type,
                "body_part": record.body_part,
                "smoking": record.smoking,
                "drinking": record.drinking,
                "risk_level": record.risk_level,
                "conditions": record.conditions or [],
                "confidence": record.confidence,
            }

    try:
        reply = await asyncio.to_thread(
            chat_service.chat,
            req.message,
            [m.model_dump() for m in req.history],
            analysis_context,
        )
        return ChatResponse(reply=reply)
    except Exception as e:
        logger.error("Chat error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"챗봇 오류: {e}")
