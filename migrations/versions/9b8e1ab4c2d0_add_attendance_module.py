"""add attendance module

Revision ID: 9b8e1ab4c2d0
Revises: f9090b739cd7
Create Date: 2026-02-26 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9b8e1ab4c2d0"
down_revision = "f9090b739cd7"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "attendances",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("batch_id", sa.Integer(), nullable=False),
        sa.Column("attendance_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("marked_by", sa.Integer(), nullable=False),
        sa.Column("remarks", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["batch_id"], ["batches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["marked_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_id", "attendance_date", name="uq_attendance_student_date"),
    )

    op.create_index("ix_attendances_attendance_date", "attendances", ["attendance_date"], unique=False)
    op.create_index("ix_attendances_batch_date", "attendances", ["batch_id", "attendance_date"], unique=False)
    op.create_index("ix_attendances_batch_id", "attendances", ["batch_id"], unique=False)
    op.create_index("ix_attendances_marked_by", "attendances", ["marked_by"], unique=False)
    op.create_index("ix_attendances_student_id", "attendances", ["student_id"], unique=False)


def downgrade():
    op.drop_index("ix_attendances_student_id", table_name="attendances")
    op.drop_index("ix_attendances_marked_by", table_name="attendances")
    op.drop_index("ix_attendances_batch_id", table_name="attendances")
    op.drop_index("ix_attendances_batch_date", table_name="attendances")
    op.drop_index("ix_attendances_attendance_date", table_name="attendances")
    op.drop_table("attendances")
