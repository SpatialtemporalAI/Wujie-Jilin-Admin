"""seed button-type menus for permission control

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2026-05-24 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f2a3b4c5d6e7'
down_revision = 'e1f2a3b4c5d6'
branch_labels = None
depends_on = None


# Mapping: parent menu name -> list of (button_label_zh, permission_code, sort)
BUTTON_MENUS = {
    'manage_menu': [
        ('查询', 'sys:menu:list', 1),
        ('新增', 'sys:menu:add', 2),
        ('编辑', 'sys:menu:edit', 3),
        ('删除', 'sys:menu:delete', 4),
    ],
    'manage_role': [
        ('查询', 'sys:role:list', 1),
        ('新增', 'sys:role:add', 2),
        ('编辑', 'sys:role:edit', 3),
        ('删除', 'sys:role:delete', 4),
    ],
    'manage_user': [
        ('查询', 'sys:user:list', 1),
        ('新增', 'sys:user:add', 2),
        ('编辑', 'sys:user:edit', 3),
        ('删除', 'sys:user:delete', 4),
    ],
    'manage_dict': [
        ('查询', 'sys:dict:list', 1),
        ('新增', 'sys:dict:add', 2),
        ('编辑', 'sys:dict:edit', 3),
        ('删除', 'sys:dict:delete', 4),
    ],
    'manage_config': [
        ('查询', 'sys:config:list', 1),
        ('新增', 'sys:config:add', 2),
        ('编辑', 'sys:config:edit', 3),
        ('删除', 'sys:config:delete', 4),
    ],
    'log_login-log': [
        ('查询', 'sys:log:list', 1),
        ('删除', 'sys:log:delete', 2),
    ],
    'log_operation-log': [
        ('查询', 'sys:oplog:list', 1),
        ('删除', 'sys:oplog:delete', 2),
    ],
    'log_online-user': [
        ('查询', 'sys:online:list', 1),
        ('踢出', 'sys:online:kick', 2),
    ],
}

# All permission codes for downgrade
_ALL_PERMISSIONS = [
    perm for buttons in BUTTON_MENUS.values() for _, perm, _ in buttons
]


def upgrade() -> None:
    import sys
    import os
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    from core.utils.snowflake import snowflake
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    conn = op.get_bind()

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

    new_button_menus = []
    button_menu_ids = []

    for parent_name, buttons in BUTTON_MENUS.items():
        result = conn.execute(
            sa.text("SELECT id FROM sys_menu WHERE name = :name AND type = 'MENU' LIMIT 1")
            .bindparams(name=parent_name)
        ).fetchone()
        if result is None:
            # Parent menu missing — skip (e.g., in partial DB state)
            continue
        parent_id = result[0]

        for label, perm_code, sort in buttons:
            # Skip if a button menu with this permission already exists under this parent
            existing = conn.execute(
                sa.text(
                    "SELECT id FROM sys_menu "
                    "WHERE parent_id = :pid AND permission = :perm AND type = 'BUTTON' LIMIT 1"
                ).bindparams(pid=parent_id, perm=perm_code)
            ).fetchone()
            if existing is not None:
                continue

            btn_id = snowflake.generate()
            button_menu_ids.append(btn_id)
            new_button_menus.append({
                'id': btn_id,
                'parent_id': parent_id,
                'name': f'{parent_name}_{perm_code.split(":")[-1]}',
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

    if new_button_menus:
        op.bulk_insert(sys_menu, new_button_menus)

    # Associate all button menus with every existing role (so existing roles inherit
    # the new permission points). New roles created later manage their own perms.
    if button_menu_ids:
        role_rows = conn.execute(sa.text("SELECT id FROM sys_role")).fetchall()
        if role_rows:
            assoc_rows = [
                {'role_id': r[0], 'menu_id': mid, 'permission': 'read'}
                for r in role_rows
                for mid in button_menu_ids
            ]
            sys_role_menu = sa.table(
                'sys_role_menu',
                sa.column('role_id', sa.BigInteger),
                sa.column('menu_id', sa.BigInteger),
                sa.column('permission', sa.String),
            )
            op.bulk_insert(sys_role_menu, assoc_rows)


def downgrade() -> None:
    if _ALL_PERMISSIONS:
        op.execute(
            sa.text(
                "DELETE FROM sys_menu WHERE type = 'BUTTON' AND permission = ANY(:perms)"
            ).bindparams(perms=list(_ALL_PERMISSIONS))
        )
