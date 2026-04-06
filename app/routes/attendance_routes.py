from flask import Blueprint
from flasgger import swag_from
from flask_jwt_extended import jwt_required

from app.controllers.attendance_controller import (
    create_attendance_controller,
    delete_attendance_controller,
    get_attendance_controller,
    list_attendance_controller,
    update_attendance_controller,
)
from app.utils.auth import roles_required

attendance_bp = Blueprint("attendance", __name__)


@attendance_bp.post("/attendance")
@roles_required("coach", "director")
@swag_from(
    {
        "tags": ["Attendance"],
        "summary": "Mark attendance for a student (coach/director only)",
        "security": [{"BearerAuth": []}],
        "parameters": [
            {
                "in": "body",
                "name": "body",
                "required": True,
                "schema": {"$ref": "#/definitions/AttendanceRequest"},
            }
        ],
        "responses": {
            201: {"schema": {"$ref": "#/definitions/StandardResponse"}},
            400: {"schema": {"$ref": "#/definitions/StandardResponse"}},
            403: {"schema": {"$ref": "#/definitions/StandardResponse"}},
            409: {"schema": {"$ref": "#/definitions/StandardResponse"}},
        },
    }
)
def create_attendance_route():
    return create_attendance_controller()


@attendance_bp.get("/attendance")
@jwt_required()
@swag_from(
    {
        "tags": ["Attendance"],
        "summary": "List attendance records with pagination and filters",
        "security": [{"BearerAuth": []}],
        "parameters": [
            {"in": "query", "name": "page", "type": "integer", "required": False, "default": 1},
            {
                "in": "query",
                "name": "per_page",
                "type": "integer",
                "required": False,
                "default": 10,
            },
            {"in": "query", "name": "student_id", "type": "integer", "required": False},
            {"in": "query", "name": "batch_id", "type": "integer", "required": False},
            {
                "in": "query",
                "name": "attendance_date",
                "type": "string",
                "required": False,
                "description": "ISO date in YYYY-MM-DD format",
            },
        ],
        "responses": {
            200: {"schema": {"$ref": "#/definitions/StandardResponse"}},
        },
    }
)
def list_attendance_route():
    return list_attendance_controller()


@attendance_bp.get("/attendance/<int:attendance_id>")
@jwt_required()
@swag_from(
    {
        "tags": ["Attendance"],
        "summary": "Get one attendance record by ID",
        "security": [{"BearerAuth": []}],
        "parameters": [{"in": "path", "name": "attendance_id", "type": "integer", "required": True}],
        "responses": {
            200: {"schema": {"$ref": "#/definitions/StandardResponse"}},
            404: {"schema": {"$ref": "#/definitions/StandardResponse"}},
        },
    }
)
def get_attendance_route(attendance_id):
    return get_attendance_controller(attendance_id)


@attendance_bp.put("/attendance/<int:attendance_id>")
@roles_required("coach", "director")
@swag_from(
    {
        "tags": ["Attendance"],
        "summary": "Update attendance status/remarks",
        "security": [{"BearerAuth": []}],
        "parameters": [
            {"in": "path", "name": "attendance_id", "type": "integer", "required": True},
            {
                "in": "body",
                "name": "body",
                "required": True,
                "schema": {"$ref": "#/definitions/AttendanceUpdateRequest"},
            },
        ],
        "responses": {
            200: {"schema": {"$ref": "#/definitions/StandardResponse"}},
            400: {"schema": {"$ref": "#/definitions/StandardResponse"}},
            403: {"schema": {"$ref": "#/definitions/StandardResponse"}},
        },
    }
)
def update_attendance_route(attendance_id):
    return update_attendance_controller(attendance_id)


@attendance_bp.delete("/attendance/<int:attendance_id>")
@roles_required("director")
@swag_from(
    {
        "tags": ["Attendance"],
        "summary": "Soft delete an attendance record (director only)",
        "security": [{"BearerAuth": []}],
        "parameters": [{"in": "path", "name": "attendance_id", "type": "integer", "required": True}],
        "responses": {
            200: {"schema": {"$ref": "#/definitions/StandardResponse"}},
            403: {"schema": {"$ref": "#/definitions/StandardResponse"}},
        },
    }
)
def delete_attendance_route(attendance_id):
    return delete_attendance_controller(attendance_id)
