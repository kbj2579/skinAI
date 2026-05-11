"""init

Revision ID: 001
Revises:
Create Date: 2026-04-11
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("nickname", sa.String(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("(datetime('now'))")),
    )

    op.create_table(
        "analyses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("analysis_type", sa.String(), nullable=False),
        sa.Column("image_s3_key", sa.String(), nullable=True),
        sa.Column("raw_result", sa.JSON(), nullable=True),
        sa.Column("risk_level", sa.String(), nullable=False),
        sa.Column("conditions", sa.JSON(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("gemini_explanation", sa.Text(), nullable=True),
        sa.Column("recommend_visit", sa.Boolean(), server_default=sa.text("0")),
        sa.Column("is_diagnostic", sa.Boolean(), server_default=sa.text("0")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("(datetime('now'))")),
    )
    op.create_index("idx_analyses_user_date", "analyses", ["user_id", "created_at"])

    op.create_table(
        "lesion_tracks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("track_name", sa.String(), nullable=True),
    )

    op.create_table(
        "lesion_analyses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("track_id", sa.Integer(), sa.ForeignKey("lesion_tracks.id"), nullable=False),
        sa.Column("image_s3_key", sa.String(), nullable=True),
        sa.Column("risk_level", sa.String(), nullable=True),
        sa.Column("asymmetry_score", sa.Float(), nullable=True),
        sa.Column("border_score", sa.Float(), nullable=True),
        sa.Column("color_variance", sa.Float(), nullable=True),
        sa.Column("size_mm", sa.Float(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("(datetime('now'))")),
    )
    op.create_index("idx_lesion_analyses_track", "lesion_analyses", ["track_id", "created_at"])


def downgrade() -> None:
    op.drop_table("lesion_analyses")
    op.drop_table("lesion_tracks")
    op.drop_table("analyses")
    op.drop_table("users")
