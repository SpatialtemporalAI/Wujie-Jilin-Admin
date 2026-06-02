"""remove role code column

Revision ID: i2j3k4l5m6n7
Revises: f15c128af6cb
Create Date: 2026-06-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'i2j3k4l5m6n7'
down_revision: Union[str, Sequence[str], None] = 'f15c128af6cb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index('ix_sys_role_code', table_name='sys_role')
    op.drop_column('sys_role', 'code')


def downgrade() -> None:
    op.add_column('sys_role', sa.Column('code', sa.String(100), nullable=False))
    op.create_index('ix_sys_role_code', 'sys_role', ['code'], unique=True)
