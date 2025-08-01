"""Add hybrid customer model and link to MWS

Revision ID: 95058e8fb291
Revises: 26d5fc08b14b
Create Date: 2025-07-27 12:26:58.729319

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '95058e8fb291'
down_revision = '26d5fc08b14b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('customers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=80), nullable=False),
    sa.Column('password', sa.String(length=256), nullable=False),
    sa.Column('company_name', sa.String(length=150), nullable=False),
    sa.Column('role', sa.String(length=50), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('username')
    )
    with op.batch_alter_table('customers', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_customers_company_name'), ['company_name'], unique=False)

    with op.batch_alter_table('mws_parts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('customer_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'customers', ['customer_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('mws_parts', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('customer_id')

    with op.batch_alter_table('customers', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_customers_company_name'))

    op.drop_table('customers')
    # ### end Alembic commands ###
