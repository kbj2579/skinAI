from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, Float, ForeignKey, Integer, String, Text,
    TIMESTAMP, JSON,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


def _now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    nickname = Column(String, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), default=_now)

    analyses = relationship("Analysis", back_populates="user", cascade="all, delete")
    lesion_tracks = relationship("LesionTrack", back_populates="user", cascade="all, delete")


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    analysis_type = Column(String, nullable=False)   # skin | scalp | lesion
    image_s3_key = Column(String, nullable=True)
    raw_result = Column(JSON, nullable=True)          # model 원본 응답
    risk_level = Column(String, nullable=False)       # normal | mild | suspicious | danger
    conditions = Column(JSON, nullable=True)
    confidence = Column(Float, nullable=True)
    gemini_explanation = Column(Text, nullable=True)
    skin_metrics = Column(JSON, nullable=True)         # 정량화 피부 지표
    recommend_visit = Column(Boolean, default=False)
    is_diagnostic = Column(Boolean, default=False)    # 항상 False
    created_at = Column(TIMESTAMP(timezone=True), default=_now)

    user = relationship("User", back_populates="analyses")


class LesionTrack(Base):
    __tablename__ = "lesion_tracks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    track_name = Column(String, nullable=True)

    user = relationship("User", back_populates="lesion_tracks")
    lesion_analyses = relationship("LesionAnalysis", back_populates="track", cascade="all, delete")


class LesionAnalysis(Base):
    __tablename__ = "lesion_analyses"

    id = Column(Integer, primary_key=True, index=True)
    track_id = Column(Integer, ForeignKey("lesion_tracks.id", ondelete="CASCADE"), nullable=False)
    image_s3_key = Column(String, nullable=True)
    risk_level = Column(String, nullable=True)
    asymmetry_score = Column(Float, nullable=True)
    border_score = Column(Float, nullable=True)
    color_variance = Column(Float, nullable=True)
    size_mm = Column(Float, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), default=_now)

    track = relationship("LesionTrack", back_populates="lesion_analyses")
