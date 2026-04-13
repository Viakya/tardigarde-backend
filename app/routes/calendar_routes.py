from flask import Blueprint
from flasgger import swag_from
from flask_jwt_extended import jwt_required

from app.controllers.calendar_controller import calendar_events_controller

calendar_bp = Blueprint("calendar", __name__)


@calendar_bp.get("/calendar/events")
@jwt_required()
@swag_from({"tags": ["Calendar"], "summary": "Get calendar events (tests, quiz deadlines, class schedules)", "security": [{"BearerAuth": []}]})
def calendar_events_route():
    return calendar_events_controller()
