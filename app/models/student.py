from app.extensions import db


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    batch_id = db.Column(db.Integer, db.ForeignKey("batches.id", ondelete="SET NULL"), nullable=True, index=True)
    phone_number = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    enrollment_date = db.Column(db.Date, nullable=False, server_default=db.func.current_date())
    discount_percent = db.Column(db.Numeric(5, 2), nullable=False, server_default="0")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now(),
        onupdate=db.func.now(),
    )

    user = db.relationship("User", back_populates="student_profile")
    batch = db.relationship("Batch", back_populates="students")
    parents = db.relationship(
        "User",
        secondary="parent_students",
        back_populates="children",
        lazy="selectin",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "batch_id": self.batch_id,
            "phone_number": self.phone_number,
            "address": self.address,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "enrollment_date": self.enrollment_date.isoformat() if self.enrollment_date else None,
            "discount_percent": float(self.discount_percent) if self.discount_percent is not None else 0,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "user": {
                "id": self.user.id,
                "email": self.user.email,
                "full_name": self.user.full_name,
                "role": self.user.role,
            }
            if self.user
            else {},
            "batch": {
                "id": self.batch.id,
                "batch_name": self.batch.batch_name,
                "year": self.batch.year,
                "batch_cost": float(self.batch.batch_cost) if self.batch.batch_cost else 0.0,
            }
            if self.batch
            else {},
            "parent_user_ids": [parent.id for parent in self.parents if parent.is_active],
            "parents": [
                {
                    "id": parent.id,
                    "email": parent.email,
                    "full_name": parent.full_name,
                    "role": parent.role,
                }
                for parent in self.parents
                if parent.is_active
            ],
        }
