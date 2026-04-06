from flask import request
from flask_jwt_extended import get_jwt, get_jwt_identity

from app.core.exceptions import ValidationError
from app.services.batch_resource_service import (
    create_batch_resource,
    delete_batch_resource,
    list_batch_resources,
    update_batch_resource,
)
from app.utils.response import api_response
from app.validators.batch_resource_validators import (
    validate_create_batch_resource_payload,
    validate_update_batch_resource_payload,
)


def list_batch_resources_controller(batch_id):
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    include_hidden = request.args.get("include_hidden", "false").lower() in {"1", "true", "yes"}

    try:
        current_user_id = int(current_user_id)
    except (TypeError, ValueError) as exc:
        raise ValidationError("Invalid user identity") from exc

    data = list_batch_resources(
        batch_id=batch_id,
        current_user_id=current_user_id,
        role=claims.get("role"),
        include_hidden=include_hidden,
    )
    return api_response(True, "Batch resources fetched successfully", data, 200)


def create_batch_resource_controller(batch_id):
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    payload = request.get_json(silent=True) or {}
    validated = validate_create_batch_resource_payload(payload)

    try:
        current_user_id = int(current_user_id)
    except (TypeError, ValueError) as exc:
        raise ValidationError("Invalid user identity") from exc

    resource = create_batch_resource(
        batch_id=batch_id,
        data=validated,
        current_user_id=current_user_id,
        role=claims.get("role"),
    )
    return api_response(True, "Batch resource created successfully", {"resource": resource.to_dict()}, 201)


def update_batch_resource_controller(resource_id):
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    payload = request.get_json(silent=True) or {}
    validated = validate_update_batch_resource_payload(payload)

    try:
        current_user_id = int(current_user_id)
    except (TypeError, ValueError) as exc:
        raise ValidationError("Invalid user identity") from exc

    resource = update_batch_resource(
        resource_id=resource_id,
        data=validated,
        current_user_id=current_user_id,
        role=claims.get("role"),
    )
    return api_response(True, "Batch resource updated successfully", {"resource": resource.to_dict()}, 200)


def delete_batch_resource_controller(resource_id):
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    try:
        current_user_id = int(current_user_id)
    except (TypeError, ValueError) as exc:
        raise ValidationError("Invalid user identity") from exc
    delete_batch_resource(resource_id=resource_id, current_user_id=current_user_id, role=claims.get("role"))
    return api_response(True, "Batch resource deleted successfully", {}, 200)
