from decimal import Decimal

from app.extensions import db


class Salary(db.Model):
    __tablename__ = "salaries"

    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    payment_date = db.Column(db.Date, nullable=False, server_default=db.func.current_date())
    payment_method = db.Column(db.String(30), default="cash")
    reference_no = db.Column(db.String(100), nullable=True)
    paid_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    remarks = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now(),
        onupdate=db.func.now(),
    )

    teacher = db.relationship("Teacher", lazy="joined")
    payer = db.relationship("User", lazy="joined")

    def to_dict(self):
        return {
            "id": self.id,
            "teacher_id": self.teacher_id,
            "amount": float(self.amount) if self.amount is not None else 0.0,
            "payment_date": self.payment_date.isoformat() if self.payment_date else None,
            "payment_method": self.payment_method,
            "reference_no": self.reference_no,
            "paid_by": self.paid_by,
            "payer_name": self.payer.full_name if self.payer else None,
            "remarks": self.remarks,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "teacher": {
                "id": self.teacher.id,
                "user": {
                    "id": self.teacher.user.id,
                    "full_name": self.teacher.user.full_name,
                    "email": self.teacher.user.email,
                }
            } if self.teacher and self.teacher.user else None,
        }
