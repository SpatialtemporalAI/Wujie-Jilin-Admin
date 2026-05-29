"""add meta_href column to sys_menu

Revision ID: f4a5b6c7d8e9
Revises: e3f4a5b6c7d8
Create Date: 2026-05-29 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f4a5b6c7d8e9'
down_revision = 'e3f4a5b6c7d8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('sys_menu', sa.Column('meta_href', sa.String(500), nullable=True, comment='外部链接地址'))


def downgrade() -> None:
    op.drop_column('sys_menu', 'meta_href')
