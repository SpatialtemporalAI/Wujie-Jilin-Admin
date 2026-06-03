"""seed gender dictionary with items

Revision ID: j3k4l5m6n7o8
Revises: i2j3k4l5m6n7
Create Date: 2026-06-03

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'j3k4l5m6n7o8'
down_revision = 'i2j3k4l5m6n7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    dict_table = sa.table(
        'sys_dict',
        sa.column('id', sa.BigInteger),
        sa.column('name', sa.String),
        sa.column('code', sa.String),
        sa.column('description', sa.Text),
        sa.column('status', sa.Boolean),
        sa.column('is_system', sa.Boolean),
        sa.column('sort', sa.Integer),
    )

    item_table = sa.table(
        'sys_dict_item',
        sa.column('id', sa.BigInteger),
        sa.column('dict_id', sa.BigInteger),
        sa.column('value', sa.String),
        sa.column('label', sa.String),
        sa.column('description', sa.Text),
        sa.column('status', sa.Boolean),
        sa.column('sort', sa.Integer),
    )

    op.bulk_insert(dict_table, [
        {
            'name': '性别',
            'code': 'gender',
            'description': '性别字典：男、女、未知',
            'status': True,
            'is_system': True,
            'sort': 1,
        },
    ])

    conn = op.get_bind()
    result = conn.execute(
        sa.text("SELECT id FROM sys_dict WHERE code = :code"),
        {'code': 'gender'},
    )
    dict_id = result.scalar_one()

    op.bulk_insert(item_table, [
        {'dict_id': dict_id, 'value': '1', 'label': '男', 'status': True, 'sort': 1},
        {'dict_id': dict_id, 'value': '2', 'label': '女', 'status': True, 'sort': 2},
        {'dict_id': dict_id, 'value': '0', 'label': '未知', 'status': True, 'sort': 3},
    ])


def downgrade() -> None:
    conn = op.get_bind()
    result = conn.execute(
        sa.text("SELECT id FROM sys_dict WHERE code = :code"),
        {'code': 'gender'},
    )
    row = result.scalar_one_or_none()

    if row is not None:
        op.execute(
            sa.text("DELETE FROM sys_dict_item WHERE dict_id = :dict_id"),
            {'dict_id': row},
        )

    op.execute(sa.text("DELETE FROM sys_dict WHERE code = :code"), {'code': 'gender'})
