from app.extensions import db


class Batch(db.Model):
    __tablename__ = "batches"
    __table_args__ = (
        db.UniqueConstraint("batch_name", "year", name="uq_batches_batch_name_year"),
    )

    id = db.Column(db.Integer, primary_key=True)
    batch_name = db.Column(db.String(120), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    batch_cost = db.Column(db.Numeric(10, 2), nullable=False, server_default="10000.00")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now(),
        onupdate=db.func.now(),
    )

    students = db.relationship("Student", back_populates="batch")
    teachers = db.relationship("Teacher", secondary="batch_teachers", back_populates="batches")
    resources = db.relationship("BatchResource", back_populates="batch", cascade="all, delete-orphan")
    quizzes = db.relationship("Quiz", back_populates="batch", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "batch_name": self.batch_name,
            "year": self.year,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "batch_cost": float(self.batch_cost) if self.batch_cost else 0.0,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "teachers": [
                {
                    "id": teacher.id,
                    "user_id": teacher.user_id,
                    "full_name": teacher.user.full_name if teacher.user else None,
                }
                for teacher in self.teachers
                if teacher.is_active
            ],
        }
