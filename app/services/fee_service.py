from datetime import date, datetime, timedelta
from decimal import Decimal

from app.core.exceptions import ValidationError
from app.extensions import db
from app.models import FeePayment, Student, User


def _get_active_student(student_id):
    student = Student.query.filter_by(id=student_id, is_active=True).first()
    if not student:
        raise ValidationError("Student not found", 404)
    return student


def _get_active_user(user_id):
    user = User.query.filter_by(id=user_id, is_active=True).first()
    if not user:
        raise ValidationError("User not found", 404)
    return user


def create_fee_payment(data, receiver_user_id):
    receiver = _get_active_user(receiver_user_id)
    student = _get_active_student(data["student_id"])

    if data["amount"] <= Decimal("0"):
        raise ValidationError("Amount must be greater than 0")

    payment = FeePayment(
        student_id=student.id,
        amount=data["amount"],
        payment_date=data.get("payment_date") or date.today(),
        payment_method=data.get("payment_method", "cash"),
        reference_no=data.get("reference_no"),
        received_by=receiver.id,
        remarks=data.get("remarks"),
    )

    db.session.add(payment)
    db.session.commit()
    return payment


def list_fee_payments(page=1, per_page=10, student_id=None, start_date=None, end_date=None, last_n_payments=None, last_n_months=None):
    query = FeePayment.query

    if student_id is not None:
        query = query.filter(FeePayment.student_id == student_id)
    
    # Filter by date range
    if start_date:
        query = query.filter(FeePayment.payment_date >= start_date)
    if end_date:
        query = query.filter(FeePayment.payment_date <= end_date)
    
    # Filter by last N months
    if last_n_months:
        months_ago = date.today() - timedelta(days=last_n_months * 30)
        query = query.filter(FeePayment.payment_date >= months_ago)
    
    # Order by date descending
    query = query.order_by(FeePayment.payment_date.desc(), FeePayment.id.desc())
    
    # If last_n_payments is set, limit without pagination
    if last_n_payments:
        payments = query.limit(last_n_payments).all()
        return {
            "fee_payments": [payment.to_dict() for payment in payments],
            "pagination": {
                "page": 1,
                "per_page": last_n_payments,
                "total": len(payments),
                "pages": 1,
                "has_next": False,
                "has_prev": False,
            },
        }

    pagination = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False,
    )

    return {
        "fee_payments": [payment.to_dict() for payment in pagination.items],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
        },
    }


def get_fee_payment_by_id(payment_id):
    payment = FeePayment.query.filter_by(id=payment_id).first()
    if not payment:
        raise ValidationError("Fee payment not found", 404)
    return payment


def delete_fee_payment(payment_id):
    payment = get_fee_payment_by_id(payment_id)
    db.session.delete(payment)
    db.session.commit()


def update_fee_payment(payment_id, data):
    payment = get_fee_payment_by_id(payment_id)

    if "amount" in data:
        if data["amount"] <= Decimal("0"):
            raise ValidationError("Amount must be greater than 0")
        payment.amount = data["amount"]

    if "payment_date" in data:
        payment.payment_date = data["payment_date"]

    if "payment_method" in data:
        payment.payment_method = data["payment_method"]

    if "reference_no" in data:
        payment.reference_no = data["reference_no"]

    if "remarks" in data:
        payment.remarks = data["remarks"]

    db.session.commit()
    return payment
