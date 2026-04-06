from sqlalchemy import case, func, text

from app.extensions import db
from app.models import Attendance, Batch, FeePayment, Salary, Student, Teacher, User


def _month_expr(col):
    """Return a month-grouping expression that works on both SQLite and PostgreSQL."""
    dialect = db.engine.dialect.name
    if dialect == "sqlite":
        return func.strftime("%Y-%m", col)
    # PostgreSQL (and compatible)
    return func.date_trunc("month", col)


def get_monthly_attendance_percentage(year=None, batch_id=None):
    month_expr = _month_expr(Attendance.attendance_date)

    query = db.session.query(
        month_expr.label("month_start"),
        func.count(Attendance.id).label("total_records"),
        func.sum(case((Attendance.status == "present", 1), else_=0)).label("present_count"),
        func.sum(case((Attendance.status == "late", 1), else_=0)).label("late_count"),
        func.sum(case((Attendance.status == "absent", 1), else_=0)).label("absent_count"),
    ).filter(Attendance.is_active.is_(True))

    if year is not None:
        query = query.filter(func.extract("year", Attendance.attendance_date) == year)

    if batch_id is not None:
        query = query.filter(Attendance.batch_id == batch_id)

    rows = query.group_by(month_expr).order_by(month_expr.asc()).all()

    result = []
    for row in rows:
        total = int(row.total_records or 0)
        present = int(row.present_count or 0)
        late = int(row.late_count or 0)
        absent = int(row.absent_count or 0)

        attendance_percentage = (present / total * 100) if total > 0 else 0.0

        result.append(
            {
                "month": row.month_start if isinstance(row.month_start, str) else (row.month_start.strftime("%Y-%m") if row.month_start else None),
                "total_records": total,
                "present_count": present,
                "late_count": late,
                "absent_count": absent,
                "attendance_percentage": round(attendance_percentage, 2),
            }
        )

    return {
        "year": year,
        "batch_id": batch_id,
        "monthly_attendance": result,
    }


def get_revenue_by_month(year=None):
    month_expr = _month_expr(FeePayment.payment_date)

    query = db.session.query(
        month_expr.label("month_start"),
        func.count(FeePayment.id).label("payments_count"),
        func.coalesce(func.sum(FeePayment.amount), 0).label("revenue"),
    )

    if year is not None:
        query = query.filter(func.extract("year", FeePayment.payment_date) == year)

    rows = query.group_by(month_expr).order_by(month_expr.asc()).all()

    return {
        "year": year,
        "monthly_revenue": [
            {
                "month": row.month_start if isinstance(row.month_start, str) else (row.month_start.strftime("%Y-%m") if row.month_start else None),
                "payments_count": int(row.payments_count or 0),
                "revenue": float(row.revenue or 0),
            }
            for row in rows
        ],
    }


def get_salary_expense_by_month(year=None):
    month_expr = _month_expr(Salary.payment_date)

    query = db.session.query(
        month_expr.label("salary_month"),
        func.count(Salary.id).label("salary_records"),
        func.coalesce(func.sum(Salary.amount), 0).label("total_budgeted"),
        func.coalesce(func.sum(Salary.amount), 0).label("total_paid"),
    )

    if year is not None:
        query = query.filter(func.extract("year", Salary.payment_date) == year)

    rows = query.group_by(month_expr).order_by(month_expr.asc()).all()

    return {
        "year": year,
        "monthly_salary_expense": [
            {
                "month": row.salary_month if isinstance(row.salary_month, str) else (row.salary_month.strftime("%Y-%m") if row.salary_month else None),
                "salary_records": int(row.salary_records or 0),
                "total_budgeted": float(row.total_budgeted or 0),
                "total_paid": float(row.total_paid or 0),
                "total_pending": float((row.total_budgeted or 0) - (row.total_paid or 0)),
            }
            for row in rows
        ],
    }


def get_batch_strength_report(include_inactive_students=False):
    active_case = case((Student.is_active.is_(True), 1), else_=0)
    inactive_case = case((Student.is_active.is_(False), 1), else_=0)

    query = (
        db.session.query(
            Batch.id.label("batch_id"),
            Batch.batch_name.label("batch_name"),
            Batch.year.label("year"),
            Batch.is_active.label("batch_is_active"),
            func.count(Student.id).label("total_students"),
            func.coalesce(func.sum(active_case), 0).label("active_students"),
            func.coalesce(func.sum(inactive_case), 0).label("inactive_students"),
        )
        .outerjoin(Student, Student.batch_id == Batch.id)
        .group_by(Batch.id)
        .order_by(Batch.year.desc(), Batch.batch_name.asc())
    )

    rows = query.all()

    result = []
    for row in rows:
        active_students = int(row.active_students or 0)
        inactive_students = int(row.inactive_students or 0)
        total_students = int(row.total_students or 0)

        payload = {
            "batch_id": row.batch_id,
            "batch_name": row.batch_name,
            "year": row.year,
            "batch_is_active": bool(row.batch_is_active),
            "total_students": total_students,
            "active_students": active_students,
            "inactive_students": inactive_students,
        }

        if include_inactive_students or active_students > 0 or total_students == 0:
            result.append(payload)

    return {"batch_strength": result}


def _active_inactive_counts(model):
    active_count = db.session.query(func.count(model.id)).filter(model.is_active.is_(True)).scalar() or 0
    inactive_count = db.session.query(func.count(model.id)).filter(model.is_active.is_(False)).scalar() or 0
    return {
        "active": int(active_count),
        "inactive": int(inactive_count),
        "total": int(active_count + inactive_count),
    }


def get_active_vs_inactive_report():
    return {
        "users": _active_inactive_counts(User),
        "students": _active_inactive_counts(Student),
        "teachers": _active_inactive_counts(Teacher),
        "batches": _active_inactive_counts(Batch),
        "attendance_records": _active_inactive_counts(Attendance),
    }
