"""remove salt column from user tables

Revision ID: a1b2c3d4e5f6
Revises: c2519d982254
Create Date: 2026-05-18 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'c2519d982254'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('sys_user', 'salt')
    op.drop_column('app_user', 'salt')


def downgrade() -> None:
    op.add_column('sys_user', sa.Column('salt', sa.String(length=255), nullable=False, server_default='', comment='密码盐值'))
    op.add_column('app_user', sa.Column('salt', sa.String(length=255), nullable=True, comment='密码盐值'))
