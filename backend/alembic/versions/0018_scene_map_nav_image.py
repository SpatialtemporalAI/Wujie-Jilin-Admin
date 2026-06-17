"""add scene_map.nav_image_id for navigation map image

Revision ID: 0018_scene_map_nav_image
Revises: 0017_scene_map_object_angle
Create Date: 2026-06-17

为 scene_map 表新增 nav_image_id 列，用于保存导航地图图片（绘制了障碍物/禁行区域的原图副本）。
迁移时将历史数据 nav_image_id 回填为 image_id。
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0018_scene_map_nav_image"
down_revision: Union[str, Sequence[str], None] = "0017_scene_map_object_angle"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "scene_map",
        sa.Column(
            "nav_image_id",
            sa.BigInteger(),
            nullable=True,
            comment="导航地图图片文件ID",
        ),
    )
    op.create_foreign_key(
        "fk_scene_map_nav_image_id_sys_file",
        "scene_map",
        "sys_file",
        ["nav_image_id"],
        ["id"],
    )
    op.execute(
        "UPDATE scene_map SET nav_image_id = image_id WHERE image_id IS NOT NULL"
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_scene_map_nav_image_id_sys_file", "scene_map", type_="foreignkey"
    )
    op.drop_column("scene_map", "nav_image_id")
