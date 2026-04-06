from flask import Blueprint
from flasgger import swag_from

from app.controllers.health_controller import health_check, wakeup_ping

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
@swag_from(
    {
        "tags": ["Health"],
        "summary": "Get service health status",
        "security": [],
        "responses": {200: {"schema": {"$ref": "#/definitions/StandardResponse"}}},
    }
)
def health_route():
    return health_check()


@health_bp.get("/wakeup")
@swag_from(
    {
        "tags": ["Health"],
        "summary": "Wake up the service (ping)",
        "security": [],
        "responses": {200: {"schema": {"$ref": "#/definitions/StandardResponse"}}},
    }
)
def wakeup_route():
    return wakeup_ping()
