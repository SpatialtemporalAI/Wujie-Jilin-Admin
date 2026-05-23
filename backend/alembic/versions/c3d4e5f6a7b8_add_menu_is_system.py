"""add is_system column to sys_menu

Revision ID: c3d4e5f6a7b8
Revises: b1e2f3a4c5d6
Create Date: 2026-05-23 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c3d4e5f6a7b8'
down_revision = 'b1e2f3a4c5d6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('sys_menu', sa.Column('is_system', sa.Boolean(), nullable=True, comment='是否为系统内置菜单'))
    op.execute("UPDATE sys_menu SET is_system = FALSE WHERE is_system IS NULL")
    op.alter_column('sys_menu', 'is_system', nullable=False)
    op.execute("UPDATE sys_menu SET is_system = TRUE WHERE permission LIKE 'sys:%'")


def downgrade() -> None:
    op.drop_column('sys_menu', 'is_system')
