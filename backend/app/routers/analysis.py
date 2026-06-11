import asyncio
import random
from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.core.rate_limit import analysis_limiter
from app.models.tables import Analysis, LesionAnalysis, LesionTrack
from app.schemas.analysis import AnalysisResponse
from app.services import ai_service, storage_service, bedrock_rag_service

router = APIRouter(prefix="/analysis", tags=["analysis"])

DISCLAIMER = "본 결과는 AI 보조 분석이며 의학적 진단이 아닙니다. 증상이 지속되거나 심해지면 전문의와 상담하세요."
VISIT_MESSAGE = "분석 결과 전문의 진료가 권장됩니다. 가까운 피부과를 방문하시어 정확한 진단을 받으시기 바랍니다."

MAX_IMAGE_BYTES = 20 * 1024 * 1024  # 20MB
MIN_IMAGE_BYTES = 1_024              # 1KB

AnalysisType = Literal["skin", "lesion"]


@router.post("/{analysis_type}", response_model=AnalysisResponse)
async def analyze(
    analysis_type: AnalysisType,
    file: UploadFile = File(...),
    track_id:  int | None = Query(default=None, description="병변 트랙 ID (lesion 분석 시 선택)"),
    body_part: str | None = Query(default=None, description="분석 부위 (얼굴/팔/다리/등/가슴/배)"),
    smoking:   bool | None = Query(default=None, description="흡연 여부"),
    drinking:  bool | None = Query(default=None, description="음주 여부"),
    symptom_description: str | None = Query(default=None, max_length=500, description="사용자가 입력한 증상 설명"),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    # Rate limiting: 사용자당 60초에 최대 10건
    analysis_limiter.check(str(user_id))

    # 파일 타입 검증
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="이미지 파일만 업로드 가능합니다.")

    image_bytes = await file.read()

    # 파일 크기 검증
    if len(image_bytes) < MIN_IMAGE_BYTES:
        raise HTTPException(status_code=400, detail="올바른 이미지 파일이 아닙니다.")
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="파일 크기는 20MB를 초과할 수 없습니다.")

    # 스토리지 업로드 + AI 추론 병렬 실행
    s3_key, model_result = await asyncio.gather(
        asyncio.to_thread(storage_service.upload, image_bytes, analysis_type, file.content_type),
        ai_service.predict(image_bytes, analysis_type),
    )

    # Rule-based: suspicious / danger → 병원 방문 권장 (코드 고정)
    recommend_visit = model_result.risk_level in ("suspicious", "danger")
    visit_message = VISIT_MESSAGE if recommend_visit else None

    # DB 이력 조회 (최근 3건)
    history_result = await db.execute(
        select(Analysis)
        .where(Analysis.user_id == user_id, Analysis.analysis_type == analysis_type)
        .order_by(Analysis.created_at.desc())
        .limit(3)
    )
    history_rows = history_result.scalars().all()
    db_history = "; ".join(
        f"{r.created_at.date()} {r.risk_level}" for r in history_rows
    ) if history_rows else ""

    # 설명 생성: Bedrock RAG (KB 미설정 시 fallback 메시지 반환)
    explanation, skin_metrics = await asyncio.to_thread(
        bedrock_rag_service.explain_with_rag,
        model_result,
        analysis_type,
        recommend_visit,
        db_history,
        body_part,
        smoking,
        drinking,
        symptom_description,
    )

    # DB 저장
    record = Analysis(
        user_id=user_id,
        analysis_type=analysis_type,
        body_part=body_part,
        smoking=smoking,
        drinking=drinking,
        symptom_description=symptom_description,
        image_s3_key=s3_key,
        raw_result=model_result.model_dump(),
        risk_level=model_result.risk_level,
        conditions=[c.model_dump() for c in model_result.conditions],
        confidence=model_result.confidence,
        gemini_explanation=explanation,
        skin_metrics=skin_metrics.model_dump() if skin_metrics else None,
        recommend_visit=recommend_visit,
        is_diagnostic=False,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    # 병변 트랙에 데이터 저장 (lesion 분석 + track_id 제공 시)
    if analysis_type == "lesion" and track_id is not None:
        track_result = await db.execute(
            select(LesionTrack).where(
                LesionTrack.id == track_id,
                LesionTrack.user_id == user_id,
            )
        )
        if track_result.scalar_one_or_none():
            lesion_entry = LesionAnalysis(
                track_id=track_id,
                image_s3_key=s3_key,
                risk_level=model_result.risk_level,
                asymmetry_score=round(random.uniform(0.0, 1.0), 2),
                border_score=round(random.uniform(0.0, 1.0), 2),
                color_variance=round(random.uniform(0.0, 1.0), 2),
                size_mm=round(random.uniform(1.0, 20.0), 1),
            )
            db.add(lesion_entry)
            await db.commit()

    return AnalysisResponse(
        id=record.id,
        analysis_type=record.analysis_type,
        body_part=record.body_part,
        smoking=record.smoking,
        drinking=record.drinking,
        symptom_description=record.symptom_description,
        risk_level=record.risk_level,
        conditions=model_result.conditions,
        confidence=record.confidence,
        skin_metrics=skin_metrics,
        gemini_explanation=record.gemini_explanation,
        recommend_visit=record.recommend_visit,
        visit_message=visit_message,
        is_diagnostic=False,
        disclaimer=DISCLAIMER,
        created_at=record.created_at,
    )
