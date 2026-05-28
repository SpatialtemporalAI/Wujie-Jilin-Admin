"""add i18n_key column to sys_menu

Revision ID: a5b6c7d8e9f0
Revises: d0e1f2a3b4c5
Create Date: 2026-05-28 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a5b6c7d8e9f0'
down_revision = 'd0e1f2a3b4c5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('sys_menu', sa.Column(
        'i18n_key', sa.String(100), nullable=True,
        comment='国际化键，如 route.home'
    ))


def downgrade() -> None:
    op.drop_column('sys_menu', 'i18n_key')
