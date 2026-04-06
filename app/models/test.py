from app.extensions import db


class Test(db.Model):
    __tablename__ = "tests"
    __table_args__ = (
        db.Index("ix_tests_batch_date", "batch_id", "test_date"),
    )

    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey("batches.id", ondelete="CASCADE"), nullable=False, index=True)
    title = db.Column(db.String(150), nullable=False)
    subject = db.Column(db.String(120), nullable=True)
    max_marks = db.Column(db.Numeric(8, 2), nullable=False)
    test_date = db.Column(db.Date, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now(),
        onupdate=db.func.now(),
    )

    batch = db.relationship("Batch", lazy="joined")
    creator = db.relationship("User", lazy="joined")
    results = db.relationship("TestResult", back_populates="test", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "batch_id": self.batch_id,
            "title": self.title,
            "subject": self.subject,
            "max_marks": float(self.max_marks) if self.max_marks is not None else None,
            "test_date": self.test_date.isoformat() if self.test_date else None,
            "created_by": self.created_by,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
