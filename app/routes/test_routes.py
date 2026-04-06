from flask import Blueprint
from flasgger import swag_from
from flask_jwt_extended import jwt_required

from app.controllers.test_controller import (
    create_test_controller,
    create_test_result_controller,
    list_test_results_controller,
    list_tests_controller,
    performance_metrics_controller,
)
from app.utils.auth import roles_required

tests_bp = Blueprint("tests", __name__)


@tests_bp.post("/tests")
@roles_required("coach", "director", "manager")
@swag_from({"tags": ["Tests"], "summary": "Create a batch test", "security": [{"BearerAuth": []}]})
def create_test_route():
    return create_test_controller()


@tests_bp.get("/tests")
@jwt_required()
@swag_from({"tags": ["Tests"], "summary": "List tests", "security": [{"BearerAuth": []}]})
def list_tests_route():
    return list_tests_controller()


@tests_bp.post("/test-results")
@roles_required("coach", "director", "manager")
@swag_from({"tags": ["Tests"], "summary": "Store student marks", "security": [{"BearerAuth": []}]})
def create_test_result_route():
    return create_test_result_controller()


@tests_bp.get("/test-results")
@jwt_required()
@swag_from({"tags": ["Tests"], "summary": "List test results", "security": [{"BearerAuth": []}]})
def list_test_results_route():
    return list_test_results_controller()


@tests_bp.get("/tests/performance-metrics")
@jwt_required()
@swag_from({"tags": ["Tests"], "summary": "Get performance metrics", "security": [{"BearerAuth": []}]})
def performance_metrics_route():
    return performance_metrics_controller()
