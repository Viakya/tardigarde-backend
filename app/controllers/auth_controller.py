import csv
import io

from flask import current_app, request

from app.core.exceptions import ValidationError
from app.services.auth_service import (
    authenticate_google_user,
    authenticate_user,
    create_user,
    delete_user,
    get_registered_users,
    get_user_by_id,
    get_users_and_admins_summary,
    update_user,
)
from app.services.token_service import generate_access_token
from app.utils.google_auth import verify_google_token
from app.utils.response import api_response
from app.validators.auth_validators import (
    validate_bulk_registration_row,
    validate_google_login_payload,
    validate_login_payload,
    validate_registration_payload,
)


def register_user():
    payload = request.get_json(silent=True) or {}
    validated = validate_registration_payload(payload)

    user = create_user(
        email=validated["email"],
        full_name=validated["full_name"],
        password=validated["password"],
        role=validated["role"],
    )
    access_token = generate_access_token(user)

    return api_response(
        True,
        "User registered successfully",
        {
            "user": user.to_dict(),
            "access_token": access_token,
        },
        201,
    )


def login_user():
    payload = request.get_json(silent=True) or {}
    validated = validate_login_payload(payload)

    user = authenticate_user(email=validated["email"], password=validated["password"])
    access_token = generate_access_token(user)

    return api_response(
        True,
        "Login successful",
        {
            "user": user.to_dict(),
            "access_token": access_token,
        },
        200,
    )


def google_login_user():
    payload = request.get_json(silent=True) or {}
    validated = validate_google_login_payload(payload)

    client_id = current_app.config.get("GOOGLE_CLIENT_ID")
    id_info = verify_google_token(validated["credential"], client_id)
    email = (id_info.get("email") or "").strip().lower()

    user = authenticate_google_user(email=email)
    access_token = generate_access_token(user)

    return api_response(
        True,
        "Google login successful",
        {
            "user": user.to_dict(),
            "access_token": access_token,
        },
        200,
    )


def get_me(current_user_id):
    try:
        user_id = int(current_user_id)
    except (TypeError, ValueError):
        return api_response(False, "Invalid user identity", {}, 401)

    user = get_user_by_id(user_id)
    if not user:
        return api_response(False, "User not found", {}, 404)

    return api_response(True, "Current user fetched", {"user": user.to_dict()}, 200)


def protected_example(current_user_id):
    try:
        user_id = int(current_user_id)
    except (TypeError, ValueError) as exc:
        raise ValidationError("Invalid user identity") from exc

    user = get_user_by_id(user_id)
    if not user:
        return api_response(False, "User not found", {}, 404)

    return api_response(
        True,
        "Protected route accessed",
        {
            "user_id": user.id,
            "email": user.email,
            "role": user.role,
        },
        200,
    )


def admin_only_example():
    return api_response(True, "Admin route accessed", {"scope": "admin"}, 200)


def users_summary():
    summary = get_users_and_admins_summary()
    return api_response(True, "User registration summary fetched", summary, 200)


def registered_users():
    users = get_registered_users()
    return api_response(True, "Registered users fetched", {"users": users}, 200)


def update_user_controller(user_id):
    payload = request.get_json(silent=True) or {}
    
    # Validate that at least one field is being updated
    allowed_fields = {"full_name", "role", "is_active", "password"}
    update_fields = {k: v for k, v in payload.items() if k in allowed_fields}
    
    if not update_fields:
        raise ValidationError("No valid fields to update")
    
    user = update_user(user_id, update_fields)
    return api_response(True, "User updated successfully", {"user": user.to_dict()}, 200)


def delete_user_controller(user_id):
    user = delete_user(user_id)
    return api_response(True, "User deleted successfully", {"user": user.to_dict()}, 200)


def register_users_bulk():
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

    required_headers = {"email", "full_name", "password", "role"}
    incoming_headers = {str(h or "").strip() for h in reader.fieldnames}
    missing = required_headers.difference(incoming_headers)
    if missing:
        raise ValidationError(f"CSV missing required headers: {', '.join(sorted(missing))}")

    created = []
    failed = []

    for index, row in enumerate(reader, start=2):
        payload = {
            "email": (row.get("email") or "").strip(),
            "full_name": (row.get("full_name") or "").strip(),
            "password": (row.get("password") or "").strip(),
            "role": (row.get("role") or "").strip(),
        }

        try:
            validated = validate_bulk_registration_row(payload)
            user = create_user(
                email=validated["email"],
                full_name=validated["full_name"],
                password=validated["password"],
                role=validated["role"],
            )
            created.append(
                {
                    "line": index,
                    "user": user.to_dict(),
                }
            )
        except Exception as exc:  # noqa: BLE001
            message = getattr(exc, "message", str(exc)) or "Failed to create user"
            failed.append(
                {
                    "line": index,
                    "email": payload["email"],
                    "message": message,
                }
            )

    if not created and not failed:
        raise ValidationError("CSV has no data rows")

    status_code = 201 if not failed else 207
    message = "Bulk user registration completed"
    return api_response(
        True,
        message,
        {
            "summary": {
                "total": len(created) + len(failed),
                "created": len(created),
                "failed": len(failed),
            },
            "created": created,
            "failed": failed,
        },
        status_code,
    )
