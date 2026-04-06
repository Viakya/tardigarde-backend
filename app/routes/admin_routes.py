from flask import Blueprint
from flasgger import swag_from

from app.controllers.admin_controller import (
    create_row_controller,
    delete_row_controller,
    list_rows_controller,
    list_tables_controller,
    table_schema_controller,
    update_row_controller,
)
from app.utils.auth import roles_required

admin_bp = Blueprint("admin", __name__)


@admin_bp.get("/admin/tables")
@roles_required("admin")
@swag_from(
    {
        "tags": ["Admin"],
        "summary": "List all database tables (admin only)",
        "security": [{"BearerAuth": []}],
        "responses": {200: {"schema": {"$ref": "#/definitions/StandardResponse"}}},
    }
)
def list_tables_route():
    return list_tables_controller()


@admin_bp.get("/admin/tables/<string:table_name>/schema")
@roles_required("admin")
@swag_from(
    {
        "tags": ["Admin"],
        "summary": "Get table schema (admin only)",
        "security": [{"BearerAuth": []}],
        "parameters": [
            {"in": "path", "name": "table_name", "type": "string", "required": True}
        ],
        "responses": {200: {"schema": {"$ref": "#/definitions/StandardResponse"}}},
    }
)
def table_schema_route(table_name):
    return table_schema_controller(table_name)


@admin_bp.get("/admin/tables/<string:table_name>/rows")
@roles_required("admin")
@swag_from(
    {
        "tags": ["Admin"],
        "summary": "List rows for a table (admin only)",
        "security": [{"BearerAuth": []}],
        "parameters": [
            {"in": "path", "name": "table_name", "type": "string", "required": True},
            {"in": "query", "name": "page", "type": "integer", "required": False},
            {"in": "query", "name": "per_page", "type": "integer", "required": False},
        ],
        "responses": {200: {"schema": {"$ref": "#/definitions/StandardResponse"}}},
    }
)
def list_rows_route(table_name):
    return list_rows_controller(table_name)


@admin_bp.post("/admin/tables/<string:table_name>/rows")
@roles_required("admin")
@swag_from(
    {
        "tags": ["Admin"],
        "summary": "Create a row in a table (admin only)",
        "security": [{"BearerAuth": []}],
        "parameters": [
            {"in": "path", "name": "table_name", "type": "string", "required": True},
            {"in": "body", "name": "body", "required": True},
        ],
        "responses": {201: {"schema": {"$ref": "#/definitions/StandardResponse"}}},
    }
)
def create_row_route(table_name):
    return create_row_controller(table_name)


@admin_bp.put("/admin/tables/<string:table_name>/rows")
@roles_required("admin")
@swag_from(
    {
        "tags": ["Admin"],
        "summary": "Update a row in a table (admin only)",
        "security": [{"BearerAuth": []}],
        "parameters": [
            {"in": "path", "name": "table_name", "type": "string", "required": True},
            {"in": "body", "name": "body", "required": True},
        ],
        "responses": {200: {"schema": {"$ref": "#/definitions/StandardResponse"}}},
    }
)
def update_row_route(table_name):
    return update_row_controller(table_name)


@admin_bp.delete("/admin/tables/<string:table_name>/rows")
@roles_required("admin")
@swag_from(
    {
        "tags": ["Admin"],
        "summary": "Delete a row from a table (admin only)",
        "security": [{"BearerAuth": []}],
        "parameters": [
            {"in": "path", "name": "table_name", "type": "string", "required": True},
            {"in": "body", "name": "body", "required": True},
        ],
        "responses": {200: {"schema": {"$ref": "#/definitions/StandardResponse"}}},
    }
)
def delete_row_route(table_name):
    return delete_row_controller(table_name)
