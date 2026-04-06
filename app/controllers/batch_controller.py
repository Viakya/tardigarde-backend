from flask import request

from app.core.exceptions import ValidationError
from app.services.batch_service import (
    create_batch,
    delete_batch,
    get_batch_by_id,
    get_batch_profile,
    list_batches,
    update_batch,
)
from app.utils.response import api_response
from app.validators.batch_validators import (
    validate_create_batch_payload,
    validate_update_batch_payload,
)


def create_batch_controller():
    payload = request.get_json(silent=True) or {}
    validated = validate_create_batch_payload(payload)

    batch = create_batch(validated)
    return api_response(True, "Batch created successfully", {"batch": batch.to_dict()}, 201)


def list_batches_controller():
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=10, type=int)

    if page < 1 or per_page < 1 or per_page > 100:
        raise ValidationError("page must be >= 1 and per_page must be between 1 and 100")

    data = list_batches(page=page, per_page=per_page)
    return api_response(True, "Batches fetched successfully", data, 200)


def get_batch_controller(batch_id):
    batch = get_batch_by_id(batch_id)
    return api_response(True, "Batch fetched successfully", {"batch": batch.to_dict()}, 200)


def update_batch_controller(batch_id):
    payload = request.get_json(silent=True) or {}
    validated = validate_update_batch_payload(payload)

    batch = update_batch(batch_id, validated)
    return api_response(True, "Batch updated successfully", {"batch": batch.to_dict()}, 200)


def delete_batch_controller(batch_id):
    delete_batch(batch_id)
    return api_response(True, "Batch deleted successfully", {}, 200)


def get_batch_profile_controller(batch_id):
    """Get detailed batch profile with financial summary."""
    data = get_batch_profile(batch_id)
    return api_response(True, "Batch profile fetched successfully", data, 200)
