from flask import Blueprint
from flasgger import swag_from
from flask_jwt_extended import jwt_required

from app.controllers.teacher_controller import (
    create_teacher_controller,
    delete_teacher_controller,
    get_teacher_controller,
    list_teachers_controller,
    update_teacher_controller,
)
from app.utils.auth import roles_required

teachers_bp = Blueprint("teachers", __name__)


@teachers_bp.post("/teachers")
@roles_required("director", "manager")
@swag_from(
    {
        "tags": ["Teachers"],
        "summary": "Create teacher profile for a coach user (director/manager only)",
        "security": [{"BearerAuth": []}],
        "parameters": [
            {
                "in": "body",
                "name": "body",
                "required": True,
                "schema": {"$ref": "#/definitions/TeacherRequest"},
            }
        ],
        "responses": {
            201: {"schema": {"$ref": "#/definitions/StandardResponse"}},
            403: {"schema": {"$ref": "#/definitions/StandardResponse"}},
        },
    }
)
def create_teacher_route():
    return create_teacher_controller()


@teachers_bp.get("/teachers")
@jwt_required()
@swag_from(
    {
        "tags": ["Teachers"],
        "summary": "Get paginated active teachers",
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
def list_teachers_route():
    return list_teachers_controller()


@teachers_bp.get("/teachers/<int:teacher_id>")
@jwt_required()
@swag_from(
    {
        "tags": ["Teachers"],
        "summary": "Fetch active teacher details",
        "security": [{"BearerAuth": []}],
        "parameters": [{"in": "path", "name": "teacher_id", "type": "integer", "required": True}],
        "responses": {
            200: {"schema": {"$ref": "#/definitions/StandardResponse"}},
            404: {"schema": {"$ref": "#/definitions/StandardResponse"}},
        },
    }
)
def get_teacher_route(teacher_id):
    return get_teacher_controller(teacher_id)


@teachers_bp.put("/teachers/<int:teacher_id>")
@roles_required("director", "manager")
@swag_from(
    {
        "tags": ["Teachers"],
        "summary": "Update teacher profile fields (director/manager only)",
        "security": [{"BearerAuth": []}],
        "parameters": [
            {"in": "path", "name": "teacher_id", "type": "integer", "required": True},
            {
                "in": "body",
                "name": "body",
                "required": True,
                "schema": {"$ref": "#/definitions/TeacherRequest"},
            },
        ],
        "responses": {200: {"schema": {"$ref": "#/definitions/StandardResponse"}}},
    }
)
def update_teacher_route(teacher_id):
    return update_teacher_controller(teacher_id)


@teachers_bp.delete("/teachers/<int:teacher_id>")
@roles_required("director", "manager")
@swag_from(
    {
        "tags": ["Teachers"],
        "summary": "Soft delete teacher profile (director only)",
        "security": [{"BearerAuth": []}],
        "parameters": [{"in": "path", "name": "teacher_id", "type": "integer", "required": True}],
        "responses": {
            200: {"schema": {"$ref": "#/definitions/StandardResponse"}},
            403: {"schema": {"$ref": "#/definitions/StandardResponse"}},
        },
    }
)
def delete_teacher_route(teacher_id):
    return delete_teacher_controller(teacher_id)
