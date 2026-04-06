from datetime import date
from decimal import Decimal, InvalidOperation

from app.core.exceptions import ValidationError


def _parse_date(value, field_name):
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


def _to_decimal(value, field_name, required=True):
    if value in (None, ""):
        if required:
            raise ValidationError(f"{field_name} is required")
        return None

    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValidationError(f"{field_name} must be a valid number") from exc

    if amount <= Decimal("0"):
        raise ValidationError(f"{field_name} must be greater than 0")

    return amount


def _required_int(value, field_name):
    if value in (None, ""):
        raise ValidationError(f"{field_name} is required")

    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field_name} must be an integer") from exc


def validate_create_salary_payload(payload):
    if not isinstance(payload, dict):
        raise ValidationError("Invalid request payload")

    payment_method = payload.get("payment_method", "cash")
    if not isinstance(payment_method, str) or not payment_method.strip():
        raise ValidationError("payment_method must be a non-empty string")

    reference_no = payload.get("reference_no")
    if reference_no is not None and not isinstance(reference_no, str):
        raise ValidationError("reference_no must be a string")

    remarks = payload.get("remarks")
    if remarks is not None and not isinstance(remarks, str):
        raise ValidationError("remarks must be a string")

    return {
        "teacher_id": _required_int(payload.get("teacher_id"), "teacher_id"),
        "amount": _to_decimal(payload.get("amount"), "amount"),
        "payment_date": _parse_date(payload.get("payment_date"), "payment_date"),
        "payment_method": payment_method.strip(),
        "reference_no": reference_no,
        "remarks": remarks,
    }


def validate_update_salary_payload(payload):
    if not isinstance(payload, dict):
        raise ValidationError("Invalid request payload")

    if not payload:
        raise ValidationError("At least one field is required for update")

    result = {}

    if "amount" in payload:
        result["amount"] = _to_decimal(payload["amount"], "amount")

    if "payment_date" in payload:
        result["payment_date"] = _parse_date(payload["payment_date"], "payment_date")

    if "payment_method" in payload:
        payment_method = payload["payment_method"]
        if not isinstance(payment_method, str) or not payment_method.strip():
            raise ValidationError("payment_method must be a non-empty string")
        result["payment_method"] = payment_method.strip()

    if "reference_no" in payload:
        reference_no = payload["reference_no"]
        if reference_no is not None and not isinstance(reference_no, str):
            raise ValidationError("reference_no must be a string")
        result["reference_no"] = reference_no

    if "remarks" in payload:
        remarks = payload["remarks"]
        if remarks is not None and not isinstance(remarks, str):
            raise ValidationError("remarks must be a string")
        result["remarks"] = remarks

    if not result:
        raise ValidationError("At least one valid field is required for update")

    return result
