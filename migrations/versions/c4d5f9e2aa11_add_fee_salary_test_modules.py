"""add fee salary test modules

Revision ID: c4d5f9e2aa11
Revises: 9b8e1ab4c2d0
Create Date: 2026-02-26 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c4d5f9e2aa11"
down_revision = "9b8e1ab4c2d0"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "student_fees",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("batch_id", sa.Integer(), nullable=False),
        sa.Column("total_fee", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("discount_amount", sa.Numeric(precision=12, scale=2), server_default="0", nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["batch_id"], ["batches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_id", "batch_id", name="uq_student_fees_student_batch"),
    )
    op.create_index("ix_student_fees_batch_id", "student_fees", ["batch_id"], unique=False)
    op.create_index("ix_student_fees_due_date", "student_fees", ["due_date"], unique=False)
    op.create_index("ix_student_fees_student_id", "student_fees", ["student_id"], unique=False)

    op.create_table(
        "fee_payments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("student_fee_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("payment_date", sa.Date(), nullable=False),
        sa.Column("payment_method", sa.String(length=30), nullable=False),
        sa.Column("reference_no", sa.String(length=100), nullable=True),
        sa.Column("received_by", sa.Integer(), nullable=False),
        sa.Column("remarks", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["received_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["student_fee_id"], ["student_fees.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_fee_payments_date", "fee_payments", ["payment_date"], unique=False)
    op.create_index("ix_fee_payments_method", "fee_payments", ["payment_method"], unique=False)
    op.create_index("ix_fee_payments_received_by", "fee_payments", ["received_by"], unique=False)
    op.create_index("ix_fee_payments_student_fee_id", "fee_payments", ["student_fee_id"], unique=False)

    op.create_table(
        "salaries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("teacher_id", sa.Integer(), nullable=False),
        sa.Column("salary_month", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("paid_amount", sa.Numeric(precision=12, scale=2), server_default="0", nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("payment_date", sa.Date(), nullable=True),
        sa.Column("paid_by", sa.Integer(), nullable=True),
        sa.Column("remarks", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["paid_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["teacher_id"], ["teachers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("teacher_id", "salary_month", name="uq_salary_teacher_month"),
    )
    op.create_index("ix_salaries_month", "salaries", ["salary_month"], unique=False)
    op.create_index("ix_salaries_status", "salaries", ["status"], unique=False)
    op.create_index("ix_salaries_teacher_id", "salaries", ["teacher_id"], unique=False)

    op.create_table(
        "tests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("batch_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("subject", sa.String(length=120), nullable=True),
        sa.Column("max_marks", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("test_date", sa.Date(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["batch_id"], ["batches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tests_batch_date", "tests", ["batch_id", "test_date"], unique=False)
    op.create_index("ix_tests_batch_id", "tests", ["batch_id"], unique=False)

    op.create_table(
        "test_results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("test_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("marks_obtained", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("remarks", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["test_id"], ["tests.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("test_id", "student_id", name="uq_test_results_test_student"),
    )
    op.create_index("ix_test_results_student", "test_results", ["student_id"], unique=False)
    op.create_index("ix_test_results_test_id", "test_results", ["test_id"], unique=False)


def downgrade():
    op.drop_index("ix_test_results_test_id", table_name="test_results")
    op.drop_index("ix_test_results_student", table_name="test_results")
    op.drop_table("test_results")

    op.drop_index("ix_tests_batch_id", table_name="tests")
    op.drop_index("ix_tests_batch_date", table_name="tests")
    op.drop_table("tests")

    op.drop_index("ix_salaries_teacher_id", table_name="salaries")
    op.drop_index("ix_salaries_status", table_name="salaries")
    op.drop_index("ix_salaries_month", table_name="salaries")
    op.drop_table("salaries")

    op.drop_index("ix_fee_payments_student_fee_id", table_name="fee_payments")
    op.drop_index("ix_fee_payments_received_by", table_name="fee_payments")
    op.drop_index("ix_fee_payments_method", table_name="fee_payments")
    op.drop_index("ix_fee_payments_date", table_name="fee_payments")
    op.drop_table("fee_payments")

    op.drop_index("ix_student_fees_student_id", table_name="student_fees")
    op.drop_index("ix_student_fees_due_date", table_name="student_fees")
    op.drop_index("ix_student_fees_batch_id", table_name="student_fees")
    op.drop_table("student_fees")
