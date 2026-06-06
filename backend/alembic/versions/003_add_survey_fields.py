"""add survey fields (body_part, smoking, drinking)

Revision ID: 003
Revises: 002
Create Date: 2026-05-26
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("analyses", sa.Column("body_part", sa.String(), nullable=True))
    op.add_column("analyses", sa.Column("smoking",   sa.Boolean(), nullable=True))
    op.add_column("analyses", sa.Column("drinking",  sa.Boolean(), nullable=True))


def downgrade() -> None:
    op.drop_column("analyses", "drinking")
    op.drop_column("analyses", "smoking")
    op.drop_column("analyses", "body_part")
