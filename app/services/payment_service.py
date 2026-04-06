import hmac
import hashlib
from decimal import Decimal

import razorpay
from flask import current_app

from app.core.exceptions import ValidationError
from app.extensions import db
from app.models import FeePayment, Student
from app.services.fee_service import create_fee_payment


def _get_razorpay_client() -> razorpay.Client:
    key_id = current_app.config.get("RAZORPAY_KEY_ID")
    key_secret = current_app.config.get("RAZORPAY_KEY_SECRET")

    if not key_id or not key_secret:
        raise ValidationError("Payment gateway not configured", 500)

    return razorpay.Client(auth=(key_id, key_secret))


def _get_remaining_fee(student_id: int) -> Decimal:
    student = Student.query.filter_by(id=student_id, is_active=True).first()
    if not student:
        raise ValidationError("Student not found", 404)

    if not student.batch:
        raise ValidationError("Student is not assigned to a batch")

    batch_cost = Decimal(str(student.batch.batch_cost or 0))
    discount = Decimal(str(student.discount_percent or 0))
    total_fee = batch_cost - (batch_cost * discount / Decimal("100"))

    paid = db.session.query(db.func.coalesce(db.func.sum(FeePayment.amount), 0)).filter(
        FeePayment.student_id == student.id
    ).scalar()
    paid_amount = Decimal(str(paid or 0))

    remaining = total_fee - paid_amount
    return remaining if remaining > 0 else Decimal("0")


def create_razorpay_order(student_id: int, amount_in_rupees: float) -> dict:
    if amount_in_rupees <= 0:
        raise ValidationError("Amount must be greater than 0")

    remaining = _get_remaining_fee(student_id)
    amount_decimal = Decimal(str(amount_in_rupees))

    if remaining <= 0:
        raise ValidationError("Fee already fully paid")

    if amount_decimal > remaining:
        raise ValidationError("Amount exceeds remaining fee")

    client = _get_razorpay_client()
    amount_paise = int(Decimal(str(amount_in_rupees)) * 100)

    order = client.order.create(
        {
            "amount": amount_paise,
            "currency": "INR",
            "payment_capture": 1,
            "notes": {"student_id": str(student_id)},
        }
    )

    return order


def verify_razorpay_signature(order_id: str, payment_id: str, signature: str) -> bool:
    secret = current_app.config.get("RAZORPAY_KEY_SECRET")
    if not secret:
        raise ValidationError("Payment gateway not configured", 500)

    message = f"{order_id}|{payment_id}".encode("utf-8")
    generated_signature = hmac.new(
        secret.encode("utf-8"),
        msg=message,
        digestmod=hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(generated_signature, signature)


def record_successful_payment(
    student_id: int,
    amount_in_rupees: float,
    payment_id: str,
    receiver_user_id: int,
):
    remaining = _get_remaining_fee(student_id)
    amount_decimal = Decimal(str(amount_in_rupees))
    if amount_decimal <= 0:
        raise ValidationError("Amount must be greater than 0")
    if remaining <= 0:
        raise ValidationError("Fee already fully paid")
    if amount_decimal > remaining:
        raise ValidationError("Amount exceeds remaining fee")

    payload = {
        "student_id": student_id,
        "amount": amount_decimal,
        "payment_method": "razorpay",
        "reference_no": payment_id,
        "remarks": "Online payment via Razorpay",
    }
    return create_fee_payment(payload, receiver_user_id=receiver_user_id)
