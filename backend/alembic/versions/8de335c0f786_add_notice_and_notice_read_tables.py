"""add notice and notice_read tables

Revision ID: 8de335c0f786
Revises: f2a3b4c5d6e7
Create Date: 2026-05-27 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '8de335c0f786'
down_revision = 'b3c4d5e6f7a8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # 创建 sys_notice 表
    existing_notice = conn.execute(sa.text("SELECT to_regclass('public.sys_notice')")).scalar()
    if existing_notice is None:
        op.create_table(
            'sys_notice',
            sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='主键 ID'),
            sa.Column('title', sa.String(length=200), nullable=False, comment='通知标题'),
            sa.Column('content', sa.Text(), nullable=False, comment='通知内容（支持HTML）'),
            sa.Column('type', sa.String(length=50), nullable=False, comment='通知类型：announcement-公告, system-系统, operation-操作提醒, approval-审批通知'),
            sa.Column('target_type', sa.String(length=50), nullable=False, comment='推送范围：all-全员, role-按角色, user-按指定用户'),
            sa.Column('target_role_ids', postgresql.ARRAY(sa.BigInteger()), nullable=True, comment='目标角色ID列表（target_type=role时有效）'),
            sa.Column('target_user_ids', postgresql.ARRAY(sa.BigInteger()), nullable=True, comment='目标用户ID列表（target_type=user时有效）'),
            sa.Column('sender_id', sa.BigInteger(), nullable=False, comment='发送者用户ID'),
            sa.Column('sender_name', sa.String(length=100), nullable=False, comment='发送者名称'),
            sa.Column('priority', sa.String(length=20), nullable=False, comment='优先级：low-低, normal-普通, high-高, urgent-紧急'),
            sa.Column('status', sa.Boolean(), nullable=False, comment='状态：True-已发布, False-草稿'),
            sa.Column('published_at', sa.DateTime(timezone=True), nullable=True, comment='发布时间'),
            sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='删除时间，为空则未删除'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, comment='创建时间'),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, comment='更新时间'),
            sa.PrimaryKeyConstraint('id'),
            comment='系统通知表',
        )
        op.create_index(op.f('ix_sys_notice_id'), 'sys_notice', ['id'], unique=True)
        op.create_index(op.f('ix_sys_notice_status'), 'sys_notice', ['status'], unique=False)
        op.create_index(op.f('ix_sys_notice_type'), 'sys_notice', ['type'], unique=False)
        op.create_index(op.f('ix_sys_notice_sender_id'), 'sys_notice', ['sender_id'], unique=False)

    # 创建 sys_notice_read 表
    existing_read = conn.execute(sa.text("SELECT to_regclass('public.sys_notice_read')")).scalar()
    if existing_read is None:
        op.create_table(
            'sys_notice_read',
            sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='主键 ID'),
            sa.Column('user_id', sa.BigInteger(), nullable=False, comment='用户ID'),
            sa.Column('notice_id', sa.BigInteger(), nullable=False, comment='通知ID'),
            sa.Column('is_read', sa.Boolean(), nullable=False, comment='是否已读'),
            sa.Column('read_at', sa.DateTime(timezone=True), nullable=True, comment='阅读时间'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, comment='创建时间'),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, comment='更新时间'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('user_id', 'notice_id', name='uix_user_notice'),
            comment='用户通知阅读记录表',
        )
        op.create_index(op.f('ix_sys_notice_read_id'), 'sys_notice_read', ['id'], unique=True)
        op.create_index(op.f('ix_sys_notice_read_user_id'), 'sys_notice_read', ['user_id'], unique=False)
        op.create_index(op.f('ix_sys_notice_read_notice_id'), 'sys_notice_read', ['notice_id'], unique=False)
        op.create_index(op.f('ix_sys_notice_read_is_read'), 'sys_notice_read', ['is_read'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_sys_notice_read_is_read'), table_name='sys_notice_read')
    op.drop_index(op.f('ix_sys_notice_read_notice_id'), table_name='sys_notice_read')
    op.drop_index(op.f('ix_sys_notice_read_user_id'), table_name='sys_notice_read')
    op.drop_index(op.f('ix_sys_notice_read_id'), table_name='sys_notice_read')
    op.drop_table('sys_notice_read')

    op.drop_index(op.f('ix_sys_notice_sender_id'), table_name='sys_notice')
    op.drop_index(op.f('ix_sys_notice_type'), table_name='sys_notice')
    op.drop_index(op.f('ix_sys_notice_status'), table_name='sys_notice')
    op.drop_index(op.f('ix_sys_notice_id'), table_name='sys_notice')
    op.drop_table('sys_notice')
