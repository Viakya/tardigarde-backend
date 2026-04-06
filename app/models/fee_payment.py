from app.extensions import db


class FeePayment(db.Model):
    __tablename__ = "fee_payments"
    __table_args__ = (
        db.Index("ix_fee_payments_date", "payment_date"),
        db.Index("ix_fee_payments_method", "payment_method"),
    )

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(
        db.Integer,
        db.ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    payment_date = db.Column(db.Date, nullable=False, server_default=db.func.current_date())
    payment_method = db.Column(db.String(30), nullable=False, default="cash")
    reference_no = db.Column(db.String(100), nullable=True)
    received_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    remarks = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now(),
        onupdate=db.func.now(),
    )

    student = db.relationship("Student", lazy="joined")
    receiver = db.relationship("User", lazy="joined")

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "amount": float(self.amount) if self.amount is not None else None,
            "payment_date": self.payment_date.isoformat() if self.payment_date else None,
            "payment_method": self.payment_method,
            "reference_no": self.reference_no,
            "received_by": self.received_by,
            "remarks": self.remarks,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "student": {
                "id": self.student.id,
                "user": {
                    "full_name": self.student.user.full_name,
                    "email": self.student.user.email,
                }
            } if self.student else None,
            "receiver_name": self.receiver.full_name if self.receiver else None,
        }

