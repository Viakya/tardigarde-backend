from flask import request
from flask_jwt_extended import get_jwt, get_jwt_identity

from app.core.exceptions import ValidationError
from app.services.test_service import (
    create_test,
    create_test_result,
    get_performance_metrics,
    list_test_results,
    list_tests,
)
from app.utils.response import api_response
from app.validators.test_validators import validate_create_test_payload, validate_create_test_result_payload


def create_test_controller():
    payload = request.get_json(silent=True) or {}
    validated = validate_create_test_payload(payload)

    current_user_id = get_jwt_identity()
    try:
        creator_user_id = int(current_user_id)
    except (TypeError, ValueError) as exc:
        raise ValidationError("Invalid user identity") from exc

    test = create_test(validated, creator_user_id)
    return api_response(True, "Test created successfully", {"test": test.to_dict()}, 201)


def list_tests_controller():
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=10, type=int)
    batch_id = request.args.get("batch_id", type=int)

    if page < 1 or per_page < 1 or per_page > 1000:
        raise ValidationError("page must be >= 1 and per_page must be between 1 and 1000")

    current_user_id = get_jwt_identity()
    current_role = (get_jwt().get("role") or "").lower()

    data = list_tests(
        page=page,
        per_page=per_page,
        batch_id=batch_id,
        current_user_id=current_user_id,
        current_role=current_role,
    )
    return api_response(True, "Tests fetched successfully", data, 200)


def create_test_result_controller():
    payload = request.get_json(silent=True) or {}
    validated = validate_create_test_result_payload(payload)

    result = create_test_result(validated)
    return api_response(True, "Test result created successfully", {"test_result": result.to_dict()}, 201)


def list_test_results_controller():
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=10, type=int)
    test_id = request.args.get("test_id", type=int)
    student_id = request.args.get("student_id", type=int)

    if page < 1 or per_page < 1 or per_page > 1000:
        raise ValidationError("page must be >= 1 and per_page must be between 1 and 1000")

    current_user_id = get_jwt_identity()
    current_role = (get_jwt().get("role") or "").lower()

    data = list_test_results(
        page=page,
        per_page=per_page,
        test_id=test_id,
        student_id=student_id,
        current_user_id=current_user_id,
        current_role=current_role,
    )
    return api_response(True, "Test results fetched successfully", data, 200)


def performance_metrics_controller():
    batch_id = request.args.get("batch_id", type=int)
    current_user_id = get_jwt_identity()
    current_role = (get_jwt().get("role") or "").lower()
    metrics = get_performance_metrics(batch_id=batch_id, current_user_id=current_user_id, current_role=current_role)
    return api_response(True, "Performance metrics generated", metrics, 200)
