from flask import current_app, request
from flask_jwt_extended import get_jwt, get_jwt_identity

from app.core.exceptions import AuthenticationError, ValidationError
from app.models import Student
from app.services.payment_service import (
    create_razorpay_order,
    record_successful_payment,
    verify_razorpay_signature,
)
from app.utils.response import api_response


def create_razorpay_order_controller():
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    payload = request.get_json(silent=True) or {}

    amount = payload.get("amount")
    student_id = payload.get("student_id")

    if amount is None or student_id is None:
        raise ValidationError("amount and student_id are required")

    try:
        amount = float(amount)
        student_id = int(student_id)
    except (TypeError, ValueError) as exc:
        raise ValidationError("Invalid amount or student_id") from exc

    if (claims.get("role") or "").lower() == "student":
        student = Student.query.filter_by(user_id=current_user_id, is_active=True).first()
        if not student or student.id != student_id:
            raise AuthenticationError("Students can only pay their own fees", 403)

    order = create_razorpay_order(student_id=student_id, amount_in_rupees=amount)
    return api_response(
        True,
        "Order created",
        {
            "order": order,
            "key_id": current_app.config.get("RAZORPAY_KEY_ID"),
        },
        201,
    )


def verify_razorpay_payment_controller():
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    payload = request.get_json(silent=True) or {}

    order_id = payload.get("razorpay_order_id")
    payment_id = payload.get("razorpay_payment_id")
    signature = payload.get("razorpay_signature")
    student_id = payload.get("student_id")
    amount = payload.get("amount")

    if not (order_id and payment_id and signature and student_id and amount):
        raise ValidationError("Missing required fields")

    if not verify_razorpay_signature(order_id, payment_id, signature):
        raise ValidationError("Payment verification failed", 400)

    try:
        student_id = int(student_id)
        amount = float(amount)
    except (TypeError, ValueError) as exc:
        raise ValidationError("Invalid amount or student_id") from exc

    if (claims.get("role") or "").lower() == "student":
        student = Student.query.filter_by(user_id=current_user_id, is_active=True).first()
        if not student or student.id != student_id:
            raise AuthenticationError("Students can only pay their own fees", 403)

    payment = record_successful_payment(
        student_id=student_id,
        amount_in_rupees=amount,
        payment_id=payment_id,
        receiver_user_id=int(current_user_id),
    )

    return api_response(
        True,
        "Payment verified and recorded",
        {"fee_payment": payment.to_dict()},
        200,
    )
