from __future__ import annotations

from flask import request
from flask_jwt_extended import get_jwt, get_jwt_identity

from app.core.exceptions import ValidationError
from app.services.calendar_service import get_calendar_events
from app.services.export_service import parse_optional_date
from app.utils.response import api_response


def calendar_events_controller():
    current_user_id = get_jwt_identity()
    role = (get_jwt().get("role") or "").lower()

    try:
        normalized_user_id = int(current_user_id)
    except (TypeError, ValueError) as exc:
        raise ValidationError("Invalid user identity") from exc

    start_date = parse_optional_date(request.args.get("start_date"), "start_date")
    end_date = parse_optional_date(request.args.get("end_date"), "end_date")
    batch_id = request.args.get("batch_id", type=int)

    payload = get_calendar_events(
        current_user_id=normalized_user_id,
        role=role,
        start_date=start_date,
        end_date=end_date,
        batch_id=batch_id,
    )
    return api_response(True, "Calendar events fetched successfully", payload, 200)
