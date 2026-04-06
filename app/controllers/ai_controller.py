from flask import request
from flask_jwt_extended import get_jwt_identity

from app.core.exceptions import ValidationError
from app.services.ai_service import (
    get_coach_batch_ai_insights,
    get_fee_risk_prediction,
    get_operations_ai_summary,
    get_parent_child_ai_summary,
    get_parent_weekly_digest,
)
from app.utils.response import api_response


def operations_ai_summary_controller():
    payload = request.get_json(silent=True) or {}
    year = payload.get("year")
    batch_id = payload.get("batch_id")
    focus = payload.get("focus")

    if year is not None:
        try:
            year = int(year)
        except (TypeError, ValueError):
            return api_response(False, "year must be an integer", {}, 400)

    if batch_id is not None:
        try:
            batch_id = int(batch_id)
        except (TypeError, ValueError):
            return api_response(False, "batch_id must be an integer", {}, 400)

    try:
        data = get_operations_ai_summary(year=year, batch_id=batch_id, focus=focus)
        return api_response(True, "AI operations summary generated", data, 200)
    except ValidationError as exc:
        return api_response(False, exc.message, {}, exc.status_code)
    except Exception as exc:
        return api_response(False, f"Failed to generate AI operations summary: {exc}", {}, 500)


def coach_batch_ai_summary_controller(batch_id):
    payload = request.get_json(silent=True) or {}
    focus = payload.get("focus")

    current_user_id = get_jwt_identity()
    try:
        data = get_coach_batch_ai_insights(
            user_id=current_user_id,
            batch_id=batch_id,
            focus=focus,
        )
        return api_response(True, "AI coach insights generated", data, 200)
    except ValidationError as exc:
        return api_response(False, exc.message, {}, exc.status_code)
    except Exception as exc:
        return api_response(False, f"Failed to generate AI coach insights: {exc}", {}, 500)


def parent_child_ai_summary_controller(student_id):
    payload = request.get_json(silent=True) or {}
    focus = payload.get("focus")

    current_user_id = get_jwt_identity()
    try:
        data = get_parent_child_ai_summary(
            parent_user_id=current_user_id,
            student_id=student_id,
            focus=focus,
        )
        return api_response(True, "AI parent summary generated", data, 200)
    except ValidationError as exc:
        return api_response(False, exc.message, {}, exc.status_code)
    except Exception as exc:
        return api_response(False, f"Failed to generate AI parent summary: {exc}", {}, 500)


def parent_weekly_digest_controller(student_id):
    payload = request.get_json(silent=True) or {}
    focus = payload.get("focus")

    current_user_id = get_jwt_identity()
    try:
        data = get_parent_weekly_digest(
            parent_user_id=current_user_id,
            student_id=student_id,
            focus=focus,
        )
        return api_response(True, "AI parent weekly digest generated", data, 200)
    except ValidationError as exc:
        return api_response(False, exc.message, {}, exc.status_code)
    except Exception as exc:
        return api_response(False, f"Failed to generate AI parent weekly digest: {exc}", {}, 500)


def fee_risk_prediction_controller():
    payload = request.get_json(silent=True) or {}
    year = payload.get("year")
    focus = payload.get("focus")

    if year is not None:
        try:
            year = int(year)
        except (TypeError, ValueError):
            return api_response(False, "year must be an integer", {}, 400)

    try:
        data = get_fee_risk_prediction(year=year, focus=focus)
        return api_response(True, "AI fee risk prediction generated", data, 200)
    except ValidationError as exc:
        return api_response(False, exc.message, {}, exc.status_code)
    except Exception as exc:
        return api_response(False, f"Failed to generate AI fee risk prediction: {exc}", {}, 500)
