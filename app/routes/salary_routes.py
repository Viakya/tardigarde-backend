from flask import Blueprint
from flasgger import swag_from
from app.controllers.salary_controller import (
    create_salary_controller,
    delete_salary_controller,
    list_salary_controller,
    salary_summary_controller,
    update_salary_controller,
)
from app.utils.auth import roles_required

salary_bp = Blueprint("salary", __name__)


@salary_bp.post("/salaries")
@roles_required("director", "manager")
@swag_from({"tags": ["Salary"], "summary": "Record salary payment", "security": [{"BearerAuth": []}]})
def create_salary_route():
    return create_salary_controller()


@salary_bp.get("/salaries")
@roles_required("admin", "director", "manager", "coach", "student")
@swag_from({"tags": ["Salary"], "summary": "List salary records", "security": [{"BearerAuth": []}]})
def list_salary_route():
    return list_salary_controller()


@salary_bp.put("/salaries/<int:salary_id>")
@roles_required("director", "manager")
@swag_from({"tags": ["Salary"], "summary": "Update salary record", "security": [{"BearerAuth": []}]})
def update_salary_route(salary_id):
    return update_salary_controller(salary_id)


@salary_bp.delete("/salaries/<int:salary_id>")
@roles_required("director", "manager")
@swag_from({"tags": ["Salary"], "summary": "Delete salary record", "security": [{"BearerAuth": []}]})
def delete_salary_route(salary_id):
    return delete_salary_controller(salary_id)


@salary_bp.get("/salaries/summary")
@roles_required("director", "manager")
@swag_from({"tags": ["Salary"], "summary": "Get salary summary", "security": [{"BearerAuth": []}]})
def salary_summary_route():
    return salary_summary_controller()
