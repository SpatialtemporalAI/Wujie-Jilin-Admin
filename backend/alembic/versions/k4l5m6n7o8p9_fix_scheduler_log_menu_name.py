"""fix scheduler log menu name

Revision ID: k4l5m6n7o8p9
Revises: j3k4l5m6n7o8
Create Date: 2026-06-03

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'k4l5m6n7o8p9'
down_revision = 'ed6be07ef320'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "UPDATE sys_menu SET name = 'manage_scheduler-log' "
        "WHERE name = 'scheduler_log' AND path = '/manage/scheduler-log'"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE sys_menu SET name = 'scheduler_log' "
        "WHERE name = 'manage_scheduler-log' AND path = '/manage/scheduler-log'"
    )
