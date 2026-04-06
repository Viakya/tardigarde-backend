from app.extensions import db


batch_teachers = db.Table(
    "batch_teachers",
    db.Column("batch_id", db.Integer, db.ForeignKey("batches.id"), primary_key=True),
    db.Column("teacher_id", db.Integer, db.ForeignKey("teachers.id"), primary_key=True),
    db.Column("assigned_at", db.DateTime(timezone=True), nullable=False, server_default=db.func.now()),
    db.Index("ix_batch_teachers_batch_id", "batch_id"),
    db.Index("ix_batch_teachers_teacher_id", "teacher_id"),
)


parent_students = db.Table(
    "parent_students",
    db.Column("parent_user_id", db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    db.Column("student_id", db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), primary_key=True),
    db.Column("linked_at", db.DateTime(timezone=True), nullable=False, server_default=db.func.now()),
    db.Index("ix_parent_students_parent_user_id", "parent_user_id"),
    db.Index("ix_parent_students_student_id", "student_id"),
)
