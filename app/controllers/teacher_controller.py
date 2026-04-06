from flask import request

from app.core.exceptions import ValidationError
from app.services.teacher_service import (
    create_teacher,
    delete_teacher,
    get_teacher_by_id,
    list_teachers,
    update_teacher,
)
from app.utils.response import api_response
from app.validators.teacher_validators import (
    validate_create_teacher_payload,
    validate_update_teacher_payload,
)


def create_teacher_controller():
    payload = request.get_json(silent=True) or {}
    validated = validate_create_teacher_payload(payload)

    teacher = create_teacher(validated)
    return api_response(True, "Teacher created successfully", {"teacher": teacher.to_dict()}, 201)


def list_teachers_controller():
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=10, type=int)

    if page < 1 or per_page < 1 or per_page > 100:
        raise ValidationError("page must be >= 1 and per_page must be between 1 and 100")

    data = list_teachers(page=page, per_page=per_page)
    return api_response(True, "Teachers fetched successfully", data, 200)


def get_teacher_controller(teacher_id):
    teacher = get_teacher_by_id(teacher_id)
    return api_response(True, "Teacher fetched successfully", {"teacher": teacher.to_dict()}, 200)


def update_teacher_controller(teacher_id):
    payload = request.get_json(silent=True) or {}
    validated = validate_update_teacher_payload(payload)

    teacher = update_teacher(teacher_id, validated)
    return api_response(True, "Teacher updated successfully", {"teacher": teacher.to_dict()}, 200)


def delete_teacher_controller(teacher_id):
    delete_teacher(teacher_id)
    return api_response(True, "Teacher deleted successfully", {}, 200)
