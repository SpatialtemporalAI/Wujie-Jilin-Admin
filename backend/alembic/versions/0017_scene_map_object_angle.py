"""add scene_map_object.angle for object rotation

Revision ID: 0017_scene_map_object_angle
Revises: 0016_scene_map_object_name
Create Date: 2026-06-16

为 scene_map_object 表新增 angle 列，保存障碍物/禁区的旋转角度。
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0017_scene_map_object_angle"
down_revision: Union[str, Sequence[str], None] = "0016_scene_map_object_name"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "scene_map_object",
        sa.Column("angle", sa.Float(), nullable=False, server_default="0", comment="旋转角度(度)"),
    )


def downgrade() -> None:
    op.drop_column("scene_map_object", "angle")
