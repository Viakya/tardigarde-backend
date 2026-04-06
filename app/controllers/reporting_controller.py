from flask import request

from app.core.exceptions import ValidationError
from app.services.reporting_service import (
    get_active_vs_inactive_report,
    get_batch_strength_report,
    get_monthly_attendance_percentage,
    get_revenue_by_month,
    get_salary_expense_by_month,
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
