from app.extensions import db


class TestResult(db.Model):
    __tablename__ = "test_results"
    __table_args__ = (
        db.UniqueConstraint("test_id", "student_id", name="uq_test_results_test_student"),
        db.Index("ix_test_results_student", "student_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey("tests.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    marks_obtained = db.Column(db.Numeric(8, 2), nullable=False)
    remarks = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now(),
        onupdate=db.func.now(),
    )

    test = db.relationship("Test", back_populates="results", lazy="joined")
    student = db.relationship("Student", lazy="joined")

    def to_dict(self):
        max_marks = float(self.test.max_marks) if self.test and self.test.max_marks is not None else None
        obtained = float(self.marks_obtained) if self.marks_obtained is not None else None
        percentage = (obtained / max_marks * 100) if max_marks and obtained is not None else None

        return {
            "id": self.id,
            "test_id": self.test_id,
            "student_id": self.student_id,
            "marks_obtained": obtained,
            "max_marks": max_marks,
            "percentage": round(percentage, 2) if percentage is not None else None,
            "remarks": self.remarks,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
