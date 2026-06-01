"""drop tenant_id from sys_dict, sys_dict_item, sys_config

Revision ID: d4e5f6a7b8c9
Revises: c8befd8ddc3e
Create Date: 2026-06-01 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'c8befd8ddc3e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """字典表和系统配置表不需要租户隔离，移除 tenant_id 列。"""
    op.drop_column('sys_dict_item', 'tenant_id')
    op.drop_column('sys_dict', 'tenant_id')
    op.drop_column('sys_config', 'tenant_id')


def downgrade() -> None:
    """重新添加 tenant_id 列。"""
    op.add_column('sys_config', sa.Column('tenant_id', sa.BigInteger(), nullable=True, comment='租户ID'))
    op.add_column('sys_dict', sa.Column('tenant_id', sa.BigInteger(), nullable=True, comment='租户ID'))
    op.add_column('sys_dict_item', sa.Column('tenant_id', sa.BigInteger(), nullable=True, comment='租户ID'))
