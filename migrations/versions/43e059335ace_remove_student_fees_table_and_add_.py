"""remove_student_fees_table_and_add_discount_percent

Revision ID: 43e059335ace
Revises: d88bca084046
Create Date: 2026-02-28 21:46:33.039849

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '43e059335ace'
down_revision = 'd88bca084046'
branch_labels = None
depends_on = None


def upgrade():
    # Add discount_percent column to students table
    op.add_column('students', sa.Column('discount_percent', sa.Numeric(precision=5, scale=2), server_default='0', nullable=False))
    
    # Drop fee_payments table first (has FK to student_fees)
    op.drop_table('fee_payments')
    
    # Then drop student_fees table
    op.drop_table('student_fees')


def downgrade():
    # Recreate student_fees table first
    op.create_table('student_fees',
        sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('student_id', sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column('batch_id', sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column('total_fee', sa.NUMERIC(precision=12, scale=2), autoincrement=False, nullable=False),
        sa.Column('discount_amount', sa.NUMERIC(precision=12, scale=2), server_default='0', autoincrement=False, nullable=False),
        sa.Column('due_date', sa.DATE(), autoincrement=False, nullable=True),
        sa.Column('is_active', sa.BOOLEAN(), autoincrement=False, nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(['batch_id'], ['batches.id'], name='student_fees_batch_id_fkey', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], name='student_fees_student_id_fkey', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name='student_fees_pkey'),
        sa.UniqueConstraint('student_id', 'batch_id', name='uq_student_fees_student_batch')
    )
    op.create_index('ix_student_fees_student_id', 'student_fees', ['student_id'], unique=False)
    op.create_index('ix_student_fees_due_date', 'student_fees', ['due_date'], unique=False)
    op.create_index('ix_student_fees_batch_id', 'student_fees', ['batch_id'], unique=False)
    
    # Recreate fee_payments table
    op.create_table('fee_payments',
        sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('student_fee_id', sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column('amount', sa.NUMERIC(precision=12, scale=2), autoincrement=False, nullable=False),
        sa.Column('payment_date', sa.DATE(), server_default=sa.text('CURRENT_DATE'), autoincrement=False, nullable=False),
        sa.Column('payment_method', sa.VARCHAR(length=30), autoincrement=False, nullable=False),
        sa.Column('reference_no', sa.VARCHAR(length=100), autoincrement=False, nullable=True),
        sa.Column('received_by', sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column('remarks', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
        sa.Column('is_active', sa.BOOLEAN(), autoincrement=False, nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(['received_by'], ['users.id'], name='fee_payments_received_by_fkey'),
        sa.ForeignKeyConstraint(['student_fee_id'], ['student_fees.id'], name='fee_payments_student_fee_id_fkey', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name='fee_payments_pkey')
    )
    op.create_index('ix_fee_payments_student_fee_id', 'fee_payments', ['student_fee_id'], unique=False)
    op.create_index('ix_fee_payments_received_by', 'fee_payments', ['received_by'], unique=False)
    op.create_index('ix_fee_payments_method', 'fee_payments', ['payment_method'], unique=False)
    op.create_index('ix_fee_payments_date', 'fee_payments', ['payment_date'], unique=False)
    
    # Remove discount_percent column from students table
    op.drop_column('students', 'discount_percent')


