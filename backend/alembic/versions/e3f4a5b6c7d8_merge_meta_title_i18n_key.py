"""merge meta_title and i18n_key into name, drop columns

Revision ID: e3f4a5b6c7d8
Revises: d2e3f4a5b6c7
Create Date: 2026-05-29 19:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e3f4a5b6c7d8'
down_revision = 'd2e3f4a5b6c7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 回填：如果 name 为空但 meta_title 有值，用 meta_title 填充 name
    op.execute(
        "UPDATE sys_menu SET name = meta_title WHERE name IS NULL AND meta_title IS NOT NULL"
    )
    op.drop_column('sys_menu', 'meta_title')
    op.drop_column('sys_menu', 'i18n_key')


def downgrade() -> None:
    op.add_column('sys_menu', sa.Column('meta_title', sa.String(100), nullable=True))
    op.add_column('sys_menu', sa.Column('i18n_key', sa.String(100), nullable=True))
    op.execute(
        "UPDATE sys_menu SET meta_title = name WHERE meta_title IS NULL"
    )
    op.execute(
        "UPDATE sys_menu SET i18n_key = 'route.' || name WHERE i18n_key IS NULL"
    )
