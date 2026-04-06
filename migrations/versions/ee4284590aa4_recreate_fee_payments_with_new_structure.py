"""recreate_fee_payments_with_new_structure

Revision ID: ee4284590aa4
Revises: 43e059335ace
Create Date: 2026-02-28 22:04:52.100770

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'ee4284590aa4'
down_revision = '43e059335ace'
branch_labels = None
depends_on = None


def upgrade():
    # Create new fee_payments table with simplified structure
    op.create_table('fee_payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('payment_date', sa.Date(), server_default=sa.text('CURRENT_DATE'), nullable=False),
        sa.Column('payment_method', sa.String(length=30), nullable=False, server_default='cash'),
        sa.Column('reference_no', sa.String(length=100), nullable=True),
        sa.Column('received_by', sa.Integer(), nullable=False),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['received_by'], ['users.id'], name='fee_payments_received_by_fkey'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], name='fee_payments_student_id_fkey', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name='fee_payments_pkey')
    )
    op.create_index('ix_fee_payments_student_id', 'fee_payments', ['student_id'], unique=False)
    op.create_index('ix_fee_payments_received_by', 'fee_payments', ['received_by'], unique=False)
    op.create_index('ix_fee_payments_method', 'fee_payments', ['payment_method'], unique=False)
    op.create_index('ix_fee_payments_date', 'fee_payments', ['payment_date'], unique=False)


def downgrade():
    # Drop the fee_payments table
    op.drop_index('ix_fee_payments_date', table_name='fee_payments')
    op.drop_index('ix_fee_payments_method', table_name='fee_payments')
    op.drop_index('ix_fee_payments_received_by', table_name='fee_payments')
    op.drop_index('ix_fee_payments_student_id', table_name='fee_payments')
    op.drop_table('fee_payments')

