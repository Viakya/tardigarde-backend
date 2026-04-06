from flask import Blueprint
from flasgger import swag_from
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.controllers.auth_controller import (
    admin_only_example,
    delete_user_controller,
    get_me,
    google_login_user,
    login_user,
    protected_example,
    registered_users,
    register_user,
    update_user_controller,
    users_summary,
)
from app.utils.auth import roles_required

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/auth/register")
@swag_from(
    {
        "tags": ["Auth"],
        "summary": "Register a new user account",
        "security": [],
        "parameters": [
            {
                "in": "body",
                "name": "body",
                "required": True,
                "schema": {"$ref": "#/definitions/AuthRegisterRequest"},
            }
        ],
        "responses": {
            201: {"schema": {"$ref": "#/definitions/StandardResponse"}},
            400: {"schema": {"$ref": "#/definitions/StandardResponse"}},
        },
    }
)
def register_route():
    return register_user()


@auth_bp.post("/auth/login")
@swag_from(
    {
        "tags": ["Auth"],
        "summary": "Authenticate user and return JWT token",
        "security": [],
        "parameters": [
            {
                "in": "body",
                "name": "body",
                "required": True,
                "schema": {"$ref": "#/definitions/AuthLoginRequest"},
            }
        ],
        "responses": {
            200: {"schema": {"$ref": "#/definitions/StandardResponse"}},
            401: {"schema": {"$ref": "#/definitions/StandardResponse"}},
        },
    }
)
def login_route():
    return login_user()


@auth_bp.post("/auth/google")
@swag_from(
    {
        "tags": ["Auth"],
        "summary": "Authenticate user with Google and return JWT token",
        "security": [],
        "parameters": [
            {
                "in": "body",
                "name": "body",
                "required": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "credential": {"type": "string"},
                    },
                    "required": ["credential"],
                },
            }
        ],
        "responses": {
            200: {"schema": {"$ref": "#/definitions/StandardResponse"}},
            401: {"schema": {"$ref": "#/definitions/StandardResponse"}},
        },
    }
)
def google_login_route():
    return google_login_user()


@auth_bp.get("/auth/me")
@jwt_required()
@swag_from(
    {
        "tags": ["Auth"],
        "summary": "Fetch authenticated user details",
        "security": [{"BearerAuth": []}],
        "responses": {
            200: {"schema": {"$ref": "#/definitions/StandardResponse"}},
            401: {"schema": {"$ref": "#/definitions/StandardResponse"}},
        },
    }
)
def me_route():
    current_user_id = get_jwt_identity()
    return get_me(current_user_id)


@auth_bp.get("/auth/protected")
@jwt_required()
@swag_from(
    {
        "tags": ["Auth"],
        "summary": "Example JWT-protected endpoint",
        "security": [{"BearerAuth": []}],
        "responses": {
            200: {"schema": {"$ref": "#/definitions/StandardResponse"}},
            401: {"schema": {"$ref": "#/definitions/StandardResponse"}},
        },
    }
)
def protected_route():
    current_user_id = get_jwt_identity()
    return protected_example(current_user_id)


@auth_bp.get("/auth/admin-only")
@roles_required("admin")
@swag_from(
    {
        "tags": ["Auth"],
        "summary": "Example route accessible only by admin role",
        "security": [{"BearerAuth": []}],
        "responses": {
            200: {"schema": {"$ref": "#/definitions/StandardResponse"}},
            403: {"schema": {"$ref": "#/definitions/StandardResponse"}},
        },
    }
)
def admin_only_route():
    return admin_only_example()


@auth_bp.get("/auth/users-summary")
@roles_required("admin")
@swag_from(
    {
        "tags": ["Auth"],
        "summary": "Get total registered users and admin details",
        "security": [{"BearerAuth": []}],
        "responses": {
            200: {"schema": {"$ref": "#/definitions/StandardResponse"}},
            403: {"schema": {"$ref": "#/definitions/StandardResponse"}},
        },
    }
)
def users_summary_route():
    return users_summary()


@auth_bp.get("/auth/registered-users")
@roles_required("admin", "director", "manager")
@swag_from(
    {
        "tags": ["Auth"],
        "summary": "Get all users registered so far",
        "security": [{"BearerAuth": []}],
        "responses": {
            200: {"schema": {"$ref": "#/definitions/StandardResponse"}},
            403: {"schema": {"$ref": "#/definitions/StandardResponse"}},
        },
    }
)
def registered_users_route():
    return registered_users()


@auth_bp.put("/auth/users/<int:user_id>")
@roles_required("admin", "director", "manager")
@swag_from(
    {
        "tags": ["Auth"],
        "summary": "Update user details (admin/manager only)",
        "security": [{"BearerAuth": []}],
        "parameters": [
            {"in": "path", "name": "user_id", "type": "integer", "required": True},
            {
                "in": "body",
                "name": "body",
                "required": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "full_name": {"type": "string"},
                        "role": {"type": "string"},
                        "is_active": {"type": "boolean"},
                        "password": {"type": "string"},
                    },
                },
            },
        ],
        "responses": {
            200: {"schema": {"$ref": "#/definitions/StandardResponse"}},
            404: {"schema": {"$ref": "#/definitions/StandardResponse"}},
        },
    }
)
def update_user_route(user_id):
    return update_user_controller(user_id)


@auth_bp.delete("/auth/users/<int:user_id>")
@roles_required("admin", "director", "manager")
@swag_from(
    {
        "tags": ["Auth"],
        "summary": "Soft delete user (admin/manager only)",
        "security": [{"BearerAuth": []}],
        "parameters": [{"in": "path", "name": "user_id", "type": "integer", "required": True}],
        "responses": {
            200: {"schema": {"$ref": "#/definitions/StandardResponse"}},
            404: {"schema": {"$ref": "#/definitions/StandardResponse"}},
        },
    }
)
def delete_user_route(user_id):
    return delete_user_controller(user_id)
