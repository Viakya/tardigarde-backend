"""add_batch_resources

Revision ID: b3d2f4c1a9b7
Revises: 97335887aea2
Create Date: 2026-03-29 14:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b3d2f4c1a9b7'
down_revision = '97335887aea2'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'batch_resources',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('batch_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=180), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('url', sa.String(length=500), nullable=False),
        sa.Column('resource_type', sa.String(length=40), nullable=False, server_default='link'),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('visible_to_students', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['batch_id'], ['batches.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
    )
    op.create_index('ix_batch_resources_batch_id', 'batch_resources', ['batch_id'])
    op.create_index('ix_batch_resources_created_by', 'batch_resources', ['created_by'])
    op.create_index('ix_batch_resources_type', 'batch_resources', ['resource_type'])


def downgrade():
    op.drop_index('ix_batch_resources_type', table_name='batch_resources')
    op.drop_index('ix_batch_resources_created_by', table_name='batch_resources')
    op.drop_index('ix_batch_resources_batch_id', table_name='batch_resources')
    op.drop_table('batch_resources')
