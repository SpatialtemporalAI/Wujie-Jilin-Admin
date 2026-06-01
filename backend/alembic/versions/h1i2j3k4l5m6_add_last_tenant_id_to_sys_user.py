"""add last_tenant_id to sys_user

Revision ID: h1i2j3k4l5m6
Revises: 76e0fc2dcf1a
Create Date: 2026-06-01 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'h1i2j3k4l5m6'
down_revision: Union[str, Sequence[str], None] = 'b713ee0de03e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'sys_user',
        sa.Column('last_tenant_id', sa.BigInteger(), nullable=True, comment='最后选择的租户ID'),
    )


def downgrade() -> None:
    op.drop_column('sys_user', 'last_tenant_id')
