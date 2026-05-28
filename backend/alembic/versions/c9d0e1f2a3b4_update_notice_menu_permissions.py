"""update notice menu permissions to sys:notice:*

Revision ID: c9d0e1f2a3b4
Revises: 8de335c0f786
Create Date: 2026-05-28 11:35:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c9d0e1f2a3b4'
down_revision = '8de335c0f786'
branch_labels = None
depends_on = None


_PERMISSION_MAP = {
    'sys:announcement:list': 'sys:notice:list',
    'sys:announcement:add': 'sys:notice:add',
    'sys:announcement:edit': 'sys:notice:edit',
    'sys:announcement:delete': 'sys:notice:delete',
    'sys:announcement:publish': 'sys:notice:publish',
}


def upgrade() -> None:
    conn = op.get_bind()

    # Update existing announcement permissions to notice permissions
    for old_perm, new_perm in _PERMISSION_MAP.items():
        conn.execute(
            sa.text(
                "UPDATE sys_menu SET permission = :new_perm WHERE permission = :old_perm"
            ).bindparams(new_perm=new_perm, old_perm=old_perm)
        )

    # If no manage_announcement menu exists at all, create one
    existing_menu = conn.execute(
        sa.text(
            "SELECT id FROM sys_menu WHERE name = 'manage_announcement' AND type = 'MENU' LIMIT 1"
        )
    ).fetchone()

    if existing_menu is None:
        import sys
        import os
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)
        from core.utils.snowflake import snowflake
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)

        manage_result = conn.execute(
            sa.text("SELECT id FROM sys_menu WHERE name = 'manage' AND type = 'CATALOG' LIMIT 1")
        ).fetchone()
        if manage_result is not None:
            manage_id = manage_result[0]
            max_sort = conn.execute(
                sa.text("SELECT COALESCE(MAX(sort), 0) FROM sys_menu WHERE parent_id = :pid")
                .bindparams(pid=manage_id)
            ).scalar()
            next_sort = max_sort + 1

            menu_id = snowflake.generate()
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
                    'id': menu_id,
                    'parent_id': manage_id,
                    'name': 'manage_announcement',
                    'path': '/manage/announcement',
                    'component': 'view.manage_announcement',
                    'redirect': None,
                    'permission': 'sys:notice:list',
                    'meta_title': 'manage_announcement',
                    'meta_icon': None,
                    'meta_hidden': False,
                    'meta_affix': False,
                    'meta_breadcrumb': True,
                    'status': True,
                    'type': 'MENU',
                    'sort': next_sort,
                    'is_system': True,
                    'created_at': now,
                },
            ])

            # Insert buttons
            buttons = [
                ('查询', 'sys:notice:list', 1),
                ('新增', 'sys:notice:add', 2),
                ('编辑', 'sys:notice:edit', 3),
                ('删除', 'sys:notice:delete', 4),
                ('发布', 'sys:notice:publish', 5),
            ]
            button_rows = []
            button_ids = []
            for label, perm_code, sort in buttons:
                btn_id = snowflake.generate()
                button_ids.append(btn_id)
                button_rows.append({
                    'id': btn_id,
                    'parent_id': menu_id,
                    'name': f"manage_announcement_{perm_code.split(':')[-1]}",
                    'path': None,
                    'component': None,
                    'redirect': None,
                    'permission': perm_code,
                    'meta_title': label,
                    'meta_icon': None,
                    'meta_hidden': True,
                    'meta_affix': False,
                    'meta_breadcrumb': False,
                    'status': True,
                    'type': 'BUTTON',
                    'sort': sort,
                    'is_system': True,
                    'created_at': now,
                })

            if button_rows:
                op.bulk_insert(sys_menu, button_rows)

            # Bind buttons to all existing roles
            role_rows = conn.execute(sa.text("SELECT id FROM sys_role")).fetchall()
            if role_rows and button_ids:
                assoc_rows = [
                    {'role_id': r[0], 'menu_id': mid, 'permission': 'read'}
                    for r in role_rows
                    for mid in button_ids
                ]
                sys_role_menu = sa.table(
                    'sys_role_menu',
                    sa.column('role_id', sa.BigInteger),
                    sa.column('menu_id', sa.BigInteger),
                    sa.column('permission', sa.String),
                )
                op.bulk_insert(sys_role_menu, assoc_rows)


def downgrade() -> None:
    conn = op.get_bind()
    # Reverse the permission mapping
    for new_perm, old_perm in {v: k for k, v in _PERMISSION_MAP.items()}.items():
        conn.execute(
            sa.text(
                "UPDATE sys_menu SET permission = :old_perm WHERE permission = :new_perm"
            ).bindparams(old_perm=old_perm, new_perm=new_perm)
        )
