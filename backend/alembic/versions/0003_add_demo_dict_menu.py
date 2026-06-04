"""add demo_dict menu

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-04

"""
from typing import Sequence, Union
from datetime import datetime

from alembic import op
import sqlalchemy as sa


revision: str = '0003'
down_revision: Union[str, Sequence[str], None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEMO_DICT_MENU_ID = 2907499345027081
DEMO_CATALOG_ID = 2907499345027072
ADMIN_ROLE_ID = 2902792101634048


def upgrade() -> None:
    op.bulk_insert(
        sa.table(
            'sys_menu',
            sa.column('id', sa.BigInteger),
            sa.column('parent_id', sa.BigInteger),
            sa.column('name', sa.String),
            sa.column('path', sa.String),
            sa.column('component', sa.String),
            sa.column('redirect', sa.String),
            sa.column('permission', sa.String),
            sa.column('meta_icon', sa.String),
            sa.column('meta_hidden', sa.Boolean),
            sa.column('meta_affix', sa.Boolean),
            sa.column('meta_breadcrumb', sa.Boolean),
            sa.column('status', sa.Boolean),
            sa.column('type', sa.String),
            sa.column('sort', sa.Integer),
            sa.column('is_system', sa.Boolean),
            sa.column('meta_href', sa.String),
            sa.column('meta_keep_alive', sa.Boolean),
            sa.column('deleted_at', sa.DateTime),
            sa.column('created_at', sa.DateTime),
            sa.column('updated_at', sa.DateTime),
        ),
        [{
            'id': DEMO_DICT_MENU_ID,
            'parent_id': DEMO_CATALOG_ID,
            'name': 'demo_dict',
            'path': '/demo/dict',
            'component': 'view.demo_dict',
            'redirect': None,
            'permission': None,
            'meta_icon': 'mdi:book-alphabet',
            'meta_hidden': False,
            'meta_affix': False,
            'meta_breadcrumb': True,
            'status': True,
            'type': 'MENU',
            'sort': 4,
            'is_system': True,
            'meta_href': None,
            'meta_keep_alive': False,
            'deleted_at': None,
            'created_at': datetime(2026, 6, 4, 16, 0, 0),
            'updated_at': None,
        }],
    )

    op.bulk_insert(
        sa.table(
            'sys_role_menu',
            sa.column('role_id', sa.BigInteger),
            sa.column('menu_id', sa.BigInteger),
            sa.column('permission', sa.String),
        ),
        [{
            'role_id': ADMIN_ROLE_ID,
            'menu_id': DEMO_DICT_MENU_ID,
            'permission': 'read',
        }],
    )


def downgrade() -> None:
    op.execute(
        f"DELETE FROM sys_role_menu WHERE role_id = {ADMIN_ROLE_ID} AND menu_id = {DEMO_DICT_MENU_ID}"
    )
    op.execute(
        f"DELETE FROM sys_menu WHERE id = {DEMO_DICT_MENU_ID}"
    )
