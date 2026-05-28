"""fix corrupted menu data: paths, meta_titles, component, and set i18n_key

Revision ID: b6c7d8e9f0a1
Revises: a5b6c7d8e9f0
Create Date: 2026-05-28 19:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b6c7d8e9f0a1'
down_revision = 'a5b6c7d8e9f0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Fix corrupted paths (remove "route." prefix duplication)
    op.execute("""
        UPDATE sys_menu SET path = '/manage'
        WHERE id = 2874692539129857 AND path = '/route.route.manage';
    """)
    op.execute("""
        UPDATE sys_menu SET path = '/log/operation-log'
        WHERE id = 2874692539129865 AND path = '/route.log/operation-log';
    """)

    # 2. Fix corrupted meta_titles (strip "route." prefixes, store route name only)
    op.execute("""
        UPDATE sys_menu SET meta_title = 'home'
        WHERE id = 2874692539129856 AND meta_title = 'route.home';
    """)
    op.execute("""
        UPDATE sys_menu SET meta_title = 'manage'
        WHERE id = 2874692539129857 AND meta_title = 'route.route.route.manage';
    """)
    op.execute("""
        UPDATE sys_menu SET meta_title = 'log_operation-log'
        WHERE id = 2874692539129865 AND meta_title = 'route.route.log_operation-log';
    """)
    op.execute("""
        UPDATE sys_menu SET meta_title = 'monitor'
        WHERE id = 1900000000000000001 AND meta_title = 'route.monitor';
    """)

    # 3. Fix monitor component (missing layout wrapper)
    op.execute("""
        UPDATE sys_menu SET component = 'layout.base$view.monitor'
        WHERE id = 1900000000000000001 AND component = 'view.monitor';
    """)

    # 4. Set i18n_key for top-level and menu-type entries (generate from name)
    op.execute("""
        UPDATE sys_menu SET i18n_key = 'route.' || name
        WHERE type IN ('CATALOG', 'MENU') AND i18n_key IS NULL;
    """)

    # 5. Set meta_title = name for menus where meta_title is empty
    op.execute("""
        UPDATE sys_menu SET meta_title = name
        WHERE type IN ('CATALOG', 'MENU') AND (meta_title IS NULL OR meta_title = '');
    """)


def downgrade() -> None:
    # Revert path changes
    op.execute("""
        UPDATE sys_menu SET path = '/route.route.manage'
        WHERE id = 2874692539129857;
    """)
    op.execute("""
        UPDATE sys_menu SET path = '/route.log/operation-log'
        WHERE id = 2874692539129865;
    """)

    # Revert meta_title changes
    op.execute("""
        UPDATE sys_menu SET meta_title = 'route.home'
        WHERE id = 2874692539129856;
    """)
    op.execute("""
        UPDATE sys_menu SET meta_title = 'route.route.route.manage'
        WHERE id = 2874692539129857;
    """)
    op.execute("""
        UPDATE sys_menu SET meta_title = 'route.route.log_operation-log'
        WHERE id = 2874692539129865;
    """)
    op.execute("""
        UPDATE sys_menu SET meta_title = 'route.monitor'
        WHERE id = 1900000000000000001;
    """)

    # Revert monitor component
    op.execute("""
        UPDATE sys_menu SET component = 'view.monitor'
        WHERE id = 1900000000000000001;
    """)

    # Clear i18n_key values
    op.execute("""
        UPDATE sys_menu SET i18n_key = NULL;
    """)
