from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, Tuple

from sqlalchemy import and_, func, select
from sqlalchemy.sql.sqltypes import Boolean, Date, DateTime, Float, Integer, Numeric
from werkzeug.security import generate_password_hash

from app.core.exceptions import ValidationError
from app.extensions import db
from app.models import (
    Attendance,
    Batch,
    FeePayment,
    Salary,
    Student,
    Teacher,
    Test,
    TestResult,
    User,
)
from app.models.associations import batch_teachers, parent_students
from app.services.batch_service import delete_batch
from app.services.student_service import delete_student
from app.services.teacher_service import delete_teacher
from app.services.auth_service import delete_user

TABLE_REGISTRY = {
    "users": User,
    "students": Student,
    "batches": Batch,
    "teachers": Teacher,
    "attendance": Attendance,
    "fee_payments": FeePayment,
    "salaries": Salary,
    "tests": Test,
    "test_results": TestResult,
    "batch_teachers": batch_teachers,
    "parent_students": parent_students,
}


def list_tables() -> list[dict[str, Any]]:
    tables = []
    for name, model in TABLE_REGISTRY.items():
        _model, table, _is_model = _resolve_table(name)
        tables.append(
            {
                "name": name,
                "label": name.replace("_", " ").title(),
                "primary_key": [col.name for col in table.primary_key.columns],
                "columns": _serialize_columns(table),
            }
        )
    return tables


def get_table_schema(table_name: str) -> dict[str, Any]:
    _model, table, _is_model = _resolve_table(table_name)
    return {
        "name": table_name,
        "label": table_name.replace("_", " ").title(),
        "primary_key": [col.name for col in table.primary_key.columns],
        "columns": _serialize_columns(table),
    }


