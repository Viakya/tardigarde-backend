from flask import Blueprint
from flasgger import swag_from
from app.controllers.batch_controller import (
    create_batch_controller,
    delete_batch_controller,
    get_batch_controller,
    get_batch_profile_controller,
    list_batches_controller,
    update_batch_controller,
)
from app.utils.auth import roles_required

batches_bp = Blueprint("batches", __name__)


@batches_bp.post("/batches")
@roles_required("director", "manager")
@swag_from(
    {
        "tags": ["Batches"],
        "summary": "Create a batch (director/manager only)",
        "security": [{"BearerAuth": []}],
        "parameters": [
            {
                "in": "body",
                "name": "body",
                "required": True,
                "schema": {"$ref": "#/definitions/BatchRequest"},
            }
        ],
        "responses": {201: {"schema": {"$ref": "#/definitions/StandardResponse"}}},
    }
)
def create_batch_route():
    return create_batch_controller()


@batches_bp.get("/batches")
@roles_required("admin", "director", "manager", "coach", "student")
@swag_from(
    {
        "tags": ["Batches"],
        "summary": "List active batches",
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
def list_batches_route():
    return list_batches_controller()


@batches_bp.get("/batches/<int:batch_id>")
@roles_required("admin", "director", "manager", "coach", "student")
@swag_from(
    {
        "tags": ["Batches"],
        "summary": "Get batch by ID",
        "security": [{"BearerAuth": []}],
        "parameters": [{"in": "path", "name": "batch_id", "type": "integer", "required": True}],
        "responses": {
            200: {"schema": {"$ref": "#/definitions/StandardResponse"}},
            404: {"schema": {"$ref": "#/definitions/StandardResponse"}},
        },
    }
)
def get_batch_route(batch_id):
    return get_batch_controller(batch_id)


@batches_bp.put("/batches/<int:batch_id>")
@roles_required("director", "manager")
@swag_from(
    {
        "tags": ["Batches"],
        "summary": "Update batch (director/manager only)",
        "security": [{"BearerAuth": []}],
        "parameters": [
            {"in": "path", "name": "batch_id", "type": "integer", "required": True},
            {
                "in": "body",
                "name": "body",
                "required": True,
                "schema": {"$ref": "#/definitions/BatchRequest"},
            },
        ],
        "responses": {200: {"schema": {"$ref": "#/definitions/StandardResponse"}}},
    }
)
def update_batch_route(batch_id):
    return update_batch_controller(batch_id)


@batches_bp.delete("/batches/<int:batch_id>")
@roles_required("director", "manager")
@swag_from(
    {
        "tags": ["Batches"],
        "summary": "Soft delete batch (director/manager only)",
        "security": [{"BearerAuth": []}],
        "parameters": [{"in": "path", "name": "batch_id", "type": "integer", "required": True}],
        "responses": {200: {"schema": {"$ref": "#/definitions/StandardResponse"}}},
    }
)
def delete_batch_route(batch_id):
    return delete_batch_controller(batch_id)


@batches_bp.get("/batches/<int:batch_id>/profile")
@roles_required("admin", "director", "manager")
@swag_from(
    {
        "tags": ["Batches"],
        "summary": "Get batch profile with financial summary",
        "security": [{"BearerAuth": []}],
        "parameters": [{"in": "path", "name": "batch_id", "type": "integer", "required": True}],
        "responses": {
            200: {"schema": {"$ref": "#/definitions/StandardResponse"}},
            404: {"schema": {"$ref": "#/definitions/StandardResponse"}},
        },
    }
)
def get_batch_profile_route(batch_id):
    return get_batch_profile_controller(batch_id)
