"""seed online user menu

Revision ID: e1f2a3b4c5d6
Revises: c3d4e5f6a7b8
Create Date: 2026-05-23 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e1f2a3b4c5d6'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None

_ONLINE_USER_MENU_ID = None


def upgrade() -> None:
    import sys
    import os
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    from core.utils.snowflake import snowflake
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)

    # Find the 'log' catalog menu id
    conn = op.get_bind()
    result = conn.execute(
        sa.text("SELECT id FROM sys_menu WHERE name = 'log' AND type = 'CATALOG' LIMIT 1")
    ).fetchone()
    if result is None:
        return

    log_menu_id = result[0]
    online_user_menu_id = snowflake.generate()

    global _ONLINE_USER_MENU_ID
    _ONLINE_USER_MENU_ID = online_user_menu_id

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
        sa.column('is_system', sa.Boolean),
        sa.column('created_at', sa.DateTime),
    )

    op.bulk_insert(sys_menu, [
        {
            'id': online_user_menu_id,
            'parent_id': log_menu_id,
            'name': 'log_online-user',
            'path': '/log/online-user',
            'component': 'view.log_online-user',
            'redirect': None,
            'permission': 'sys:online-user:list',
            'meta_title': 'log_online-user',
            'meta_icon': None,
            'meta_hidden': False,
            'meta_affix': False,
            'meta_breadcrumb': True,
            'status': True,
            'type': 'MENU',
            'sort': 3,
            'is_system': True,
            'created_at': now,
        },
    ])


def downgrade() -> None:
    op.execute(
        sa.text("DELETE FROM sys_menu WHERE name = 'log_online-user'")
    )
