"""tambah kolom MT DATE di tabel stripping

Revision ID: 9ed37ef04f6c
Revises: 8bce897896b4
Create Date: 2025-08-10 17:25:32.144033

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = '9ed37ef04f6c'
down_revision = '8bce897896b4'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('stripping', schema=None) as batch_op:
        batch_op.add_column(sa.Column('MT DATE', sa.Date(), nullable=True))


def downgrade():
    with op.batch_alter_table('stripping', schema=None) as batch_op:
        batch_op.drop_column('MT DATE')
