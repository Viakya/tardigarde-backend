from datetime import date

from flask import request
from flask_jwt_extended import get_jwt, get_jwt_identity

from app.core.exceptions import ValidationError
from app.services.attendance_service import (
    create_attendance,
    delete_attendance,
    get_attendance_by_id,
    list_attendance,
    update_attendance,
)
from app.utils.response import api_response
from app.validators.attendance_validators import (
    validate_create_attendance_payload,
    validate_update_attendance_payload,
)


def create_attendance_controller():
    payload = request.get_json(silent=True) or {}
    validated = validate_create_attendance_payload(payload)

    current_user_id = get_jwt_identity()
    try:
        marker_user_id = int(current_user_id)
    except (TypeError, ValueError) as exc:
        raise ValidationError("Invalid user identity") from exc

    attendance = create_attendance(validated, marker_user_id)
    return api_response(True, "Attendance marked successfully", {"attendance": attendance.to_dict()}, 201)


def list_attendance_controller():
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=10, type=int)

    if page < 1 or per_page < 1 or per_page > 1000:
        raise ValidationError("page must be >= 1 and per_page must be between 1 and 1000")

    student_id = request.args.get("student_id", type=int)
    batch_id = request.args.get("batch_id", type=int)

    attendance_date_raw = request.args.get("attendance_date")
    attendance_date = None
    if attendance_date_raw:
        try:
            attendance_date = date.fromisoformat(attendance_date_raw)
        except ValueError as exc:
            raise ValidationError("attendance_date must be in YYYY-MM-DD format") from exc

    current_user_id = get_jwt_identity()
    current_role = (get_jwt().get("role") or "").lower()

    data = list_attendance(
        page=page,
        per_page=per_page,
        student_id=student_id,
        batch_id=batch_id,
        attendance_date=attendance_date,
        current_user_id=current_user_id,
        current_role=current_role,
    )

    return api_response(True, "Attendance fetched successfully", data, 200)


def get_attendance_controller(attendance_id):
    current_user_id = get_jwt_identity()
    current_role = (get_jwt().get("role") or "").lower()
    attendance = get_attendance_by_id(attendance_id, current_user_id=current_user_id, current_role=current_role)
    return api_response(True, "Attendance fetched successfully", {"attendance": attendance.to_dict()}, 200)


def update_attendance_controller(attendance_id):
    payload = request.get_json(silent=True) or {}
    validated = validate_update_attendance_payload(payload)

    current_user_id = get_jwt_identity()
    try:
        marker_user_id = int(current_user_id)
    except (TypeError, ValueError) as exc:
        raise ValidationError("Invalid user identity") from exc

    attendance = update_attendance(attendance_id, validated, marker_user_id)
    return api_response(True, "Attendance updated successfully", {"attendance": attendance.to_dict()}, 200)


def delete_attendance_controller(attendance_id):
    delete_attendance(attendance_id)
    return api_response(True, "Attendance deleted successfully", {}, 200)
