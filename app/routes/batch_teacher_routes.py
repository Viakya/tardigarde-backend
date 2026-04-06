from flask import Blueprint
from flasgger import swag_from
from flask_jwt_extended import jwt_required

from app.controllers.batch_teacher_controller import (
    assign_teacher_to_batch_controller,
    list_batches_for_teacher_controller,
    list_teachers_for_batch_controller,
    remove_teacher_from_batch_controller,
)
from app.utils.auth import roles_required

batch_teachers_bp = Blueprint("batch_teachers", __name__)


@batch_teachers_bp.post("/batches/<int:batch_id>/teachers")
@roles_required("director", "manager")
@swag_from(
    {
        "tags": ["Batch-Teacher Assignment"],
        "summary": "Assign a teacher to a batch (director/manager only)",
        "security": [{"BearerAuth": []}],
        "parameters": [
            {"in": "path", "name": "batch_id", "type": "integer", "required": True},
            {
                "in": "body",
                "name": "body",
                "required": True,
                "schema": {"$ref": "#/definitions/BatchTeacherAssignRequest"},
            },
        ],
        "responses": {
            201: {"schema": {"$ref": "#/definitions/StandardResponse"}},
            409: {"schema": {"$ref": "#/definitions/StandardResponse"}},
        },
    }
)
def assign_teacher_to_batch_route(batch_id):
    return assign_teacher_to_batch_controller(batch_id)


@batch_teachers_bp.delete("/batches/<int:batch_id>/teachers/<int:teacher_id>")
@roles_required("director", "manager")
@swag_from(
    {
        "tags": ["Batch-Teacher Assignment"],
        "summary": "Remove assignment between teacher and batch (director/manager only)",
        "security": [{"BearerAuth": []}],
        "parameters": [
            {"in": "path", "name": "batch_id", "type": "integer", "required": True},
            {"in": "path", "name": "teacher_id", "type": "integer", "required": True},
        ],
        "responses": {200: {"schema": {"$ref": "#/definitions/StandardResponse"}}},
    }
)
def remove_teacher_from_batch_route(batch_id, teacher_id):
    return remove_teacher_from_batch_controller(batch_id, teacher_id)


@batch_teachers_bp.get("/batches/<int:batch_id>/teachers")
@jwt_required()
@swag_from(
    {
        "tags": ["Batch-Teacher Assignment"],
        "summary": "List active teachers assigned to a batch",
        "security": [{"BearerAuth": []}],
        "parameters": [{"in": "path", "name": "batch_id", "type": "integer", "required": True}],
        "responses": {200: {"schema": {"$ref": "#/definitions/StandardResponse"}}},
    }
)
def list_teachers_for_batch_route(batch_id):
    return list_teachers_for_batch_controller(batch_id)


@batch_teachers_bp.get("/teachers/<int:teacher_id>/batches")
@jwt_required()
@swag_from(
    {
        "tags": ["Batch-Teacher Assignment"],
        "summary": "List active batches assigned to a teacher",
        "security": [{"BearerAuth": []}],
        "parameters": [{"in": "path", "name": "teacher_id", "type": "integer", "required": True}],
        "responses": {200: {"schema": {"$ref": "#/definitions/StandardResponse"}}},
    }
)
def list_batches_for_teacher_route(teacher_id):
    return list_batches_for_teacher_controller(teacher_id)
