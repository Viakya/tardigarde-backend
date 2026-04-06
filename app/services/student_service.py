from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, ValidationError
from app.extensions import db
from app.models import Attendance, Batch, Student, TestResult, User
from app.services.parent_access_service import validate_parent_users


UPDATABLE_FIELDS = {"batch_id", "phone_number", "address", "date_of_birth", "enrollment_date", "discount_percent", "is_active"}


def create_student(data):
    user = db.session.get(User, data["user_id"])
    if not user:
        raise ValidationError("User not found", 404)

    if user.role.lower() != "student":
        raise ValidationError("User role must be student to create a student profile")

    existing_profile = Student.query.filter_by(user_id=user.id).first()
    if existing_profile:
        raise ConflictError("Student profile already exists for this user")

    batch_id = data.get("batch_id")
    if batch_id is not None:
        batch = Batch.query.filter_by(id=batch_id, is_active=True).first()
        if not batch:
            raise ValidationError("Batch not found", 404)

    student = Student(
        user_id=user.id,
        batch_id=batch_id,
        phone_number=data.get("phone_number"),
        address=data.get("address"),
        date_of_birth=data.get("date_of_birth"),
        enrollment_date=data.get("enrollment_date"),
        discount_percent=data.get("discount_percent", 0),
        is_active=data.get("is_active", True),
    )

    parent_user_ids = data.get("parent_user_ids")
    if parent_user_ids is not None:
        student.parents = validate_parent_users(parent_user_ids)

    db.session.add(student)
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ConflictError("Failed to create student profile") from exc

    return student


def get_student_by_id(student_id):
    student = Student.query.filter_by(id=student_id, is_active=True).first()
    if not student:
        raise ValidationError("Student not found", 404)
    return student


def get_student_by_user_id(user_id):
    student = Student.query.filter_by(user_id=user_id, is_active=True).first()
    if not student:
        raise ValidationError("Student profile not found", 404)
    return student


def list_students(page=1, per_page=10):
    pagination = (
        Student.query.filter_by(is_active=True)
        .order_by(Student.id.desc())
        .paginate(
            page=page,
            per_page=per_page,
            error_out=False,
        )
    )

    return {
        "students": [student.to_dict() for student in pagination.items],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
        },
    }


def update_student(student_id, data):
    student = get_student_by_id(student_id)

    invalid_fields = set(data.keys()).difference(UPDATABLE_FIELDS)
    if invalid_fields:
        raise ValidationError(f"Cannot update protected fields: {', '.join(sorted(invalid_fields))}")

    if "batch_id" in data and data["batch_id"] is not None:
        batch = Batch.query.filter_by(id=data["batch_id"], is_active=True).first()
        if not batch:
            raise ValidationError("Batch not found", 404)

    if "parent_user_ids" in data:
        student.parents = validate_parent_users(data.get("parent_user_ids"))

    for key, value in data.items():
        if key == "parent_user_ids":
            continue
        setattr(student, key, value)

    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ConflictError("Failed to update student profile") from exc

    return student


def delete_student(student_id):
    student = get_student_by_id(student_id)
    if student.user:
        student.user.is_active = False
    student.parents.clear()
    Attendance.query.filter_by(student_id=student.id).update({"is_active": False})
    TestResult.query.filter_by(student_id=student.id).update({"is_active": False})
    student.is_active = False
    db.session.commit()


def connect_parent(student_id, parent_user_id):
    student = get_student_by_id(student_id)

    parent = db.session.get(User, parent_user_id)
    if not parent or not parent.is_active:
        raise ValidationError("Parent user not found", 404)

    if (parent.role or "").lower() != "parent":
        raise ValidationError("User must have role 'parent' to be linked as a parent")

    if parent in student.parents:
        raise ConflictError("Parent is already connected to this student")

    student.parents.append(parent)
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ConflictError("Failed to connect parent") from exc

    return student


def disconnect_parent(student_id, parent_user_id):
    student = get_student_by_id(student_id)

    parent = db.session.get(User, parent_user_id)
    if not parent:
        raise ValidationError("Parent user not found", 404)

    if parent not in student.parents:
        raise ValidationError("Parent is not connected to this student")

    student.parents.remove(parent)
    db.session.commit()

    return student
