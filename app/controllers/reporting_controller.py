from flask import request

from app.core.exceptions import ValidationError
from app.services.reporting_service import (
    get_active_vs_inactive_report,
    get_batch_strength_report,
    get_director_risk_summary,
    get_monthly_attendance_percentage,
    get_revenue_by_month,
    get_salary_expense_by_month,
    get_smart_nudges,
)
from app.utils.response import api_response


def _parse_year(year_raw):
    if year_raw in (None, ""):
        return None

    try:
        year = int(year_raw)
    except (TypeError, ValueError) as exc:
        raise ValidationError("year must be an integer") from exc

    if year < 2000 or year > 2100:
        raise ValidationError("year must be between 2000 and 2100")

    return year


def monthly_attendance_report_controller():
    year = _parse_year(request.args.get("year"))
    batch_id = request.args.get("batch_id", type=int)

    data = get_monthly_attendance_percentage(year=year, batch_id=batch_id)
    return api_response(True, "Monthly attendance report generated", data, 200)


def revenue_by_month_controller():
    year = _parse_year(request.args.get("year"))
    data = get_revenue_by_month(year=year)
    return api_response(True, "Revenue by month report generated", data, 200)


def salary_expense_by_month_controller():
    year = _parse_year(request.args.get("year"))
    data = get_salary_expense_by_month(year=year)
    return api_response(True, "Salary expense by month report generated", data, 200)


def batch_strength_controller():
    include_inactive_students_raw = (request.args.get("include_inactive_students") or "false").strip().lower()
    include_inactive_students = include_inactive_students_raw in {"1", "true", "yes"}

    data = get_batch_strength_report(include_inactive_students=include_inactive_students)
    return api_response(True, "Batch strength report generated", data, 200)


def active_vs_inactive_controller():
    data = get_active_vs_inactive_report()
    return api_response(True, "Active vs inactive report generated", data, 200)


def risk_summary_controller():
    days = request.args.get("days", default=30, type=int)
    if days is None or days < 1 or days > 365:
        raise ValidationError("days must be between 1 and 365")

    data = get_director_risk_summary(days=days)
    return api_response(True, "Director risk summary generated", data, 200)


def smart_nudges_controller():
    limit = request.args.get("limit", default=8, type=int)
    if limit is None or limit < 1 or limit > 25:
        raise ValidationError("limit must be between 1 and 25")

    data = get_smart_nudges(limit=limit)
    return api_response(True, "Smart nudges generated", data, 200)
