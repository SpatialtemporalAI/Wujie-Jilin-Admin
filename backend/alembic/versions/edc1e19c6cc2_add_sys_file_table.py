"""add_sys_file_table

Revision ID: edc1e19c6cc2
Revises: b6c7d8e9f0a1
Create Date: 2026-05-28 23:04:00.916329

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'edc1e19c6cc2'
down_revision: Union[str, Sequence[str], None] = 'b6c7d8e9f0a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('sys_file',
    sa.Column('id', sa.BigInteger(), nullable=False, comment='雪花算法主键 ID'),
    sa.Column('original_name', sa.String(length=500), nullable=False, comment='原始文件名'),
    sa.Column('stored_name', sa.String(length=500), nullable=False, comment='存储文件名'),
    sa.Column('file_path', sa.String(length=1000), nullable=False, comment='存储路径'),
    sa.Column('file_size', sa.BigInteger(), nullable=False, comment='文件大小(字节)'),
    sa.Column('mime_type', sa.String(length=200), nullable=False, comment='MIME类型'),
    sa.Column('extension', sa.String(length=20), nullable=False, comment='扩展名'),
    sa.Column('created_by', sa.BigInteger(), nullable=False, comment='上传者用户ID'),
    sa.Column('storage_platform', sa.String(length=50), nullable=False, comment='存储平台标识'),
    sa.Column('hash', sa.String(length=64), nullable=True, comment='SHA-256哈希'),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='删除时间，为空则未删除'),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, comment='创建时间'),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, comment='更新时间'),
    sa.PrimaryKeyConstraint('id'),
    comment='\n    系统文件存储表\n    '
    )
    op.create_index(op.f('ix_sys_file_id'), 'sys_file', ['id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_sys_file_id'), table_name='sys_file')
    op.drop_table('sys_file')
