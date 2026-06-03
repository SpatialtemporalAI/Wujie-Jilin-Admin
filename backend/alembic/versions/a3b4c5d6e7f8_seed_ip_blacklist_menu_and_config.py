"""seed ip-blacklist menu, button perms, and rate_limit config

Revision ID: a3b4c5d6e7f8
Revises: f2a3b4c5d6e7
Create Date: 2026-05-24 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a3b4c5d6e7f8'
down_revision = 'f2a3b4c5d6e7'
branch_labels = None
depends_on = None

# Permission codes for downgrade
_BLACKLIST_PERMS = ['sys:blacklist:list', 'sys:blacklist:add', 'sys:blacklist:remove']

# Rate-limit default config rows
_RATE_LIMIT_CONFIGS = [
    {
        'key': 'rate_limit.enabled',
        'value': 'true',
        'default_value': 'true',
        'validation_rule': None,
        'description': '限流总开关',
        'type': 'BOOLEAN',
        'group': 'SECURITY',
        'is_system': True,
    },
    {
        'key': 'rate_limit.ip_per_minute',
        'value': '120',
        'default_value': '120',
        'validation_rule': None,
        'description': 'IP 全局限流（次/分钟）',
        'type': 'NUMBER',
        'group': 'SECURITY',
        'is_system': True,
    },
    {
        'key': 'rate_limit.user_per_minute',
        'value': '300',
        'default_value': '300',
        'validation_rule': None,
        'description': '用户限流（次/分钟）',
        'type': 'NUMBER',
        'group': 'SECURITY',
        'is_system': True,
    },
    {
        'key': 'rate_limit.login_fail_max',
        'value': '5',
        'default_value': '5',
        'validation_rule': None,
        'description': '登录失败上限次数',
        'type': 'NUMBER',
        'group': 'SECURITY',
        'is_system': True,
    },
    {
        'key': 'rate_limit.login_fail_window',
        'value': '600',
        'default_value': '600',
        'validation_rule': None,
        'description': '登录失败统计窗口（秒）',
        'type': 'NUMBER',
        'group': 'SECURITY',
        'is_system': True,
    },
    {
        'key': 'rate_limit.login_fail_block_ttl',
        'value': '1800',
        'default_value': '1800',
        'validation_rule': None,
        'description': '登录失败自动拉黑时长（秒）',
        'type': 'NUMBER',
        'group': 'SECURITY',
        'is_system': True,
    },
    {
        'key': 'rate_limit.blacklist_redis_ttl',
        'value': '86400',
        'default_value': '86400',
        'validation_rule': None,
        'description': '永久黑名单 Redis 兜底 TTL（秒）',
        'type': 'NUMBER',
        'group': 'SECURITY',
        'is_system': True,
    },
    {
        'key': 'rate_limit.whitelist_path_prefixes',
        'value': '["/docs","/redoc","/openapi.json","/admin/health"]',
        'default_value': '["/docs","/redoc","/openapi.json","/admin/health"]',
        'validation_rule': None,
        'description': '路径白名单前缀',
        'type': 'JSON',
        'group': 'SECURITY',
        'is_system': True,
    },
    {
        'key': 'rate_limit.whitelist_ips',
        'value': '[]',
        'default_value': '[]',
        'validation_rule': None,
        'description': 'IP 白名单',
        'type': 'JSON',
        'group': 'SECURITY',
        'is_system': True,
    },
    {
        'key': 'rate_limit.path_rules',
        'value': '[]',
        'default_value': '[]',
        'validation_rule': None,
        'description': '路径细粒度限流规则',
        'type': 'JSON',
        'group': 'SECURITY',
        'is_system': True,
    },
]


def upgrade() -> None:
    import sys
    import os
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    from database.utils.snowflake import snowflake
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    conn = op.get_bind()

    # ── A. Insert ip-blacklist MENU under 'manage' catalog ──
    manage_result = conn.execute(
        sa.text("SELECT id FROM sys_menu WHERE name = 'manage' AND type = 'CATALOG' LIMIT 1")
    ).fetchone()
    if manage_result is None:
        return
    manage_id = manage_result[0]

    # Check if menu already exists
    existing = conn.execute(
        sa.text("SELECT id FROM sys_menu WHERE name = 'manage_ip-blacklist' AND type = 'MENU' LIMIT 1")
    ).fetchone()
    if existing is None:
        blacklist_menu_id = snowflake.generate()
        # Determine next sort order under manage
        max_sort = conn.execute(
            sa.text("SELECT COALESCE(MAX(sort), 0) FROM sys_menu WHERE parent_id = :pid")
            .bindparams(pid=manage_id)
        ).scalar()
        next_sort = max_sort + 1

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
                'id': blacklist_menu_id,
                'parent_id': manage_id,
                'name': 'manage_ip-blacklist',
                'path': '/manage/ip-blacklist',
                'component': 'view.manage_ip-blacklist',
                'redirect': None,
                'permission': 'sys:blacklist:list',
                'meta_title': 'manage_ip-blacklist',
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
    else:
        blacklist_menu_id = existing[0]

    # ── B. Insert button permissions under ip-blacklist menu ──
    buttons = [
        ('查询', 'sys:blacklist:list', 1),
        ('新增', 'sys:blacklist:add', 2),
        ('删除', 'sys:blacklist:remove', 3),
    ]
    new_button_ids = []
    new_button_rows = []
    for label, perm_code, sort in buttons:
        existing_btn = conn.execute(
            sa.text(
                "SELECT id FROM sys_menu "
                "WHERE parent_id = :pid AND permission = :perm AND type = 'BUTTON' LIMIT 1"
            ).bindparams(pid=blacklist_menu_id, perm=perm_code)
        ).fetchone()
        if existing_btn is not None:
            continue
        btn_id = snowflake.generate()
        new_button_ids.append(btn_id)
        new_button_rows.append({
            'id': btn_id,
            'parent_id': blacklist_menu_id,
            'name': f'manage_ip-blacklist_{perm_code.split(":")[-1]}',
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

    if new_button_rows:
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
        op.bulk_insert(sys_menu, new_button_rows)

    # Bind new button menus to all existing roles
    if new_button_ids:
        role_rows = conn.execute(sa.text("SELECT id FROM sys_role")).fetchall()
        if role_rows:
            assoc_rows = [
                {'role_id': r[0], 'menu_id': mid, 'permission': 'read'}
                for r in role_rows
                for mid in new_button_ids
            ]
            sys_role_menu = sa.table(
                'sys_role_menu',
                sa.column('role_id', sa.BigInteger),
                sa.column('menu_id', sa.BigInteger),
                sa.column('permission', sa.String),
            )
            op.bulk_insert(sys_role_menu, assoc_rows)

    # ── C. Insert rate_limit default config rows (upsert) ──
    for cfg in _RATE_LIMIT_CONFIGS:
        # Skip if already exists
        existing_cfg = conn.execute(
            sa.text("SELECT id FROM sys_config WHERE key = :key").bindparams(key=cfg['key'])
        ).fetchone()
        if existing_cfg is not None:
            continue
        conn.execute(
            sa.text(
                'INSERT INTO sys_config '
                '(key, value, default_value, validation_rule, description, type, "group", is_system, created_at) '
                'VALUES (:key, :value, :default_value, :validation_rule, :description, '
                'CAST(:type AS configtype), CAST(:group AS configgroup), :is_system, :created_at)'
            ).bindparams(
                key=cfg['key'],
                value=cfg['value'],
                default_value=cfg['default_value'],
                validation_rule=cfg['validation_rule'],
                description=cfg['description'],
                type=cfg['type'],
                group=cfg['group'],
                is_system=cfg['is_system'],
                created_at=now,
            )
        )


def downgrade() -> None:
    # Remove rate_limit config rows
    op.execute(
        sa.text("DELETE FROM sys_config WHERE key LIKE 'rate_limit.%'")
    )
    # Remove button menus
    if _BLACKLIST_PERMS:
        op.execute(
            sa.text(
                "DELETE FROM sys_menu WHERE type = 'BUTTON' AND permission = ANY(:perms)"
            ).bindparams(perms=_BLACKLIST_PERMS)
        )
    # Remove the MENU entry
    op.execute(
        sa.text("DELETE FROM sys_menu WHERE name = 'manage_ip-blacklist' AND type = 'MENU'")
    )
