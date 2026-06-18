"""set scene_map resolution default to 1

Revision ID: 0019_scene_map_resolution_default
Revises: 0018_scene_map_nav_image
Create Date: 2026-06-17
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0019_scene_map_resolution_default"
down_revision: Union[str, Sequence[str], None] = "0018_scene_map_nav_image"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "scene_map",
        "resolution",
        existing_type=sa.Float(),
        server_default="1",
        existing_nullable=False,
        existing_comment="分辨率(米/像素)，如0.2表示1像素=20厘米",
        comment="映射比例",
    )


def downgrade() -> None:
    op.alter_column(
        "scene_map",
        "resolution",
        existing_type=sa.Float(),
        server_default="0.2",
        existing_nullable=False,
        existing_comment="映射比例",
        comment="分辨率(米/像素)，如0.2表示1像素=20厘米",
    )
