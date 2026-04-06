from app.extensions import db


class Attendance(db.Model):
    __tablename__ = "attendances"
    __table_args__ = (
        db.UniqueConstraint("student_id", "attendance_date", name="uq_attendance_student_date"),
        db.Index("ix_attendances_batch_date", "batch_id", "attendance_date"),
        db.Index("ix_attendances_marked_by", "marked_by"),
    )

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    batch_id = db.Column(db.Integer, db.ForeignKey("batches.id", ondelete="CASCADE"), nullable=False, index=True)
    attendance_date = db.Column(db.Date, nullable=False, server_default=db.func.current_date(), index=True)
    status = db.Column(db.String(20), nullable=False)
    marked_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    remarks = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now(),
        onupdate=db.func.now(),
    )

    student = db.relationship("Student", lazy="joined")
    batch = db.relationship("Batch", lazy="joined")
    marker = db.relationship("User", lazy="joined")

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "batch_id": self.batch_id,
            "attendance_date": self.attendance_date.isoformat() if self.attendance_date else None,
            "status": self.status,
            "marked_by": self.marked_by,
            "remarks": self.remarks,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "student": {
                "id": self.student.id,
                "user_id": self.student.user_id,
                "full_name": self.student.user.full_name if self.student and self.student.user else None,
            }
            if self.student
            else {},
            "batch": {
                "id": self.batch.id,
                "batch_name": self.batch.batch_name,
                "year": self.batch.year,
            }
            if self.batch
            else {},
            "marker": {
                "id": self.marker.id,
                "email": self.marker.email,
                "full_name": self.marker.full_name,
                "role": self.marker.role,
            }
            if self.marker
            else {},
        }
