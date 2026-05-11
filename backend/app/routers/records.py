from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.tables import Analysis, LesionTrack, LesionAnalysis
from app.schemas.analysis import ConditionItem
from app.schemas.records import (
    RecordSummary, RecordDetail,
    LesionTrackCreate, LesionTrackResponse, LesionAnalysisSummary,
    RecordListResponse,
)

DISCLAIMER = "본 결과는 AI 보조 분석이며 의학적 진단이 아닙니다. 증상이 지속되거나 심해지면 전문의와 상담하세요."

router = APIRouter(prefix="/records", tags=["records"])


# ── 병변 트랙 (반드시 /{record_id} 보다 앞에 위치) ─────────────

@router.get("/lesion-tracks", response_model=list[LesionTrackResponse])
async def list_tracks(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(LesionTrack).where(LesionTrack.user_id == user_id)
    )
    return result.scalars().all()


@router.post("/lesion-tracks", response_model=LesionTrackResponse, status_code=201)
async def create_track(
    body: LesionTrackCreate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    track = LesionTrack(user_id=user_id, track_name=body.track_name)
    db.add(track)
    await db.commit()
    await db.refresh(track)
    return track


@router.get("/lesion-tracks/{track_id}", response_model=list[LesionAnalysisSummary])
async def get_track_history(
    track_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    track_result = await db.execute(
        select(LesionTrack).where(
            LesionTrack.id == track_id,
            LesionTrack.user_id == user_id,
        )
    )
    if not track_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="트랙을 찾을 수 없습니다.")

    result = await db.execute(
        select(LesionAnalysis)
        .where(LesionAnalysis.track_id == track_id)
        .order_by(LesionAnalysis.created_at.asc())
    )
    return result.scalars().all()


# ── 분석 이력 ──────────────────────────────────────────────────

@router.get("/", response_model=RecordListResponse)
async def list_records(
    analysis_type: str | None = None,
    limit: int = 20,
    offset: int = 0,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    base_query = select(Analysis).where(Analysis.user_id == user_id)
    if analysis_type:
        base_query = base_query.where(Analysis.analysis_type == analysis_type)

    # 전체 건수
    count_result = await db.execute(
        select(func.count()).select_from(base_query.subquery())
    )
    total = count_result.scalar_one()

    # 페이지 데이터
    rows_result = await db.execute(
        base_query.order_by(Analysis.created_at.desc()).limit(limit).offset(offset)
    )
    items = rows_result.scalars().all()

    return RecordListResponse(total=total, items=items)


@router.get("/{record_id}", response_model=RecordDetail)
async def get_record(
    record_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Analysis).where(
            Analysis.id == record_id,
            Analysis.user_id == user_id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="기록을 찾을 수 없습니다.")

    conditions = [ConditionItem(**c) for c in (record.conditions or [])]

    return RecordDetail(
        id=record.id,
        analysis_type=record.analysis_type,
        risk_level=record.risk_level,
        conditions=conditions,
        confidence=record.confidence,
        skin_metrics=record.skin_metrics,
        gemini_explanation=record.gemini_explanation,
        recommend_visit=record.recommend_visit,
        is_diagnostic=False,
        disclaimer=DISCLAIMER,
        created_at=record.created_at,
    )
