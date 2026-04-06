"""
Teacher Dashboard Routes - API endpoints for teacher-specific operations
"""
from flasgger import swag_from
from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app.controllers.teacher_dashboard_controller import (
    get_dashboard_summary_controller,
    get_my_batches_controller,
    get_batch_students_controller,
    get_batch_attendance_controller,
    mark_attendance_controller,
    get_batch_tests_controller,
    create_test_controller,
    get_test_results_controller,
    save_test_results_controller,
    get_attendance_history_controller,
    get_student_profile_controller,
)
from app.utils.auth import roles_required

teacher_dashboard_bp = Blueprint("teacher_dashboard", __name__)


@teacher_dashboard_bp.get("/teacher/dashboard")
@jwt_required()
@roles_required("coach", "director")
@swag_from({
    "tags": ["Teacher Dashboard"],
    "summary": "Get teacher dashboard summary",
    "description": "Returns comprehensive dashboard data for the logged-in teacher",
    "security": [{"BearerAuth": []}],
    "responses": {
        "200": {
            "description": "Dashboard data retrieved successfully",
        }
    }
})
def get_dashboard():
    return get_dashboard_summary_controller()


@teacher_dashboard_bp.get("/teacher/batches")
@jwt_required()
@roles_required("coach", "director")
@swag_from({
    "tags": ["Teacher Dashboard"],
    "summary": "Get teacher's batches",
    "description": "Returns all batches assigned to the logged-in teacher",
    "security": [{"BearerAuth": []}],
    "responses": {
        "200": {
            "description": "Batches retrieved successfully",
        }
    }
})
def get_batches():
    return get_my_batches_controller()


@teacher_dashboard_bp.get("/teacher/batches/<int:batch_id>/students")
@jwt_required()
@roles_required("coach", "director")
@swag_from({
    "tags": ["Teacher Dashboard"],
    "summary": "Get students in a batch",
    "description": "Returns all students in the specified batch",
    "security": [{"BearerAuth": []}],
    "parameters": [
        {
            "name": "batch_id",
            "in": "path",
            "type": "integer",
            "required": True,
            "description": "Batch ID"
        }
    ],
    "responses": {
        "200": {
            "description": "Students retrieved successfully",
        }
    }
})
def get_students(batch_id):
    return get_batch_students_controller(batch_id)


@teacher_dashboard_bp.get("/teacher/batches/<int:batch_id>/attendance")
@jwt_required()
@roles_required("coach", "director")
@swag_from({
    "tags": ["Teacher Dashboard"],
    "summary": "Get batch attendance",
    "description": "Returns attendance for a batch on a specific date",
    "security": [{"BearerAuth": []}],
    "parameters": [
        {
            "name": "batch_id",
            "in": "path",
            "type": "integer",
            "required": True,
            "description": "Batch ID"
        },
        {
            "name": "date",
            "in": "query",
            "type": "string",
            "required": False,
            "description": "Date in YYYY-MM-DD format (defaults to today)"
        }
    ],
    "responses": {
        "200": {
            "description": "Attendance retrieved successfully",
        }
    }
})
def get_attendance(batch_id):
    return get_batch_attendance_controller(batch_id, request)


@teacher_dashboard_bp.post("/teacher/batches/<int:batch_id>/attendance")
@jwt_required()
@roles_required("coach", "director")
@swag_from({
    "tags": ["Teacher Dashboard"],
    "summary": "Mark batch attendance",
    "description": "Mark attendance for multiple students in a batch",
    "security": [{"BearerAuth": []}],
    "parameters": [
        {
            "name": "batch_id",
            "in": "path",
            "type": "integer",
            "required": True,
            "description": "Batch ID"
        },
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "example": "2026-03-04"},
                    "attendance": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "student_id": {"type": "integer"},
                                "status": {"type": "string", "enum": ["present", "absent", "late", "excused"]},
                                "remarks": {"type": "string"}
                            }
                        }
                    }
                }
            }
        }
    ],
    "responses": {
        "200": {
            "description": "Attendance saved successfully",
        }
    }
})
def mark_attendance(batch_id):
    return mark_attendance_controller(batch_id, request)


