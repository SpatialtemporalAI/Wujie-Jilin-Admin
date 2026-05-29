"""add meta_keep_alive column to sys_menu

Revision ID: g5b6c7d8e9f0
Revises: f4a5b6c7d8e9
Create Date: 2026-05-29 23:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'g5b6c7d8e9f0'
down_revision = 'f4a5b6c7d8e9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('sys_menu', sa.Column('meta_keep_alive', sa.Boolean(), nullable=True, comment='是否缓存路由'))
    op.execute("UPDATE sys_menu SET meta_keep_alive = FALSE")
    op.alter_column('sys_menu', 'meta_keep_alive', nullable=False)


def downgrade() -> None:
    op.drop_column('sys_menu', 'meta_keep_alive')
