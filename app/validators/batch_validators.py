from datetime import date
from decimal import Decimal, InvalidOperation

from app.core.exceptions import ValidationError


ALLOWED_UPDATE_FIELDS = {"batch_name", "year", "start_date", "end_date", "is_active", "batch_cost"}


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


def _normalize_batch_name(value):
    normalized = (value or "").strip()
    if not normalized:
        raise ValidationError("batch_name is required")
    if len(normalized) > 120:
        raise ValidationError("batch_name cannot exceed 120 characters")
    return normalized


def _normalize_year(value):
    if value is None:
        raise ValidationError("year is required")

    try:
        year = int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError("year must be an integer") from exc

    if year < 2000 or year > 2100:
        raise ValidationError("year must be between 2000 and 2100")

    return year


def _validate_date_window(start_date, end_date):
    if start_date and end_date and end_date < start_date:
        raise ValidationError("end_date cannot be earlier than start_date")


def _normalize_batch_cost(value):
    """Validate and normalize batch_cost to a Decimal."""
    if value is None:
        raise ValidationError("batch_cost is required")
    
    try:
        cost = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValidationError("batch_cost must be a valid number") from exc
    
    if cost < 0:
        raise ValidationError("batch_cost cannot be negative")
    
    if cost > 9999999.99:
        raise ValidationError("batch_cost is too large")
    
    return cost


def validate_create_batch_payload(payload):
    if not isinstance(payload, dict):
        raise ValidationError("Invalid request payload")

    batch_name = _normalize_batch_name(payload.get("batch_name"))
    year = _normalize_year(payload.get("year"))
    batch_cost = _normalize_batch_cost(payload.get("batch_cost"))
    start_date = _parse_iso_date(payload.get("start_date"), "start_date")
    end_date = _parse_iso_date(payload.get("end_date"), "end_date")
    _validate_date_window(start_date, end_date)

    is_active = payload.get("is_active", True)
    if not isinstance(is_active, bool):
        raise ValidationError("is_active must be a boolean")

    return {
        "batch_name": batch_name,
        "year": year,
        "batch_cost": batch_cost,
        "start_date": start_date,
        "end_date": end_date,
        "is_active": is_active,
    }


def validate_update_batch_payload(payload):
    if not isinstance(payload, dict):
        raise ValidationError("Invalid request payload")

    incoming_keys = set(payload.keys())
    invalid_keys = incoming_keys.difference(ALLOWED_UPDATE_FIELDS)
    if invalid_keys:
        raise ValidationError(f"Unsupported fields: {', '.join(sorted(invalid_keys))}")

    if not incoming_keys:
        raise ValidationError("At least one field is required for update")

    normalized_data = {}

    if "batch_name" in payload:
        normalized_data["batch_name"] = _normalize_batch_name(payload.get("batch_name"))

    if "year" in payload:
        normalized_data["year"] = _normalize_year(payload.get("year"))

    if "start_date" in payload:
        normalized_data["start_date"] = _parse_iso_date(payload.get("start_date"), "start_date")

    if "end_date" in payload:
        normalized_data["end_date"] = _parse_iso_date(payload.get("end_date"), "end_date")

    if "start_date" in normalized_data or "end_date" in normalized_data:
        _validate_date_window(
            normalized_data.get("start_date"),
            normalized_data.get("end_date"),
        )

    if "is_active" in payload:
        is_active = payload.get("is_active")
        if not isinstance(is_active, bool):
            raise ValidationError("is_active must be a boolean")
        normalized_data["is_active"] = is_active

    if "batch_cost" in payload:
        normalized_data["batch_cost"] = _normalize_batch_cost(payload.get("batch_cost"))

    return normalized_data
