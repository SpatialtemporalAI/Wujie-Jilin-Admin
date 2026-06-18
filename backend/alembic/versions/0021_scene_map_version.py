"""add scene_map.version and scene_map.target_version

Revision ID: 0021_scene_map_version
Revises: 0020_task_map_id
Create Date: 2026-06-18

为 scene_map 表新增 version / target_version 字段，用于地图版本管理与导览服务同步状态记录。
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0021_scene_map_version"
down_revision: Union[str, Sequence[str], None] = "0020_task_map_id"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "scene_map",
        sa.Column(
            "version",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="地图内容版本号，编辑器保存 +1",
        ),
    )
    op.add_column(
        "scene_map",
        sa.Column(
            "target_version",
            sa.Integer(),
            nullable=True,
            comment="导览服务已同步版本号（定时任务回填）",
        ),
    )


def downgrade() -> None:
    op.drop_column("scene_map", "target_version")
    op.drop_column("scene_map", "version")
