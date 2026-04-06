from flask import request

from app.services.admin_service import (
    create_row,
    delete_row,
    get_table_schema,
    list_rows,
    list_tables,
    update_row,
)
from app.utils.response import api_response


def list_tables_controller():
    tables = list_tables()
    return api_response(True, "Tables fetched", {"tables": tables}, 200)


def table_schema_controller(table_name: str):
    schema = get_table_schema(table_name)
    return api_response(True, "Table schema fetched", schema, 200)


def list_rows_controller(table_name: str):
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 25))
    data = list_rows(table_name, page=page, per_page=per_page)
    return api_response(True, "Rows fetched", data, 200)


def create_row_controller(table_name: str):
    payload = request.get_json(silent=True) or {}
    row = create_row(table_name, payload)
    return api_response(True, "Row created", {"row": row}, 201)


def update_row_controller(table_name: str):
    payload = request.get_json(silent=True) or {}
    row = update_row(table_name, payload)
    return api_response(True, "Row updated", {"row": row}, 200)


def delete_row_controller(table_name: str):
    payload = request.get_json(silent=True) or {}
    result = delete_row(table_name, payload)
    return api_response(True, "Row deleted", result, 200)
