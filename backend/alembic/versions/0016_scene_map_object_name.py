"""add scene_map_object.name for obstacle/forbidden-zone renaming

Revision ID: 0016_scene_map_object_name
Revises: 0015_task_point_annotation_id
Create Date: 2026-06-16

为 scene_map_object 表新增 name 列，支持障碍物/禁行区域的命名与重命名。
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0016_scene_map_object_name"
down_revision: Union[str, Sequence[str], None] = "0015_task_point_annotation_id"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "scene_map_object",
        sa.Column("name", sa.String(length=100), nullable=True, comment="物体名称"),
    )


def downgrade() -> None:
    op.drop_column("scene_map_object", "name")
