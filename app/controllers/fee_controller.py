from datetime import datetime

from flask import request

from app.core.exceptions import ValidationError
from app.services.fee_service import (
    create_fee_payment,
    delete_fee_payment,
    get_fee_payment_by_id,
    list_fee_payments,
    update_fee_payment,
)
from app.utils.response import api_response
from app.validators.fee_validators import validate_create_fee_payment_payload, validate_update_fee_payment_payload


def create_fee_payment_controller(current_user_id):
    payload = request.get_json(silent=True) or {}
    validated = validate_create_fee_payment_payload(payload)

    payment = create_fee_payment(validated, receiver_user_id=current_user_id)
    return api_response(True, "Fee payment created successfully", {"fee_payment": payment.to_dict()}, 201)


def list_fee_payments_controller():
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=10, type=int)
    student_id = request.args.get("student_id", type=int)
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")
    last_n_payments = request.args.get("last_n", type=int)
    last_n_months = request.args.get("last_months", type=int)

    if page < 1 or per_page < 1 or per_page > 1000:
        raise ValidationError("page must be >= 1 and per_page must be between 1 and 1000")

    # Parse dates
    start_date = None
    end_date = None
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        except ValueError:
            raise ValidationError("start_date must be in YYYY-MM-DD format")
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            raise ValidationError("end_date must be in YYYY-MM-DD format")

    data = list_fee_payments(
        page=page, 
        per_page=per_page, 
        student_id=student_id,
        start_date=start_date,
        end_date=end_date,
        last_n_payments=last_n_payments,
        last_n_months=last_n_months
    )
    return api_response(True, "Fee payments fetched successfully", data, 200)


def get_fee_payment_controller(payment_id):
    payment = get_fee_payment_by_id(payment_id)
    return api_response(True, "Fee payment fetched successfully", {"fee_payment": payment.to_dict()}, 200)


def delete_fee_payment_controller(payment_id):
    delete_fee_payment(payment_id)
    return api_response(True, "Fee payment deleted successfully", {}, 200)


def update_fee_payment_controller(payment_id):
    payload = request.get_json(silent=True) or {}
    validated = validate_update_fee_payment_payload(payload)

    payment = update_fee_payment(payment_id, validated)
    return api_response(True, "Fee payment updated successfully", {"fee_payment": payment.to_dict()}, 200)
