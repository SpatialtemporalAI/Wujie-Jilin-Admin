"""add task runtime fields (last_run_at, next_run_at, finish_at, error_message)

Revision ID: 0023_task_runtime_fields
Revises: 0022_wake_word_enabled
Create Date: 2026-06-23

为 task 表新增 4 个运行态字段：
- last_run_at:    最近一次开始执行时间
- next_run_at:    下一次计划执行时间
- finish_at:      最近一次结束时间
- error_message:  最近一次失败或取消原因
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0023_task_runtime_fields"
down_revision: Union[str, Sequence[str], None] = "0022_wake_word_enabled"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "task",
        sa.Column(
            "last_run_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="最近一次开始执行时间",
        ),
    )
    op.add_column(
        "task",
        sa.Column(
            "next_run_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="下一次计划执行时间",
        ),
    )
    op.add_column(
        "task",
        sa.Column(
            "finish_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="最近一次结束时间",
        ),
    )
    op.add_column(
        "task",
        sa.Column(
            "error_message",
            sa.Text(),
            nullable=True,
            comment="最近一次失败或取消原因",
        ),
    )


def downgrade() -> None:
    op.drop_column("task", "error_message")
    op.drop_column("task", "finish_at")
    op.drop_column("task", "next_run_at")
    op.drop_column("task", "last_run_at")
