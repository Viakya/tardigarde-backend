from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func

from app.core.exceptions import ValidationError
from app.extensions import db
from app.models import Salary, Teacher, User


def _get_active_teacher(teacher_id):
    teacher = Teacher.query.filter_by(id=teacher_id, is_active=True).first()
    if not teacher:
        raise ValidationError("Teacher not found", 404)
    return teacher


def _get_salary(salary_id):
    salary = Salary.query.filter_by(id=salary_id).first()
    if not salary:
        raise ValidationError("Salary record not found", 404)
    return salary


def create_salary_record(data, paid_by_user_id=None):
    teacher = _get_active_teacher(data["teacher_id"])

    if paid_by_user_id is not None:
        payer = db.session.get(User, paid_by_user_id)
        if not payer or not payer.is_active:
            raise ValidationError("Payer user not found", 404)

    salary = Salary(
        teacher_id=teacher.id,
        amount=data["amount"],
        payment_date=data.get("payment_date") or date.today(),
        payment_method=data.get("payment_method", "cash"),
        reference_no=data.get("reference_no"),
        paid_by=paid_by_user_id,
        remarks=data.get("remarks"),
    )

    db.session.add(salary)
    db.session.commit()
    return salary


def list_salary_records(page=1, per_page=10, teacher_id=None, start_date=None, end_date=None, last_n_payments=None, last_n_months=None):
    query = Salary.query

    if teacher_id is not None:
        query = query.filter(Salary.teacher_id == teacher_id)
    
    # Filter by date range
    if start_date:
        query = query.filter(Salary.payment_date >= start_date)
    if end_date:
        query = query.filter(Salary.payment_date <= end_date)
    
    # Filter by last N months
    if last_n_months:
        months_ago = date.today() - timedelta(days=last_n_months * 30)
        query = query.filter(Salary.payment_date >= months_ago)
    
    # Order by date descending
    query = query.order_by(Salary.payment_date.desc(), Salary.id.desc())
    
    # If last_n_payments is set, limit without pagination
    if last_n_payments:
        salaries = query.limit(last_n_payments).all()
        return {
            "salaries": [salary.to_dict() for salary in salaries],
            "pagination": {
                "page": 1,
                "per_page": last_n_payments,
                "total": len(salaries),
                "pages": 1,
                "has_next": False,
                "has_prev": False,
            },
        }

    pagination = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False,
    )

    return {
        "salaries": [salary.to_dict() for salary in pagination.items],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
        },
    }


def update_salary_record(salary_id, data):
    salary = _get_salary(salary_id)

    if "amount" in data:
        if data["amount"] <= Decimal("0"):
            raise ValidationError("Amount must be greater than 0")
        salary.amount = data["amount"]

    if "payment_date" in data:
        salary.payment_date = data["payment_date"]

    if "payment_method" in data:
        salary.payment_method = data["payment_method"]

    if "reference_no" in data:
        salary.reference_no = data["reference_no"]

    if "remarks" in data:
        salary.remarks = data["remarks"]

    db.session.commit()
    return salary


def delete_salary_record(salary_id):
    salary = _get_salary(salary_id)
    db.session.delete(salary)
    db.session.commit()


def get_salary_summary(teacher_id=None):
    query = Salary.query

    if teacher_id is not None:
        query = query.filter(Salary.teacher_id == teacher_id)

    records = query.all()
    total_paid = sum((Decimal(record.amount or 0) for record in records), Decimal("0"))

    return {
        "teacher_id": teacher_id,
        "total_records": len(records),
        "total_paid": float(total_paid),
    }
