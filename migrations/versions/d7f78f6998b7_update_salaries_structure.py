"""update_salaries_structure

Revision ID: d7f78f6998b7
Revises: d91603e6f6d4
Create Date: 2026-03-01 18:51:57.583051

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd7f78f6998b7'
down_revision = 'd91603e6f6d4'
branch_labels = None
depends_on = None


def upgrade():
    # Drop obsolete index if exists
    op.execute("DROP INDEX IF EXISTS ix_salaries_status")
    
    # Drop obsolete columns
    op.drop_column('salaries', 'paid_amount')
    op.drop_column('salaries', 'status')
    op.drop_column('salaries', 'is_active')
    
    # Add new columns
    op.add_column('salaries', sa.Column('payment_method', sa.String(30), server_default='cash'))
    op.add_column('salaries', sa.Column('reference_no', sa.String(100), nullable=True))
    
    # Make payment_date not nullable with default (use existing data or set default)
    op.execute("UPDATE salaries SET payment_date = CURRENT_DATE WHERE payment_date IS NULL")
    op.alter_column('salaries', 'payment_date', nullable=False, server_default=sa.text('CURRENT_DATE'))
    
    # Change remarks to Text
    op.alter_column('salaries', 'remarks', type_=sa.Text())


def downgrade():
    # Reverse changes
    op.drop_column('salaries', 'payment_method')
    op.drop_column('salaries', 'reference_no')
    op.add_column('salaries', sa.Column('paid_amount', sa.Numeric(12, 2), server_default='0'))
    op.add_column('salaries', sa.Column('status', sa.String(20), server_default='pending'))
    op.add_column('salaries', sa.Column('is_active', sa.Boolean(), server_default='true'))
    op.create_index('ix_salaries_status', 'salaries', ['status'])
