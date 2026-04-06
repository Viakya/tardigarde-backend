from datetime import date

from app.core.exceptions import ValidationError


ATTENDANCE_STATUSES = {"present", "absent", "late"}
ALLOWED_UPDATE_FIELDS = {"status", "remarks", "is_active"}


def _parse_iso_date(value, field_name):
    if value in (None, ""):
        return None

    if isinstance(value, date):
        return value

    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a valid ISO date (YYYY-MM-DD)")

    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValidationError(f"{field_name} must be in YYYY-MM-DD format") from exc


def _normalize_required_int(value, field_name):
    if value in (None, ""):
        raise ValidationError(f"{field_name} is required")

    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field_name} must be an integer") from exc


def _normalize_status(value):
    normalized = (value or "").strip().lower()
    if normalized not in ATTENDANCE_STATUSES:
        raise ValidationError(f"status must be one of: {', '.join(sorted(ATTENDANCE_STATUSES))}")
    return normalized


def _normalize_remarks(value):
    if value is None:
        return None

    normalized = str(value).strip()
    if len(normalized) > 255:
        raise ValidationError("remarks cannot exceed 255 characters")

    return normalized or None


def validate_create_attendance_payload(payload):
    if not isinstance(payload, dict):
        raise ValidationError("Invalid request payload")

    is_active = payload.get("is_active", True)
    if not isinstance(is_active, bool):
        raise ValidationError("is_active must be a boolean")

    return {
        "student_id": _normalize_required_int(payload.get("student_id"), "student_id"),
        "batch_id": _normalize_required_int(payload.get("batch_id"), "batch_id"),
        "attendance_date": _parse_iso_date(payload.get("attendance_date"), "attendance_date") or date.today(),
        "status": _normalize_status(payload.get("status")),
        "remarks": _normalize_remarks(payload.get("remarks")),
        "is_active": is_active,
    }


def validate_update_attendance_payload(payload):
    if not isinstance(payload, dict):
        raise ValidationError("Invalid request payload")

    incoming_keys = set(payload.keys())
    invalid_keys = incoming_keys.difference(ALLOWED_UPDATE_FIELDS)
    if invalid_keys:
        raise ValidationError(f"Unsupported fields: {', '.join(sorted(invalid_keys))}")

    if not incoming_keys:
        raise ValidationError("At least one field is required for update")

    normalized = {}

    if "status" in payload:
        normalized["status"] = _normalize_status(payload.get("status"))

    if "remarks" in payload:
        normalized["remarks"] = _normalize_remarks(payload.get("remarks"))

    if "is_active" in payload:
        is_active = payload.get("is_active")
        if not isinstance(is_active, bool):
            raise ValidationError("is_active must be a boolean")
        normalized["is_active"] = is_active

    return normalized
