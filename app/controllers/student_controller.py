import csv
import io

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
    create_students_bulk,
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


def create_students_bulk_controller():
    file = request.files.get("file")
    if not file:
        raise ValidationError("CSV file is required in 'file' field")

    filename = (file.filename or "").lower()
    if not filename.endswith(".csv"):
        raise ValidationError("Only .csv files are supported")

    try:
        raw = file.read().decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValidationError("CSV must be UTF-8 encoded") from exc

    reader = csv.DictReader(io.StringIO(raw))
    if not reader.fieldnames:
        raise ValidationError("CSV header is missing")

    required_headers = {"user_id"}
    incoming_headers = {str(h or "").strip() for h in reader.fieldnames}
    missing = required_headers.difference(incoming_headers)
    if missing:
        raise ValidationError(f"CSV missing required headers: {', '.join(sorted(missing))}")

    rows_to_create = []
    failed_rows = []

    for index, row in enumerate(reader, start=2):
        normalized = {
            "user_id": (row.get("user_id") or "").strip(),
            "batch_id": (row.get("batch_id") or "").strip() or None,
            "phone_number": (row.get("phone_number") or "").strip() or None,
            "address": (row.get("address") or "").strip() or None,
            "date_of_birth": (row.get("date_of_birth") or "").strip() or None,
            "enrollment_date": (row.get("enrollment_date") or "").strip() or None,
            "discount_percent": (row.get("discount_percent") or "").strip() or None,
            "is_active": (row.get("is_active") or "").strip() or "true",
        }

        is_active_raw = str(normalized["is_active"]).strip().lower()
        if is_active_raw in {"true", "1", "yes", "y"}:
            normalized["is_active"] = True
        elif is_active_raw in {"false", "0", "no", "n"}:
            normalized["is_active"] = False

        parent_user_ids_raw = (row.get("parent_user_ids") or "").strip()
        if parent_user_ids_raw:
            normalized["parent_user_ids"] = [part.strip() for part in parent_user_ids_raw.replace(";", ",").split(",") if part.strip()]

        try:
            validated = validate_create_student_payload(normalized)
            rows_to_create.append({"line": index, "payload": validated})
        except ValidationError as exc:
            failed_rows.append(
                {
                    "line": index,
                    "user_id": normalized.get("user_id"),
                    "message": exc.message,
                }
            )

    if not rows_to_create and not failed_rows:
        raise ValidationError("CSV has no data rows")

    result = create_students_bulk(rows_to_create) if rows_to_create else {
        "summary": {"total": 0, "created": 0, "failed": 0},
        "created": [],
        "failed": [],
    }
    if failed_rows:
        result["failed"].extend(failed_rows)
        result["summary"]["failed"] = len(result["failed"])
        result["summary"]["total"] = result["summary"]["created"] + result["summary"]["failed"]

    status_code = 201 if (result["summary"].get("failed", 0) == 0) else 207
    return api_response(True, "Bulk student registration completed", result, status_code)
