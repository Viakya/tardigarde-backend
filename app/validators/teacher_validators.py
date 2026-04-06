from datetime import date

from app.core.exceptions import ValidationError


ALLOWED_UPDATE_FIELDS = {"specialization", "phone_number", "hire_date", "is_active"}


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


def _normalize_phone(value):
    if value is None:
        return None

    normalized = str(value).strip()
    if len(normalized) > 20:
        raise ValidationError("phone_number cannot exceed 20 characters")

    return normalized or None


def _normalize_specialization(value):
    if value is None:
        return None

    normalized = str(value).strip()
    if len(normalized) > 120:
        raise ValidationError("specialization cannot exceed 120 characters")

    return normalized or None


def _normalize_user_id(value):
    if value is None:
        raise ValidationError("user_id is required")

    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError("user_id must be an integer") from exc


def validate_create_teacher_payload(payload):
    if not isinstance(payload, dict):
        raise ValidationError("Invalid request payload")

    is_active = payload.get("is_active", True)
    if not isinstance(is_active, bool):
        raise ValidationError("is_active must be a boolean")

    return {
        "user_id": _normalize_user_id(payload.get("user_id")),
        "specialization": _normalize_specialization(payload.get("specialization")),
        "phone_number": _normalize_phone(payload.get("phone_number")),
        "hire_date": _parse_iso_date(payload.get("hire_date"), "hire_date"),
        "is_active": is_active,
    }


def validate_update_teacher_payload(payload):
    if not isinstance(payload, dict):
        raise ValidationError("Invalid request payload")

    incoming_keys = set(payload.keys())
    invalid_keys = incoming_keys.difference(ALLOWED_UPDATE_FIELDS)
    if invalid_keys:
        raise ValidationError(f"Unsupported fields: {', '.join(sorted(invalid_keys))}")

    if not incoming_keys:
        raise ValidationError("At least one field is required for update")

    normalized_data = {}

    if "specialization" in payload:
        normalized_data["specialization"] = _normalize_specialization(payload.get("specialization"))

    if "phone_number" in payload:
        normalized_data["phone_number"] = _normalize_phone(payload.get("phone_number"))

    if "hire_date" in payload:
        normalized_data["hire_date"] = _parse_iso_date(payload.get("hire_date"), "hire_date")

    if "is_active" in payload:
        is_active = payload.get("is_active")
        if not isinstance(is_active, bool):
            raise ValidationError("is_active must be a boolean")
        normalized_data["is_active"] = is_active

    return normalized_data
