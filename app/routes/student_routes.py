from flask import Blueprint
from flasgger import swag_from
from flask_jwt_extended import jwt_required

from app.controllers.student_controller import (
    create_student_controller,
    delete_student_controller,
    get_student_controller,
    get_my_student_profile_controller,
    list_students_controller,
    update_student_controller,
    connect_parent_controller,
    disconnect_parent_controller,
)
from app.utils.auth import roles_required

students_bp = Blueprint("students", __name__)


@students_bp.post("/students")
@roles_required("director", "manager")
@swag_from(
    {
        "tags": ["Students"],
        "summary": "Create a student profile (director/manager only)",
        "security": [{"BearerAuth": []}],
        "parameters": [
            {
                "in": "body",
                "name": "body",
                "required": True,
                "schema": {"$ref": "#/definitions/StudentRequest"},
            }
        ],
        "responses": {
            201: {"schema": {"$ref": "#/definitions/StandardResponse"}},
            403: {"schema": {"$ref": "#/definitions/StandardResponse"}},
        },
    }
)
def create_student_route():
    return create_student_controller()


@students_bp.get("/students")
@jwt_required()
@swag_from(
    {
        "tags": ["Students"],
        "summary": "Get paginated active students",
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
        ],
        "responses": {200: {"schema": {"$ref": "#/definitions/StandardResponse"}}},
    }
)
def list_students_route():
    return list_students_controller()


@students_bp.get("/students/me")
@jwt_required()
@swag_from(
    {
        "tags": ["Students"],
        "summary": "Get the student profile for the currently logged-in student user",
        "security": [{"BearerAuth": []}],
        "responses": {
            200: {"schema": {"$ref": "#/definitions/StandardResponse"}},
            404: {"schema": {"$ref": "#/definitions/StandardResponse"}},
        },
    }
)
def get_my_student_profile_route():
    return get_my_student_profile_controller()


@students_bp.get("/students/<int:student_id>")
@jwt_required()
@swag_from(
    {
        "tags": ["Students"],
        "summary": "Fetch one active student by ID",
        "security": [{"BearerAuth": []}],
        "parameters": [{"in": "path", "name": "student_id", "type": "integer", "required": True}],
        "responses": {
            200: {"schema": {"$ref": "#/definitions/StandardResponse"}},
            404: {"schema": {"$ref": "#/definitions/StandardResponse"}},
        },
    }
)
def get_student_route(student_id):
    return get_student_controller(student_id)


@students_bp.put("/students/<int:student_id>")
@jwt_required()
@swag_from(
    {
        "tags": ["Students"],
        "summary": "Update active student profile fields",
        "security": [{"BearerAuth": []}],
        "parameters": [
            {"in": "path", "name": "student_id", "type": "integer", "required": True},
            {
                "in": "body",
                "name": "body",
                "required": True,
                "schema": {"$ref": "#/definitions/StudentRequest"},
            },
        ],
        "responses": {200: {"schema": {"$ref": "#/definitions/StandardResponse"}}},
    }
)
def update_student_route(student_id):
    return update_student_controller(student_id)


@students_bp.delete("/students/<int:student_id>")
@jwt_required()
@swag_from(
    {
        "tags": ["Students"],
        "summary": "Soft delete student by ID",
        "security": [{"BearerAuth": []}],
        "parameters": [{"in": "path", "name": "student_id", "type": "integer", "required": True}],
        "responses": {200: {"schema": {"$ref": "#/definitions/StandardResponse"}}},
    }
)
def delete_student_route(student_id):
    return delete_student_controller(student_id)


@students_bp.post("/students/<int:student_id>/parents")
@roles_required("director", "manager")
@swag_from(
    {
        "tags": ["Students"],
        "summary": "Connect a parent to a student (director/manager only)",
        "security": [{"BearerAuth": []}],
        "parameters": [
            {"in": "path", "name": "student_id", "type": "integer", "required": True},
            {
                "in": "body",
                "name": "body",
                "required": True,
                "schema": {
                    "type": "object",
                    "properties": {"parent_user_id": {"type": "integer"}},
                    "required": ["parent_user_id"],
                },
            },
        ],
        "responses": {
            200: {"schema": {"$ref": "#/definitions/StandardResponse"}},
            404: {"schema": {"$ref": "#/definitions/StandardResponse"}},
            409: {"schema": {"$ref": "#/definitions/StandardResponse"}},
        },
    }
)
def connect_parent_route(student_id):
    return connect_parent_controller(student_id)


@students_bp.delete("/students/<int:student_id>/parents/<int:parent_user_id>")
@roles_required("director", "manager")
@swag_from(
    {
        "tags": ["Students"],
        "summary": "Disconnect a parent from a student (director/manager only)",
        "security": [{"BearerAuth": []}],
        "parameters": [
            {"in": "path", "name": "student_id", "type": "integer", "required": True},
            {"in": "path", "name": "parent_user_id", "type": "integer", "required": True},
        ],
        "responses": {
            200: {"schema": {"$ref": "#/definitions/StandardResponse"}},
            404: {"schema": {"$ref": "#/definitions/StandardResponse"}},
        },
    }
)
def disconnect_parent_route(student_id, parent_user_id):
    return disconnect_parent_controller(student_id, parent_user_id)