@teacher_dashboard_bp.get("/teacher/batches/<int:batch_id>/attendance/history")
@jwt_required()
@roles_required("coach", "director")
@swag_from({
    "tags": ["Teacher Dashboard"],
    "summary": "Get attendance history",
    "description": "Returns attendance history for a batch over a date range",
    "security": [{"BearerAuth": []}],
    "parameters": [
        {
            "name": "batch_id",
            "in": "path",
            "type": "integer",
            "required": True,
            "description": "Batch ID"
        },
        {
            "name": "start_date",
            "in": "query",
            "type": "string",
            "required": False,
            "description": "Start date in YYYY-MM-DD format"
        },
        {
            "name": "end_date",
            "in": "query",
            "type": "string",
            "required": False,
            "description": "End date in YYYY-MM-DD format"
        }
    ],
    "responses": {
        "200": {
            "description": "Attendance history retrieved successfully",
        }
    }
})
def get_history(batch_id):
    return get_attendance_history_controller(batch_id, request)


@teacher_dashboard_bp.get("/teacher/batches/<int:batch_id>/tests")
@jwt_required()
@roles_required("coach", "director")
@swag_from({
    "tags": ["Teacher Dashboard"],
    "summary": "Get batch tests",
    "description": "Returns all tests for a batch",
    "security": [{"BearerAuth": []}],
    "parameters": [
        {
            "name": "batch_id",
            "in": "path",
            "type": "integer",
            "required": True,
            "description": "Batch ID"
        }
    ],
    "responses": {
        "200": {
            "description": "Tests retrieved successfully",
        }
    }
})
def get_tests(batch_id):
    return get_batch_tests_controller(batch_id)


@teacher_dashboard_bp.post("/teacher/batches/<int:batch_id>/tests")
@jwt_required()
@roles_required("coach", "director")
@swag_from({
    "tags": ["Teacher Dashboard"],
    "summary": "Create a test",
    "description": "Create a new test for a batch",
    "security": [{"BearerAuth": []}],
    "parameters": [
        {
            "name": "batch_id",
            "in": "path",
            "type": "integer",
            "required": True,
            "description": "Batch ID"
        },
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "subject": {"type": "string"},
                    "max_marks": {"type": "number"},
                    "test_date": {"type": "string", "example": "2026-03-15"}
                }
            }
        }
    ],
    "responses": {
        "201": {
            "description": "Test created successfully",
        }
    }
})
def create_batch_test(batch_id):
    return create_test_controller(batch_id, request)


@teacher_dashboard_bp.get("/teacher/tests/<int:test_id>/results")
@jwt_required()
@roles_required("coach", "director")
@swag_from({
    "tags": ["Teacher Dashboard"],
    "summary": "Get test results",
    "description": "Returns all results for a test",
    "security": [{"BearerAuth": []}],
    "parameters": [
        {
            "name": "test_id",
            "in": "path",
            "type": "integer",
            "required": True,
            "description": "Test ID"
        }
    ],
    "responses": {
        "200": {
            "description": "Results retrieved successfully",
        }
    }
})
def get_results(test_id):
    return get_test_results_controller(test_id)


@teacher_dashboard_bp.post("/teacher/tests/<int:test_id>/results")
@jwt_required()
@roles_required("coach", "director")
@swag_from({
    "tags": ["Teacher Dashboard"],
    "summary": "Save test results",
    "description": "Save test results for multiple students",
    "security": [{"BearerAuth": []}],
    "parameters": [
        {
            "name": "test_id",
            "in": "path",
            "type": "integer",
            "required": True,
            "description": "Test ID"
        },
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "results": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "student_id": {"type": "integer"},
                                "marks_obtained": {"type": "number"},
                                "remarks": {"type": "string"}
                            }
                        }
                    }
                }
            }
        }
    ],
    "responses": {
        "200": {
            "description": "Results saved successfully",
        }
    }
})
def save_results(test_id):
    return save_test_results_controller(test_id, request)


@teacher_dashboard_bp.get("/teacher/students/<int:student_id>/profile")
@jwt_required()
@roles_required("coach", "director")
@swag_from({
    "tags": ["Teacher Dashboard"],
    "summary": "Get student profile",
    "description": "Returns detailed profile of a student (teacher must be assigned to the student's batch)",
    "security": [{"BearerAuth": []}],
    "parameters": [
        {
            "name": "student_id",
            "in": "path",
            "type": "integer",
            "required": True,
            "description": "Student ID"
        }
    ],
    "responses": {
        "200": {
            "description": "Student profile retrieved successfully",
        }
    }
})
def get_student_profile_route(student_id):
    return get_student_profile_controller(student_id)
