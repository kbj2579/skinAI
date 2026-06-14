"""add cosmetics and skin_type

Revision ID: 005
Revises: 004
Create Date: 2026-06-14
"""
from alembic import op
import sqlalchemy as sa

revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('skin_type', sa.String(), nullable=True))
    op.create_table(
        'user_cosmetics',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_name', sa.String(), nullable=False),
        sa.Column('start_date', sa.String(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.create_index('ix_user_cosmetics_user_id', 'user_cosmetics', ['user_id'])


def downgrade():
    op.drop_index('ix_user_cosmetics_user_id', 'user_cosmetics')
    op.drop_table('user_cosmetics')
    op.drop_column('users', 'skin_type')
