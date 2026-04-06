from datetime import date
from decimal import Decimal, InvalidOperation

from app.core.exceptions import ValidationError


def _required_int(value, field_name):
    if value in (None, ""):
        raise ValidationError(f"{field_name} is required")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field_name} must be an integer") from exc


def _to_decimal(value, field_name):
    if value in (None, ""):
        raise ValidationError(f"{field_name} is required")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValidationError(f"{field_name} must be a valid number") from exc

    if number < Decimal("0"):
        raise ValidationError(f"{field_name} cannot be negative")

    return number


def _parse_date(value, field_name):
    if value in (None, ""):
        raise ValidationError(f"{field_name} is required")

    if isinstance(value, date):
        return value

    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be in YYYY-MM-DD format")

    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValidationError(f"{field_name} must be in YYYY-MM-DD format") from exc


def validate_create_test_payload(payload):
    if not isinstance(payload, dict):
        raise ValidationError("Invalid request payload")

    title = (payload.get("title") or "").strip()
    if not title:
        raise ValidationError("title is required")

    return {
        "batch_id": _required_int(payload.get("batch_id"), "batch_id"),
        "title": title,
        "subject": (payload.get("subject") or "").strip() or None,
        "max_marks": _to_decimal(payload.get("max_marks"), "max_marks"),
        "test_date": _parse_date(payload.get("test_date"), "test_date"),
    }


def validate_create_test_result_payload(payload):
    if not isinstance(payload, dict):
        raise ValidationError("Invalid request payload")

    return {
        "test_id": _required_int(payload.get("test_id"), "test_id"),
        "student_id": _required_int(payload.get("student_id"), "student_id"),
        "marks_obtained": _to_decimal(payload.get("marks_obtained"), "marks_obtained"),
        "remarks": (payload.get("remarks") or "").strip() or None,
    }
