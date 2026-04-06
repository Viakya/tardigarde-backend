from datetime import date
from decimal import Decimal, InvalidOperation

from app.core.exceptions import ValidationError


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


def _normalize_amount(value):
    """Validate and normalize amount to a Decimal."""
    if value is None:
        raise ValidationError("amount is required")
    
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValidationError("amount must be a valid number") from exc
    
    if amount <= 0:
        raise ValidationError("amount must be greater than 0")
    
    if amount > 99999999.99:
        raise ValidationError("amount is too large")
    
    return amount


def validate_create_fee_payment_payload(payload):
    if not isinstance(payload, dict):
        raise ValidationError("Invalid request payload")

    student_id = payload.get("student_id")
    if student_id is None:
        raise ValidationError("student_id is required")
    
    try:
        student_id = int(student_id)
    except (TypeError, ValueError) as exc:
        raise ValidationError("student_id must be an integer") from exc

    amount = _normalize_amount(payload.get("amount"))
    payment_date = _parse_iso_date(payload.get("payment_date"), "payment_date")
    
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
        "student_id": student_id,
        "amount": amount,
        "payment_date": payment_date,
        "payment_method": payment_method.strip(),
        "reference_no": reference_no,
        "remarks": remarks,
    }


def validate_update_fee_payment_payload(payload):
    if not isinstance(payload, dict):
        raise ValidationError("Invalid request payload")

    result = {}

    if "amount" in payload:
        result["amount"] = _normalize_amount(payload["amount"])

    if "payment_date" in payload:
        result["payment_date"] = _parse_iso_date(payload["payment_date"], "payment_date")

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
        raise ValidationError("At least one field is required for update")

    return result
