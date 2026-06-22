"""add robot_voice_config.wake_word_enabled

Revision ID: 0022_wake_word_enabled
Revises: 0021_scene_map_version
Create Date: 2026-06-22

为 robot_voice_config 表新增 wake_word_enabled 字段，用于控制唤醒词开关。
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0022_wake_word_enabled"
down_revision: Union[str, Sequence[str], None] = "0021_scene_map_version"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "robot_voice_config",
        sa.Column(
            "wake_word_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
            comment="是否启用唤醒词：True-启用，False-禁用",
        ),
    )


def downgrade() -> None:
    op.drop_column("robot_voice_config", "wake_word_enabled")