def list_rows(table_name: str, page: int = 1, per_page: int = 25) -> dict[str, Any]:
    _model, table, _is_model = _resolve_table(table_name)
    page = max(page, 1)
    per_page = max(min(per_page, 200), 1)
    offset = (page - 1) * per_page

    total = db.session.execute(select(func.count()).select_from(table)).scalar() or 0
    rows = db.session.execute(select(table).offset(offset).limit(per_page)).mappings().all()
    return {
        "rows": [dict(row) for row in rows],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


def create_row(table_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    model, table, is_model = _resolve_table(table_name)
    data = _coerce_payload(table, payload)

    if is_model:
        if model is User:
            data = _apply_user_password(data, payload)
        instance = model(**data)
        db.session.add(instance)
        db.session.commit()
        return _fetch_row(table, instance)

    result = db.session.execute(table.insert().values(**data))
    db.session.commit()
    return _fetch_row_by_pk(table, result.inserted_primary_key)


def update_row(table_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    model, table, is_model = _resolve_table(table_name)
    key = payload.get("key") or {}
    data = payload.get("data") or {}

    if not key:
        raise ValidationError("Missing key for update")
    if not data:
        raise ValidationError("Missing data to update")

    key = _coerce_payload(table, key)
    data = _coerce_payload(table, data)

    if is_model:
        query = model.query.filter_by(**key)
        instance = query.first()
        if not instance:
            raise ValidationError("Row not found")
        if model is User:
            data = _apply_user_password(data, payload.get("data") or {})
        for field, value in data.items():
            setattr(instance, field, value)
        db.session.commit()
        return _fetch_row(table, instance)

    update_stmt = table.update().where(_build_where(table, key)).values(**data)
    result = db.session.execute(update_stmt)
    if result.rowcount == 0:
        raise ValidationError("Row not found")
    db.session.commit()
    return _fetch_row_by_key(table, key)


def delete_row(table_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    model, table, is_model = _resolve_table(table_name)
    key = payload.get("key") or payload

    if not key:
        raise ValidationError("Missing key for delete")

    key = _coerce_payload(table, key)

    if is_model:
        if model is User:
            user_id = key.get("id")
            if not user_id:
                raise ValidationError("User id is required for delete")
            delete_user(user_id)
            return {"deleted": True}
        if model is Student:
            student_id = key.get("id")
            if not student_id:
                raise ValidationError("Student id is required for delete")
            delete_student(student_id)
            return {"deleted": True}
        if model is Teacher:
            teacher_id = key.get("id")
            if not teacher_id:
                raise ValidationError("Teacher id is required for delete")
            delete_teacher(teacher_id)
            return {"deleted": True}
        if model is Batch:
            batch_id = key.get("id")
            if not batch_id:
                raise ValidationError("Batch id is required for delete")
            delete_batch(batch_id)
            return {"deleted": True}

    delete_stmt = table.delete().where(_build_where(table, key))
    result = db.session.execute(delete_stmt)
    if result.rowcount == 0:
        raise ValidationError("Row not found")
    db.session.commit()
    return {"deleted": True}


def _resolve_table(table_name: str) -> Tuple[Any, Any, bool]:
    model = TABLE_REGISTRY.get(table_name)
    if model is None:
        raise ValidationError("Unknown or unauthorized table")
    table = model.__table__ if hasattr(model, "__table__") else model
    is_model = hasattr(model, "__mapper__")
    return model, table, is_model


def _serialize_columns(table) -> list[dict[str, Any]]:
    columns = []
    for column in table.columns:
        columns.append(
            {
                "name": column.name,
                "type": str(column.type).upper(),
                "nullable": column.nullable,
                "primary_key": column.primary_key,
                "autoincrement": bool(column.autoincrement),
                "has_default": bool(column.default or column.server_default),
            }
        )
    return columns


def _coerce_payload(table, payload: dict[str, Any]) -> dict[str, Any]:
    column_map = {col.name: col for col in table.columns}
    coerced: dict[str, Any] = {}
    for key, value in payload.items():
        if key not in column_map:
            continue
        column = column_map[key]
        coerced[key] = _coerce_value(value, column)
    return coerced


def _coerce_value(value: Any, column) -> Any:
    if value == "":
        return None
    if value is None:
        return None

    col_type = column.type
    if isinstance(col_type, Boolean):
        if isinstance(value, str):
            return value.strip().lower() in {"true", "1", "yes"}
        return bool(value)
    if isinstance(col_type, Integer):
        return int(value)
    if isinstance(col_type, Float):
        return float(value)
    if isinstance(col_type, Numeric):
        return Decimal(str(value))
    if isinstance(col_type, Date):
        if isinstance(value, date):
            return value
        return date.fromisoformat(str(value))
    if isinstance(col_type, DateTime):
        if isinstance(value, datetime):
            return value
        text = str(value)
        if text.endswith("Z"):
            text = text[:-1]
        return datetime.fromisoformat(text)
    return value


def _build_where(table, key: dict[str, Any]):
    if not key:
        raise ValidationError("Missing key fields")
    return and_(*[table.c[field] == value for field, value in key.items()])


def _fetch_row(table, instance) -> dict[str, Any]:
    pk_values = [getattr(instance, column.name) for column in table.primary_key.columns]
    return _fetch_row_by_pk(table, pk_values)


def _fetch_row_by_pk(table, pk_values: list[Any] | tuple[Any, ...]) -> dict[str, Any]:
    if not table.primary_key.columns:
        return {}
    pk_columns = list(table.primary_key.columns)
    if len(pk_columns) != len(pk_values):
        raise ValidationError("Invalid primary key for fetch")
    where_clause = and_(*[col == value for col, value in zip(pk_columns, pk_values)])
    row = db.session.execute(select(table).where(where_clause)).mappings().first()
    return dict(row) if row else {}


def _fetch_row_by_key(table, key: dict[str, Any]) -> dict[str, Any]:
    row = db.session.execute(select(table).where(_build_where(table, key))).mappings().first()
    return dict(row) if row else {}


def _apply_user_password(data: dict[str, Any], raw_payload: dict[str, Any]) -> dict[str, Any]:
    if "password" in raw_payload and raw_payload["password"]:
        password = raw_payload["password"]
        data = dict(data)
        data.pop("password", None)
        data["password_hash"] = generate_password_hash(password)
    return data
