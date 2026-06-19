"""add task.map_id referencing scene_map.id

Revision ID: 0020_task_map_id
Revises: 0019_scene_map_resolution
Create Date: 2026-06-17

为 task 表新增 map_id 列，固话任务关联的场景地图，避免机器人改绑场景后影响任务的场景配置。
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0020_task_map_id"
down_revision: Union[str, Sequence[str], None] = "0019_scene_map_resolution"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "task",
        sa.Column("map_id", sa.BigInteger(), nullable=True, comment="关联场景地图ID"),
    )
    op.create_foreign_key(
        "fk_task_map_id_scene_map",
        "task",
        "scene_map",
        ["map_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_task_map_id_scene_map",
        "task",
        type_="foreignkey",
    )
    op.drop_column("task", "map_id")
