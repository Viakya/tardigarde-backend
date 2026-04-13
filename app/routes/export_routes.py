from flask import Blueprint
from flasgger import swag_from

from app.controllers.export_controller import (
    export_results_excel_controller,
    export_revenue_pdf_controller,
)
from app.utils.auth import roles_required

exports_bp = Blueprint("exports", __name__)


@exports_bp.get("/reports/export/results.xlsx")
@roles_required("admin", "director", "manager", "coach")
@swag_from({"tags": ["Exports"], "summary": "Export test results as Excel", "security": [{"BearerAuth": []}]})
def export_results_route():
    return export_results_excel_controller()


@exports_bp.get("/reports/export/revenue.pdf")
@roles_required("admin", "director", "manager")
@swag_from({"tags": ["Exports"], "summary": "Export revenue report as PDF", "security": [{"BearerAuth": []}]})
def export_revenue_route():
    return export_revenue_pdf_controller()
