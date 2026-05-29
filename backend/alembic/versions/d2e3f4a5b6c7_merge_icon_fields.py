"""merge icon column into meta_icon and drop icon

Revision ID: d2e3f4a5b6c7
Revises: c1d2e3f4a5b6
Create Date: 2026-05-29 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'd2e3f4a5b6c7'
down_revision = 'c1d2e3f4a5b6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 回填：将 icon 有值但 meta_icon 为空的行迁移数据
    op.execute(
        "UPDATE sys_menu SET meta_icon = icon WHERE meta_icon IS NULL AND icon IS NOT NULL"
    )
    op.drop_column('sys_menu', 'icon')


def downgrade() -> None:
    op.add_column('sys_menu', sa.Column('icon', sa.String(50), nullable=True))
    op.execute(
        "UPDATE sys_menu SET icon = meta_icon WHERE icon IS NULL AND meta_icon IS NOT NULL"
    )
