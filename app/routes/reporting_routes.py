from flask import Blueprint
from flasgger import swag_from

from app.controllers.reporting_controller import (
    active_vs_inactive_controller,
    batch_strength_controller,
    monthly_attendance_report_controller,
    revenue_by_month_controller,
    risk_summary_controller,
    salary_expense_by_month_controller,
    smart_nudges_controller,
)
from app.utils.auth import roles_required

reports_bp = Blueprint("reports", __name__)


@reports_bp.get("/reports/monthly-attendance")
@roles_required("admin", "director", "manager", "coach")
@swag_from({"tags": ["Reports"], "summary": "Get monthly attendance percentage report", "security": [{"BearerAuth": []}]})
def monthly_attendance_report_route():
    return monthly_attendance_report_controller()


@reports_bp.get("/reports/revenue-by-month")
@roles_required("admin", "director", "manager")
@swag_from({"tags": ["Reports"], "summary": "Get monthly revenue report", "security": [{"BearerAuth": []}]})
def revenue_by_month_route():
    return revenue_by_month_controller()


@reports_bp.get("/reports/salary-expense-by-month")
@roles_required("admin", "director", "manager")
@swag_from({"tags": ["Reports"], "summary": "Get salary expense by month report", "security": [{"BearerAuth": []}]})
def salary_expense_by_month_route():
    return salary_expense_by_month_controller()


@reports_bp.get("/reports/batch-strength")
@roles_required("admin", "director", "manager", "coach")
@swag_from({"tags": ["Reports"], "summary": "Get batch strength report", "security": [{"BearerAuth": []}]})
def batch_strength_route():
    return batch_strength_controller()


@reports_bp.get("/reports/active-vs-inactive")
@roles_required("admin", "director", "manager")
@swag_from({"tags": ["Reports"], "summary": "Get active vs inactive report across modules", "security": [{"BearerAuth": []}]})
def active_vs_inactive_route():
    return active_vs_inactive_controller()


@reports_bp.get("/reports/risk-summary")
@roles_required("admin", "director", "manager")
@swag_from({"tags": ["Reports"], "summary": "Get director risk summary", "security": [{"BearerAuth": []}]})
def risk_summary_route():
    return risk_summary_controller()


@reports_bp.get("/reports/smart-nudges")
@roles_required("admin", "director", "manager")
@swag_from({"tags": ["Reports"], "summary": "Get smart nudges", "security": [{"BearerAuth": []}]})
def smart_nudges_route():
    return smart_nudges_controller()
