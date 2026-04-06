from datetime import date, datetime

from flask import request
from flask_jwt_extended import get_jwt_identity

from app.core.exceptions import ValidationError
from app.services.salary_service import (
    create_salary_record,
    delete_salary_record,
    get_salary_summary,
    list_salary_records,
    update_salary_record,
)
from app.utils.response import api_response
from app.validators.salary_validators import validate_create_salary_payload, validate_update_salary_payload


def create_salary_controller():
    payload = request.get_json(silent=True) or {}
    validated = validate_create_salary_payload(payload)

    current_user_id = get_jwt_identity()
    try:
        paid_by_user_id = int(current_user_id)
    except (TypeError, ValueError):
        paid_by_user_id = None

    salary = create_salary_record(validated, paid_by_user_id=paid_by_user_id)
    return api_response(True, "Salary payment recorded successfully", {"salary": salary.to_dict()}, 201)


def list_salary_controller():
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=10, type=int)
    teacher_id = request.args.get("teacher_id", type=int)
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")
    last_n_payments = request.args.get("last_n", type=int)
    last_n_months = request.args.get("last_months", type=int)

    if page < 1 or per_page < 1 or per_page > 100:
        raise ValidationError("page must be >= 1 and per_page must be between 1 and 100")

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

    data = list_salary_records(
        page=page, 
        per_page=per_page, 
        teacher_id=teacher_id,
        start_date=start_date,
        end_date=end_date,
        last_n_payments=last_n_payments,
        last_n_months=last_n_months
    )
    return api_response(True, "Salary records fetched successfully", data, 200)


def update_salary_controller(salary_id):
    payload = request.get_json(silent=True) or {}
    validated = validate_update_salary_payload(payload)

    salary = update_salary_record(salary_id, validated)
    return api_response(True, "Salary record updated successfully", {"salary": salary.to_dict()}, 200)


def delete_salary_controller(salary_id):
    delete_salary_record(salary_id)
    return api_response(True, "Salary record deleted successfully", {}, 200)


def salary_summary_controller():
    teacher_id = request.args.get("teacher_id", type=int)
    summary = get_salary_summary(teacher_id=teacher_id)
    return api_response(True, "Salary summary generated", summary, 200)
