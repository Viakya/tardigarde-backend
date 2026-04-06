from flask import request
from flask_jwt_extended import get_jwt_identity

from app.core.exceptions import ValidationError
from app.services.student_service import (
    create_student,
    delete_student,
    get_student_by_id,
    get_student_by_user_id,
    list_students,
    update_student,
    connect_parent,
    disconnect_parent,
)
from app.utils.response import api_response
from app.validators.student_validators import (
    validate_create_student_payload,
    validate_update_student_payload,
)


def create_student_controller():
    payload = request.get_json(silent=True) or {}
    validated = validate_create_student_payload(payload)

    student = create_student(validated)
    return api_response(True, "Student created successfully", {"student": student.to_dict()}, 201)


def list_students_controller():
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=10, type=int)

    if page < 1 or per_page < 1 or per_page > 100:
        raise ValidationError("page must be >= 1 and per_page must be between 1 and 100")

    data = list_students(page=page, per_page=per_page)
    return api_response(True, "Students fetched successfully", data, 200)


def get_student_controller(student_id):
    student = get_student_by_id(student_id)
    return api_response(True, "Student fetched successfully", {"student": student.to_dict()}, 200)


def update_student_controller(student_id):
    payload = request.get_json(silent=True) or {}
    validated = validate_update_student_payload(payload)

    student = update_student(student_id, validated)
    return api_response(True, "Student updated successfully", {"student": student.to_dict()}, 200)


def delete_student_controller(student_id):
    delete_student(student_id)
    return api_response(True, "Student deleted successfully", {}, 200)


def get_my_student_profile_controller():
    current_user_id = get_jwt_identity()
    try:
        user_id = int(current_user_id)
    except (TypeError, ValueError) as exc:
        raise ValidationError("Invalid user identity") from exc

    student = get_student_by_user_id(user_id)
    return api_response(True, "Student profile fetched", {"student": student.to_dict()}, 200)


def connect_parent_controller(student_id):
    payload = request.get_json(silent=True) or {}
    parent_user_id = payload.get("parent_user_id")
    if not parent_user_id:
        raise ValidationError("parent_user_id is required")

    student = connect_parent(student_id, parent_user_id)
    return api_response(True, "Parent connected successfully", {"student": student.to_dict()}, 200)


def disconnect_parent_controller(student_id, parent_user_id):
    student = disconnect_parent(student_id, parent_user_id)
    return api_response(True, "Parent disconnected successfully", {"student": student.to_dict()}, 200)
