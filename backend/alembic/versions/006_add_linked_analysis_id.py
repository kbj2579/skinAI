"""add linked_analysis_id to analyses

Revision ID: 006
Revises: 005
Create Date: 2026-06-14
"""
from alembic import op
import sqlalchemy as sa

revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'analyses',
        sa.Column('linked_analysis_id', sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        'fk_analyses_linked_analysis_id',
        'analyses', 'analyses',
        ['linked_analysis_id'], ['id'],
        ondelete='SET NULL',
    )


def downgrade():
    op.drop_constraint('fk_analyses_linked_analysis_id', 'analyses', type_='foreignkey')
    op.drop_column('analyses', 'linked_analysis_id')
