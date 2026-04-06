from datetime import date
from decimal import Decimal, InvalidOperation

from app.core.exceptions import ValidationError


ALLOWED_UPDATE_FIELDS = {
    "batch_id",
    "phone_number",
    "address",
    "date_of_birth",
    "enrollment_date",
    "discount_percent",
    "is_active",
    "parent_user_ids",
}


def _normalize_optional_int(value, field_name):
    if value in (None, ""):
        return None

    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field_name} must be an integer") from exc


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


def _normalize_address(value):
    if value is None:
        return None

    normalized = str(value).strip()
    if len(normalized) > 500:
        raise ValidationError("address cannot exceed 500 characters")

    return normalized or None


def _normalize_parent_user_ids(value):
    if value in (None, ""):
        return None

    if not isinstance(value, list):
        raise ValidationError("parent_user_ids must be a list of integers")

    normalized = []
    for raw_parent_id in value:
        try:
            parent_id = int(raw_parent_id)
        except (TypeError, ValueError) as exc:
            raise ValidationError("parent_user_ids must contain only integers") from exc

        normalized.append(parent_id)

    return list(dict.fromkeys(normalized))


def _normalize_discount_percent(value):
    """Validate and normalize discount_percent to a Decimal."""
    if value in (None, ""):
        return Decimal("0")
    
    try:
        discount = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValidationError("discount_percent must be a valid number") from exc
    
    if discount < 0:
        raise ValidationError("discount_percent cannot be negative")
    
    if discount > 100:
        raise ValidationError("discount_percent cannot exceed 100")
    
    return discount


def validate_create_student_payload(payload):
    if not isinstance(payload, dict):
        raise ValidationError("Invalid request payload")

    user_id = payload.get("user_id")
    if user_id is None:
        raise ValidationError("user_id is required")

    try:
        user_id = int(user_id)
    except (TypeError, ValueError) as exc:
        raise ValidationError("user_id must be an integer") from exc

    is_active = payload.get("is_active", True)
    if not isinstance(is_active, bool):
        raise ValidationError("is_active must be a boolean")

    return {
        "user_id": user_id,
        "batch_id": _normalize_optional_int(payload.get("batch_id"), "batch_id"),
        "phone_number": _normalize_phone(payload.get("phone_number")),
        "address": _normalize_address(payload.get("address")),
        "date_of_birth": _parse_iso_date(payload.get("date_of_birth"), "date_of_birth"),
        "enrollment_date": _parse_iso_date(payload.get("enrollment_date"), "enrollment_date"),
        "discount_percent": _normalize_discount_percent(payload.get("discount_percent")),
        "is_active": is_active,
        "parent_user_ids": _normalize_parent_user_ids(payload.get("parent_user_ids")),
    }


def validate_update_student_payload(payload):
    if not isinstance(payload, dict):
        raise ValidationError("Invalid request payload")

    incoming_keys = set(payload.keys())
    invalid_keys = incoming_keys.difference(ALLOWED_UPDATE_FIELDS)
    if invalid_keys:
        raise ValidationError(f"Unsupported fields: {', '.join(sorted(invalid_keys))}")

    if not incoming_keys:
        raise ValidationError("At least one field is required for update")

    normalized_data = {}

    if "batch_id" in payload:
        normalized_data["batch_id"] = _normalize_optional_int(payload.get("batch_id"), "batch_id")

    if "phone_number" in payload:
        normalized_data["phone_number"] = _normalize_phone(payload.get("phone_number"))

    if "address" in payload:
        normalized_data["address"] = _normalize_address(payload.get("address"))

    if "date_of_birth" in payload:
        normalized_data["date_of_birth"] = _parse_iso_date(payload.get("date_of_birth"), "date_of_birth")

    if "enrollment_date" in payload:
        normalized_data["enrollment_date"] = _parse_iso_date(payload.get("enrollment_date"), "enrollment_date")

    if "discount_percent" in payload:
        normalized_data["discount_percent"] = _normalize_discount_percent(payload.get("discount_percent"))

    if "is_active" in payload:
        is_active = payload.get("is_active")
        if not isinstance(is_active, bool):
            raise ValidationError("is_active must be a boolean")
        normalized_data["is_active"] = is_active

    if "parent_user_ids" in payload:
        normalized_data["parent_user_ids"] = _normalize_parent_user_ids(payload.get("parent_user_ids"))

    return normalized_data
