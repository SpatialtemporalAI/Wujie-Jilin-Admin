"""remove redundant manage_notification menu

Revision ID: d0e1f2a3b4c5
Revises: c9d0e1f2a3b4
Create Date: 2026-05-28 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'd0e1f2a3b4c5'
down_revision = 'c9d0e1f2a3b4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # Find all manage_notification related menu IDs
    result = conn.execute(
        sa.text("SELECT id FROM sys_menu WHERE name LIKE 'manage_notification%'")
    ).fetchall()

    menu_ids = [r[0] for r in result]

    if menu_ids:
        # Remove role-menu associations first
        conn.execute(
            sa.text(
                "DELETE FROM sys_role_menu WHERE menu_id = ANY(:menu_ids)"
            ).bindparams(menu_ids=menu_ids)
        )

        # Remove the menu entries
        conn.execute(
            sa.text(
                "DELETE FROM sys_menu WHERE name LIKE 'manage_notification%'"
            )
        )


def downgrade() -> None:
    # The notification menu was pointing to a non-existent view (view.manage_notification).
    # Restoring it would re-introduce the broken route, so downgrade is a no-op.
    pass
