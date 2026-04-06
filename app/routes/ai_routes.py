from flask import Blueprint
from flasgger import swag_from
from flask_jwt_extended import jwt_required

from app.controllers.ai_controller import (
    coach_batch_ai_summary_controller,
    fee_risk_prediction_controller,
    operations_ai_summary_controller,
    parent_child_ai_summary_controller,
    parent_weekly_digest_controller,
)
from app.utils.auth import roles_required

ai_bp = Blueprint("ai", __name__)


@ai_bp.post("/ai/ops-summary")
@jwt_required()
@roles_required("admin", "director", "manager")
@swag_from(
    {
        "tags": ["AI"],
        "summary": "Generate AI operations summary",
        "security": [{"BearerAuth": []}],
        "parameters": [
            {
                "in": "body",
                "name": "body",
                "required": False,
                "schema": {
                    "type": "object",
                    "properties": {
                        "year": {"type": "integer", "example": 2026},
                        "batch_id": {"type": "integer", "example": 2},
                        "focus": {"type": "string", "example": "cashflow and attendance risks"},
                    },
                },
            }
        ],
        "responses": {
            200: {"schema": {"$ref": "#/definitions/StandardResponse"}},
            400: {"schema": {"$ref": "#/definitions/StandardResponse"}},
            403: {"schema": {"$ref": "#/definitions/StandardResponse"}},
        },
    }
)
def operations_ai_summary_route():
    return operations_ai_summary_controller()


@ai_bp.post("/ai/coach/batches/<int:batch_id>/insights")
@jwt_required()
@roles_required("coach", "director")
@swag_from(
    {
        "tags": ["AI"],
        "summary": "Generate AI coaching insights for a batch",
        "security": [{"BearerAuth": []}],
        "parameters": [
            {"in": "path", "name": "batch_id", "type": "integer", "required": True},
            {
                "in": "body",
                "name": "body",
                "required": False,
                "schema": {
                    "type": "object",
                    "properties": {
                        "focus": {"type": "string", "example": "interventions for low attendance"},
                    },
                },
            },
        ],
        "responses": {
            200: {"schema": {"$ref": "#/definitions/StandardResponse"}},
            403: {"schema": {"$ref": "#/definitions/StandardResponse"}},
            404: {"schema": {"$ref": "#/definitions/StandardResponse"}},
        },
    }
)
def coach_batch_ai_summary_route(batch_id):
    return coach_batch_ai_summary_controller(batch_id)


@ai_bp.post("/ai/parent/children/<int:student_id>/summary")
@jwt_required()
@roles_required("parent")
@swag_from(
    {
        "tags": ["AI"],
        "summary": "Generate AI progress summary for a parent child view",
        "security": [{"BearerAuth": []}],
        "parameters": [
            {"in": "path", "name": "student_id", "type": "integer", "required": True},
            {
                "in": "body",
                "name": "body",
                "required": False,
                "schema": {
                    "type": "object",
                    "properties": {
                        "focus": {"type": "string", "example": "discipline and performance improvement"},
                    },
                },
            },
        ],
        "responses": {
            200: {"schema": {"$ref": "#/definitions/StandardResponse"}},
            403: {"schema": {"$ref": "#/definitions/StandardResponse"}},
            404: {"schema": {"$ref": "#/definitions/StandardResponse"}},
        },
    }
)
def parent_child_ai_summary_route(student_id):
    return parent_child_ai_summary_controller(student_id)


@ai_bp.post("/ai/parent/children/<int:student_id>/weekly-digest")
@jwt_required()
@roles_required("parent")
@swag_from(
    {
        "tags": ["AI"],
        "summary": "Generate weekly AI digest for parent child view",
        "security": [{"BearerAuth": []}],
        "parameters": [
            {"in": "path", "name": "student_id", "type": "integer", "required": True},
            {
                "in": "body",
                "name": "body",
                "required": False,
                "schema": {
                    "type": "object",
                    "properties": {
                        "focus": {"type": "string", "example": "weekly progress and discipline"},
                    },
                },
            },
        ],
        "responses": {
            200: {"schema": {"$ref": "#/definitions/StandardResponse"}},
            403: {"schema": {"$ref": "#/definitions/StandardResponse"}},
            404: {"schema": {"$ref": "#/definitions/StandardResponse"}},
        },
    }
)
def parent_weekly_digest_route(student_id):
    return parent_weekly_digest_controller(student_id)


@ai_bp.post("/ai/fee-risk-prediction")
@jwt_required()
@roles_required("admin", "director", "manager")
@swag_from(
    {
        "tags": ["AI"],
        "summary": "Generate AI fee risk prediction list",
        "security": [{"BearerAuth": []}],
        "parameters": [
            {
                "in": "body",
                "name": "body",
                "required": False,
                "schema": {
                    "type": "object",
                    "properties": {
                        "year": {"type": "integer", "example": 2026},
                        "focus": {"type": "string", "example": "identify high-risk dues for follow-up"},
                    },
                },
            }
        ],
        "responses": {
            200: {"schema": {"$ref": "#/definitions/StandardResponse"}},
            400: {"schema": {"$ref": "#/definitions/StandardResponse"}},
            403: {"schema": {"$ref": "#/definitions/StandardResponse"}},
        },
    }
)
def fee_risk_prediction_route():
    return fee_risk_prediction_controller()
