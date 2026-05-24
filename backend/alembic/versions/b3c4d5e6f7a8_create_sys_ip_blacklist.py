"""create sys_ip_blacklist table

Revision ID: b3c4d5e6f7a8
Revises: a3b4c5d6e7f8
Create Date: 2026-05-24 19:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b3c4d5e6f7a8'
down_revision = 'a3b4c5d6e7f8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    existing = conn.execute(sa.text("SELECT to_regclass('public.sys_ip_blacklist')")).scalar()
    if existing is not None:
        return
    op.create_table(
        'sys_ip_blacklist',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='主键 ID'),
        sa.Column('ip', sa.String(length=64), nullable=False, comment='IP 地址'),
        sa.Column('type', sa.String(length=16), nullable=False, comment='类型：permanent / temporary'),
        sa.Column('reason', sa.String(length=255), nullable=True, comment='加入原因'),
        sa.Column('expire_at', sa.DateTime(timezone=True), nullable=True, comment='过期时间（temporary 必填）'),
        sa.Column('creator_id', sa.BigInteger(), nullable=True, comment='创建人ID（系统自动写入时为空）'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='删除时间，为空则未删除'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ip'),
        comment='IP 黑名单表',
    )
    op.create_index(op.f('ix_sys_ip_blacklist_id'), 'sys_ip_blacklist', ['id'], unique=True)
    op.create_index(op.f('ix_sys_ip_blacklist_ip'), 'sys_ip_blacklist', ['ip'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_sys_ip_blacklist_ip'), table_name='sys_ip_blacklist')
    op.drop_index(op.f('ix_sys_ip_blacklist_id'), table_name='sys_ip_blacklist')
    op.drop_table('sys_ip_blacklist')
