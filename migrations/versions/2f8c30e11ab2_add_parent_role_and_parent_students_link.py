"""add parent role and parent-student link

Revision ID: 2f8c30e11ab2
Revises: f9090b739cd7
Create Date: 2026-02-27 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2f8c30e11ab2"
down_revision = "f9090b739cd7"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "parent_students",
        sa.Column("parent_user_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("linked_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["parent_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("parent_user_id", "student_id"),
    )
    op.create_index("ix_parent_students_parent_user_id", "parent_students", ["parent_user_id"], unique=False)
    op.create_index("ix_parent_students_student_id", "parent_students", ["student_id"], unique=False)


def downgrade():
    op.drop_index("ix_parent_students_student_id", table_name="parent_students")
    op.drop_index("ix_parent_students_parent_user_id", table_name="parent_students")
    op.drop_table("parent_students")
