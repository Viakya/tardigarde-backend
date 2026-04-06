"""
Parent Routes - API endpoints for parent-specific operations
"""
from flasgger import swag_from
from flask import Blueprint
from flask_jwt_extended import jwt_required

from app.controllers.parent_controller import (
    get_my_children_controller,
    get_child_details_controller,
    get_child_fees_controller,
    get_child_attendance_controller,
    get_child_test_results_controller,
    get_child_quiz_results_controller,
    get_child_quiz_detail_controller,
    get_parent_dashboard_controller,
)
from app.utils.auth import roles_required

parents_bp = Blueprint("parents", __name__)


@parents_bp.get("/parents/dashboard")
@jwt_required()
@roles_required("parent")
@swag_from({
    "tags": ["Parents"],
    "summary": "Get parent dashboard summary",
    "description": "Returns comprehensive dashboard data including all children's overview",
    "security": [{"BearerAuth": []}],
    "responses": {
        "200": {
            "description": "Dashboard summary fetched successfully",
        },
        "401": {"description": "Unauthorized"},
        "403": {"description": "Forbidden - not a parent"},
    }
})
def get_dashboard_route():
    return get_parent_dashboard_controller()


@parents_bp.get("/parents/children")
@jwt_required()
@roles_required("parent")
@swag_from({
    "tags": ["Parents"],
    "summary": "Get all children linked to the parent",
    "description": "Returns list of all students linked to the current parent user",
    "security": [{"BearerAuth": []}],
    "responses": {
        "200": {
            "description": "Children fetched successfully",
        },
        "401": {"description": "Unauthorized"},
    }
})
def get_children_route():
    return get_my_children_controller()


@parents_bp.get("/parents/children/<int:student_id>")
@jwt_required()
@roles_required("parent")
@swag_from({
    "tags": ["Parents"],
    "summary": "Get details of a specific child",
    "description": "Returns detailed information about a specific child/student",
    "security": [{"BearerAuth": []}],
    "parameters": [
        {"in": "path", "name": "student_id", "type": "integer", "required": True}
    ],
    "responses": {
        "200": {"description": "Child details fetched successfully"},
        "403": {"description": "Not authorized to view this student"},
        "404": {"description": "Student not found"},
    }
})
def get_child_details_route(student_id):
    return get_child_details_controller(student_id)


@parents_bp.get("/parents/children/<int:student_id>/fees")
@jwt_required()
@roles_required("parent")
@swag_from({
    "tags": ["Parents"],
    "summary": "Get fee information for a child",
    "description": "Returns fee summary and payment history for a specific child",
    "security": [{"BearerAuth": []}],
    "parameters": [
        {"in": "path", "name": "student_id", "type": "integer", "required": True}
    ],
    "responses": {
        "200": {"description": "Fee information fetched successfully"},
        "403": {"description": "Not authorized to view this student's fees"},
        "404": {"description": "Student not found"},
    }
})
def get_child_fees_route(student_id):
    return get_child_fees_controller(student_id)


@parents_bp.get("/parents/children/<int:student_id>/attendance")
@jwt_required()
@roles_required("parent")
@swag_from({
    "tags": ["Parents"],
    "summary": "Get attendance records for a child",
    "description": "Returns attendance summary and records for a specific child",
    "security": [{"BearerAuth": []}],
    "parameters": [
        {"in": "path", "name": "student_id", "type": "integer", "required": True},
        {"in": "query", "name": "days", "type": "integer", "default": 30, "description": "Number of days to look back"}
    ],
    "responses": {
        "200": {"description": "Attendance records fetched successfully"},
        "403": {"description": "Not authorized to view this student's attendance"},
        "404": {"description": "Student not found"},
    }
})
def get_child_attendance_route(student_id):
    return get_child_attendance_controller(student_id)


@parents_bp.get("/parents/children/<int:student_id>/tests")
@jwt_required()
@roles_required("parent")
@swag_from({
    "tags": ["Parents"],
    "summary": "Get test results for a child",
    "description": "Returns test results and performance summary for a specific child",
    "security": [{"BearerAuth": []}],
    "parameters": [
        {"in": "path", "name": "student_id", "type": "integer", "required": True}
    ],
    "responses": {
        "200": {"description": "Test results fetched successfully"},
        "403": {"description": "Not authorized to view this student's tests"},
        "404": {"description": "Student not found"},
    }
})
def get_child_tests_route(student_id):
    return get_child_test_results_controller(student_id)


@parents_bp.get("/parents/children/<int:student_id>/quizzes")
@jwt_required()
@roles_required("parent")
@swag_from({
    "tags": ["Parents"],
    "summary": "Get quiz results for a child",
    "description": "Returns quiz results and performance summary for a specific child",
    "security": [{"BearerAuth": []}],
    "parameters": [
        {"in": "path", "name": "student_id", "type": "integer", "required": True}
    ],
    "responses": {
        "200": {"description": "Quiz results fetched successfully"},
        "403": {"description": "Not authorized to view this student's quizzes"},
        "404": {"description": "Student not found"},
    }
})
def get_child_quizzes_route(student_id):
    return get_child_quiz_results_controller(student_id)


@parents_bp.get("/parents/children/<int:student_id>/quizzes/<int:quiz_id>")
@jwt_required()
@roles_required("parent")
@swag_from({
    "tags": ["Parents"],
    "summary": "Get quiz detail for a child",
    "description": "Returns quiz questions and student answers for a specific child",
    "security": [{"BearerAuth": []}],
    "parameters": [
        {"in": "path", "name": "student_id", "type": "integer", "required": True},
        {"in": "path", "name": "quiz_id", "type": "integer", "required": True}
    ],
    "responses": {
        "200": {"description": "Quiz detail fetched successfully"},
        "403": {"description": "Not authorized to view this student's quizzes"},
        "404": {"description": "Quiz not found"},
    }
})
def get_child_quiz_detail_route(student_id, quiz_id):
    return get_child_quiz_detail_controller(student_id, quiz_id)
