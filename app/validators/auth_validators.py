from app.constants.roles import USER_ROLES
from app.core.exceptions import ValidationError


def validate_registration_payload(payload):
    email = (payload.get("email") or "").strip().lower()
    full_name = (payload.get("full_name") or "").strip()
    password = (payload.get("password") or "").strip()
    role = (payload.get("role") or "student").strip().lower()

    if not email or not full_name or not password:
        raise ValidationError("email, full_name and password are required")

    if len(password) < 8:
        raise ValidationError("password must be at least 8 characters")

    if role not in USER_ROLES:
        raise ValidationError(f"role must be one of: {', '.join(sorted(USER_ROLES))}")

    return {
        "email": email,
        "full_name": full_name,
        "password": password,
        "role": role,
    }


def validate_login_payload(payload):
    email = (payload.get("email") or "").strip().lower()
    password = (payload.get("password") or "").strip()

    if not email or not password:
        raise ValidationError("email and password are required")

    return {
        "email": email,
        "password": password,
    }


def validate_google_login_payload(payload):
    credential = (payload.get("credential") or "").strip()

    if not credential:
        raise ValidationError("Google credential is required")

    return {
        "credential": credential,
    }


def validate_bulk_registration_row(payload):
    if not isinstance(payload, dict):
        raise ValidationError("Invalid row payload")

    # Reuse single-user validation so rules stay consistent.
    return validate_registration_payload(payload)
