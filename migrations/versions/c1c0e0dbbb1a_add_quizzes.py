"""add_quizzes

Revision ID: c1c0e0dbbb1a
Revises: 0d73f9cc2229
Create Date: 2026-03-30 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c1c0e0dbbb1a'
down_revision = '0d73f9cc2229'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'quizzes',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('batch_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=180), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('difficulty', sa.String(length=20), nullable=False, server_default='medium'),
        sa.Column('total_marks', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('question_count', sa.Integer(), nullable=False),
        sa.Column('mode', sa.String(length=20), nullable=False, server_default='practice'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='draft'),
        sa.Column('open_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('close_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['batch_id'], ['batches.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
    )
    op.create_index('ix_quizzes_batch_id', 'quizzes', ['batch_id'])
    op.create_index('ix_quizzes_status', 'quizzes', ['status'])

    op.create_table(
        'quiz_questions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('quiz_id', sa.Integer(), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('option_a', sa.Text(), nullable=False),
        sa.Column('option_b', sa.Text(), nullable=False),
        sa.Column('option_c', sa.Text(), nullable=False),
        sa.Column('option_d', sa.Text(), nullable=False),
        sa.Column('correct_option', sa.String(length=1), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('marks', sa.Numeric(6, 2), nullable=False),
        sa.ForeignKeyConstraint(['quiz_id'], ['quizzes.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_quiz_questions_quiz_id', 'quiz_questions', ['quiz_id'])

    op.create_table(
        'quiz_submissions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('quiz_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('score', sa.Numeric(6, 2), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='submitted'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['quiz_id'], ['quizzes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('quiz_id', 'student_id', name='uq_quiz_submission_student'),
    )
    op.create_index('ix_quiz_submissions_quiz_id', 'quiz_submissions', ['quiz_id'])
    op.create_index('ix_quiz_submissions_student_id', 'quiz_submissions', ['student_id'])

    op.create_table(
        'quiz_answers',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('submission_id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('selected_option', sa.String(length=1), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('marks_awarded', sa.Numeric(6, 2), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['submission_id'], ['quiz_submissions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['question_id'], ['quiz_questions.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_quiz_answers_submission_id', 'quiz_answers', ['submission_id'])
    op.create_index('ix_quiz_answers_question_id', 'quiz_answers', ['question_id'])


def downgrade():
    op.drop_index('ix_quiz_answers_question_id', table_name='quiz_answers')
    op.drop_index('ix_quiz_answers_submission_id', table_name='quiz_answers')
    op.drop_table('quiz_answers')

    op.drop_index('ix_quiz_submissions_student_id', table_name='quiz_submissions')
    op.drop_index('ix_quiz_submissions_quiz_id', table_name='quiz_submissions')
    op.drop_table('quiz_submissions')

    op.drop_index('ix_quiz_questions_quiz_id', table_name='quiz_questions')
    op.drop_table('quiz_questions')

    op.drop_index('ix_quizzes_status', table_name='quizzes')
    op.drop_index('ix_quizzes_batch_id', table_name='quizzes')
    op.drop_table('quizzes')
