"""seed admin and log module menus

Revision ID: b1e2f3a4c5d6
Revises: a4ca5a267393
Create Date: 2026-05-23 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b1e2f3a4c5d6'
down_revision = 'a4ca5a267393'
branch_labels = None
depends_on = None

# Store generated IDs for downgrade
_MENU_IDS = {}


def upgrade() -> None:
    import sys
    import os
    # Add project root to path for importing snowflake utility
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    from database.utils.snowflake import snowflake
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    home_id = snowflake.generate()
    manage_id = snowflake.generate()
    log_id = snowflake.generate()
    manage_config_id = snowflake.generate()
    manage_dict_id = snowflake.generate()
    manage_menu_id = snowflake.generate()
    manage_role_id = snowflake.generate()
    manage_user_id = snowflake.generate()
    log_login_log_id = snowflake.generate()
    log_operation_log_id = snowflake.generate()

    # Store IDs for downgrade
    _MENU_IDS.update({
        'home': home_id,
        'manage': manage_id,
        'log': log_id,
        'manage_config': manage_config_id,
        'manage_dict': manage_dict_id,
        'manage_menu': manage_menu_id,
        'manage_role': manage_role_id,
        'manage_user': manage_user_id,
        'log_login_log': log_login_log_id,
        'log_operation_log': log_operation_log_id,
    })

    # Top-level menus
    top_menus = [
        {
            'id': home_id,
            'parent_id': None,
            'name': 'home',
            'path': '/home',
            'component': 'layout.base$view.home',
            'redirect': None,
            'permission': None,
            'meta_title': 'home',
            'meta_icon': 'mdi:monitor-dashboard',
            'meta_hidden': False,
            'meta_affix': False,
            'meta_breadcrumb': True,
            'status': True,
            'type': 'MENU',
            'sort': 1,
            'created_at': now,
        },
        {
            'id': manage_id,
            'parent_id': None,
            'name': 'manage',
            'path': '/manage',
            'component': 'layout.base',
            'redirect': None,
            'permission': None,
            'meta_title': 'manage',
            'meta_icon': 'mdi:cog',
            'meta_hidden': False,
            'meta_affix': False,
            'meta_breadcrumb': True,
            'status': True,
            'type': 'CATALOG',
            'sort': 2,
            'created_at': now,
        },
        {
            'id': log_id,
            'parent_id': None,
            'name': 'log',
            'path': '/log',
            'component': 'layout.base',
            'redirect': None,
            'permission': None,
            'meta_title': 'log',
            'meta_icon': 'mdi:file-document-outline',
            'meta_hidden': False,
            'meta_affix': False,
            'meta_breadcrumb': True,
            'status': True,
            'type': 'CATALOG',
            'sort': 3,
            'created_at': now,
        },
    ]

    # Child menus
    child_menus = [
        {
            'id': manage_config_id,
            'parent_id': manage_id,
            'name': 'manage_config',
            'path': '/manage/config',
            'component': 'view.manage_config',
            'redirect': None,
            'permission': 'sys:config:list',
            'meta_title': 'manage_config',
            'meta_icon': None,
            'meta_hidden': False,
            'meta_affix': False,
            'meta_breadcrumb': True,
            'status': True,
            'type': 'MENU',
            'sort': 1,
            'created_at': now,
        },
        {
            'id': manage_dict_id,
            'parent_id': manage_id,
            'name': 'manage_dict',
            'path': '/manage/dict',
            'component': 'view.manage_dict',
            'redirect': None,
            'permission': 'sys:dict:list',
            'meta_title': 'manage_dict',
            'meta_icon': None,
            'meta_hidden': False,
            'meta_affix': False,
            'meta_breadcrumb': True,
            'status': True,
            'type': 'MENU',
            'sort': 2,
            'created_at': now,
        },
        {
            'id': manage_menu_id,
            'parent_id': manage_id,
            'name': 'manage_menu',
            'path': '/manage/menu',
            'component': 'view.manage_menu',
            'redirect': None,
            'permission': 'sys:menu:list',
            'meta_title': 'manage_menu',
            'meta_icon': None,
            'meta_hidden': False,
            'meta_affix': False,
            'meta_breadcrumb': True,
            'status': True,
            'type': 'MENU',
            'sort': 3,
            'created_at': now,
        },
        {
            'id': manage_role_id,
            'parent_id': manage_id,
            'name': 'manage_role',
            'path': '/manage/role',
            'component': 'view.manage_role',
            'redirect': None,
            'permission': 'sys:role:list',
            'meta_title': 'manage_role',
            'meta_icon': None,
            'meta_hidden': False,
            'meta_affix': False,
            'meta_breadcrumb': True,
            'status': True,
            'type': 'MENU',
            'sort': 4,
            'created_at': now,
        },
        {
            'id': manage_user_id,
            'parent_id': manage_id,
            'name': 'manage_user',
            'path': '/manage/user',
            'component': 'view.manage_user',
            'redirect': None,
            'permission': 'sys:user:list',
            'meta_title': 'manage_user',
            'meta_icon': None,
            'meta_hidden': False,
            'meta_affix': False,
            'meta_breadcrumb': True,
            'status': True,
            'type': 'MENU',
            'sort': 5,
            'created_at': now,
        },
        {
            'id': log_login_log_id,
            'parent_id': log_id,
            'name': 'log_login-log',
            'path': '/log/login-log',
            'component': 'view.log_login-log',
            'redirect': None,
            'permission': 'sys:login-log:list',
            'meta_title': 'log_login-log',
            'meta_icon': None,
            'meta_hidden': False,
            'meta_affix': False,
            'meta_breadcrumb': True,
            'status': True,
            'type': 'MENU',
            'sort': 1,
            'created_at': now,
        },
        {
            'id': log_operation_log_id,
            'parent_id': log_id,
            'name': 'log_operation-log',
            'path': '/log/operation-log',
            'component': 'view.log_operation-log',
            'redirect': None,
            'permission': 'sys:operation-log:list',
            'meta_title': 'log_operation-log',
            'meta_icon': None,
            'meta_hidden': False,
            'meta_affix': False,
            'meta_breadcrumb': True,
            'status': True,
            'type': 'MENU',
            'sort': 2,
            'created_at': now,
        },
    ]

    sys_menu = sa.table(
        'sys_menu',
        sa.column('id', sa.BigInteger),
        sa.column('parent_id', sa.BigInteger),
        sa.column('name', sa.String),
        sa.column('path', sa.String),
        sa.column('component', sa.String),
        sa.column('redirect', sa.String),
        sa.column('permission', sa.String),
        sa.column('meta_title', sa.String),
        sa.column('meta_icon', sa.String),
        sa.column('meta_hidden', sa.Boolean),
        sa.column('meta_affix', sa.Boolean),
        sa.column('meta_breadcrumb', sa.Boolean),
        sa.column('status', sa.Boolean),
        sa.column('type', sa.String),
        sa.column('sort', sa.Integer),
        sa.column('created_at', sa.DateTime),
    )

    op.bulk_insert(sys_menu, top_menus)
    op.bulk_insert(sys_menu, child_menus)


def downgrade() -> None:
    # Delete all seeded menus (child first due to FK constraint)
    all_ids = list(_MENU_IDS.values())
    if all_ids:
        op.execute(
            sa.text("DELETE FROM sys_menu WHERE id = ANY(:ids)").bindparams(
                ids=list(all_ids)
            )
        )
