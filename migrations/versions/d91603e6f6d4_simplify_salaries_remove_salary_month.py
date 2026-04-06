"""simplify_salaries_remove_salary_month

Revision ID: d91603e6f6d4
Revises: 97335887aea2
Create Date: 2026-03-01 18:50:14.634387

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd91603e6f6d4'
down_revision = '97335887aea2'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the unique constraint that uses salary_month
    op.drop_constraint('uq_salary_teacher_month', 'salaries', type_='unique')
    
    # Drop the index on salary_month
    op.drop_index('ix_salaries_month', table_name='salaries')
    
    # Drop the salary_month column
    op.drop_column('salaries', 'salary_month')


def downgrade():
    # Re-add salary_month column
    op.add_column('salaries', sa.Column('salary_month', sa.Date(), nullable=True))
    
    # Re-add index
    op.create_index('ix_salaries_month', 'salaries', ['salary_month'])
    
    # Re-add unique constraint (can't fully restore as data would be lost)
    op.create_unique_constraint('uq_salary_teacher_month', 'salaries', ['teacher_id', 'salary_month'])
