from sqlalchemy.exc import IntegrityError
from sqlalchemy import func

from app.core.exceptions import ConflictError, ValidationError
from app.extensions import db
from app.models import Attendance, Batch, FeePayment, Student, Test, TestResult


UPDATABLE_FIELDS = {"batch_name", "year", "start_date", "end_date", "batch_cost", "is_active"}


def create_batch(data):
    existing_batch = Batch.query.filter_by(
        batch_name=data["batch_name"],
        year=data["year"],
    ).first()
    if existing_batch:
        raise ConflictError("Batch already exists for this year")

    batch = Batch(
        batch_name=data["batch_name"],
        year=data["year"],
        start_date=data.get("start_date"),
        end_date=data.get("end_date"),
        batch_cost=data.get("batch_cost", 10000.00),
        is_active=data.get("is_active", True),
    )

    db.session.add(batch)
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ConflictError("Failed to create batch") from exc

    return batch


def get_batch_by_id(batch_id):
    batch = Batch.query.filter_by(id=batch_id, is_active=True).first()
    if not batch:
        raise ValidationError("Batch not found", 404)
    return batch


def list_batches(page=1, per_page=10):
    pagination = (
        Batch.query.filter_by(is_active=True)
        .order_by(Batch.id.desc())
        .paginate(
            page=page,
            per_page=per_page,
            error_out=False,
        )
    )

    return {
        "batches": [batch.to_dict() for batch in pagination.items],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
        },
    }


def update_batch(batch_id, data):
    batch = get_batch_by_id(batch_id)

    invalid_fields = set(data.keys()).difference(UPDATABLE_FIELDS)
    if invalid_fields:
        raise ValidationError(f"Cannot update protected fields: {', '.join(sorted(invalid_fields))}")

    for key, value in data.items():
        setattr(batch, key, value)

    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ConflictError("Failed to update batch") from exc

    return batch


def delete_batch(batch_id):
    batch = get_batch_by_id(batch_id)
    batch.teachers.clear()
    Student.query.filter_by(batch_id=batch.id).update({"batch_id": None})
    Attendance.query.filter_by(batch_id=batch.id).update({"is_active": False})
    tests = Test.query.filter_by(batch_id=batch.id).all()
    if tests:
        test_ids = [test.id for test in tests]
        TestResult.query.filter(TestResult.test_id.in_(test_ids)).update({"is_active": False})
        Test.query.filter_by(batch_id=batch.id).update({"is_active": False})
    batch.is_active = False
    db.session.commit()


def get_batch_profile(batch_id):
    """Get detailed batch profile with financial summary."""
    batch = Batch.query.filter_by(id=batch_id).first()
    if not batch:
        raise ValidationError("Batch not found", 404)
    
    # Get all students in this batch
    students = Student.query.filter_by(batch_id=batch_id, is_active=True).all()
    total_students = len(students)
    
    # Calculate revenue metrics
    batch_cost = float(batch.batch_cost) if batch.batch_cost else 0.0
    total_revenue = batch_cost * total_students
    
    # Calculate discounts
    total_discount_amount = 0.0
    student_details = []
    student_ids = []
    
    for student in students:
        discount_percent = float(student.discount_percent) if student.discount_percent else 0.0
        discount_amount = (batch_cost * discount_percent) / 100
        total_discount_amount += discount_amount
        student_ids.append(student.id)
        
        student_details.append({
            "id": student.id,
            "user_id": student.user_id,
            "full_name": student.user.full_name if student.user else None,
            "email": student.user.email if student.user else None,
            "phone_number": student.phone_number,
            "enrollment_date": student.enrollment_date.isoformat() if student.enrollment_date else None,
            "discount_percent": discount_percent,
            "discount_amount": discount_amount,
            "fee_after_discount": batch_cost - discount_amount,
        })
    
    # Calculate expected revenue after discounts
    expected_revenue = total_revenue - total_discount_amount
    
    # Get total payments received for students in this batch
    total_received = 0.0
    if student_ids:
        result = db.session.query(func.sum(FeePayment.amount)).filter(
            FeePayment.student_id.in_(student_ids)
        ).scalar()
        total_received = float(result) if result else 0.0
    
    # Outstanding amount
    outstanding = expected_revenue - total_received
    
    # Get teachers assigned to this batch
    teacher_details = [
        {
            "id": teacher.id,
            "user_id": teacher.user_id,
            "full_name": teacher.user.full_name if teacher.user else None,
            "email": teacher.user.email if teacher.user else None,
            "phone_number": teacher.phone_number,
            "specialization": teacher.specialization,
        }
        for teacher in batch.teachers
        if teacher.is_active
    ]
    
    return {
        "batch": {
            "id": batch.id,
            "batch_name": batch.batch_name,
            "year": batch.year,
            "batch_cost": batch_cost,
            "start_date": batch.start_date.isoformat() if batch.start_date else None,
            "end_date": batch.end_date.isoformat() if batch.end_date else None,
            "is_active": batch.is_active,
            "created_at": batch.created_at.isoformat() if batch.created_at else None,
            "updated_at": batch.updated_at.isoformat() if batch.updated_at else None,
        },
        "financial_summary": {
            "batch_cost": batch_cost,
            "total_students": total_students,
            "total_revenue": total_revenue,  # batch_cost * total_students
            "total_discount_amount": total_discount_amount,
            "expected_revenue": expected_revenue,  # total_revenue - total_discount_amount
            "total_received": total_received,  # sum of all payments
            "outstanding": outstanding,  # expected_revenue - total_received
        },
        "students": student_details,
        "teachers": teacher_details,
    }
