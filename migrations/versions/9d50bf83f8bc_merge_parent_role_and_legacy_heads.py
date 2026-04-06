"""merge parent-role and legacy heads

Revision ID: 9d50bf83f8bc
Revises: 2f8c30e11ab2, c4d5f9e2aa11
Create Date: 2026-02-27 21:13:18.854016

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9d50bf83f8bc'
down_revision = ('2f8c30e11ab2', 'c4d5f9e2aa11')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
