"""fix oversized menu IDs that exceed JavaScript safe integer range (2^53)

Revision ID: c1d2e3f4a5b6
Revises: edc1e19c6cc2
Create Date: 2026-05-29 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c1d2e3f4a5b6'
down_revision = 'edc1e19c6cc2'
branch_labels = None
depends_on = None

JS_MAX_SAFE_INTEGER = 9007199254740992  # 2^53


def upgrade() -> None:
    """Reassign all menu IDs exceeding 2^53 to safe values."""
    conn = op.get_bind()

    # Find all oversized menu IDs
    result = conn.execute(
        sa.text("SELECT id FROM sys_menu WHERE id >= :limit ORDER BY id"),
        {"limit": JS_MAX_SAFE_INTEGER}
    )
    oversized_ids = [row[0] for row in result.fetchall()]

    if not oversized_ids:
        return

    # Get current max safe ID as starting point for new IDs
    result = conn.execute(
        sa.text("SELECT COALESCE(MAX(id), 0) FROM sys_menu WHERE id < :limit"),
        {"limit": JS_MAX_SAFE_INTEGER}
    )
    next_id = result.scalar() + 1

    # Build old→new ID mapping
    id_map = {}
    for old_id in oversized_ids:
        id_map[old_id] = next_id
        next_id += 1

    # Drop FK constraints temporarily
    op.drop_constraint('sys_role_menu_menu_id_fkey', 'sys_role_menu', type_='foreignkey')
    op.drop_constraint('sys_role_menu_role_id_fkey', 'sys_role_menu', type_='foreignkey')
    op.drop_constraint('sys_menu_parent_id_fkey', 'sys_menu', type_='foreignkey')

    for old_id, new_id in id_map.items():
        # Update role-menu associations
        conn.execute(
            sa.text("UPDATE sys_role_menu SET menu_id = :new_id WHERE menu_id = :old_id"),
            {"new_id": new_id, "old_id": old_id}
        )
        # Update parent references in child menus
        conn.execute(
            sa.text("UPDATE sys_menu SET parent_id = :new_id WHERE parent_id = :old_id"),
            {"new_id": new_id, "old_id": old_id}
        )
        # Update the menu ID itself
        conn.execute(
            sa.text("UPDATE sys_menu SET id = :new_id WHERE id = :old_id"),
            {"new_id": new_id, "old_id": old_id}
        )

    # Recreate FK constraints
    op.create_foreign_key('sys_role_menu_menu_id_fkey', 'sys_role_menu', 'sys_menu', ['menu_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('sys_role_menu_role_id_fkey', 'sys_role_menu', 'sys_role', ['role_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('sys_menu_parent_id_fkey', 'sys_menu', 'sys_menu', ['parent_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    """Downgrade is not supported for this migration."""
    pass
