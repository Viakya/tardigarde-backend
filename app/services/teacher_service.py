from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, ValidationError
from app.extensions import db
from app.models import Salary, Teacher, User
from app.models.associations import batch_teachers


UPDATABLE_FIELDS = {"specialization", "phone_number", "hire_date", "is_active"}


def create_teacher(data):
    user = db.session.get(User, data["user_id"])
    if not user:
        raise ValidationError("User not found", 404)

    if user.role.lower() != "coach":
        raise ValidationError("User role must be coach to create a teacher profile")

    existing_profile = Teacher.query.filter_by(user_id=user.id).first()
    if existing_profile:
        raise ConflictError("Teacher profile already exists for this user")

    teacher = Teacher(
        user_id=user.id,
        specialization=data.get("specialization"),
        phone_number=data.get("phone_number"),
        hire_date=data.get("hire_date"),
        is_active=data.get("is_active", True),
    )

    db.session.add(teacher)
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ConflictError("Failed to create teacher profile") from exc

    return teacher


def get_teacher_by_id(teacher_id):
    teacher = Teacher.query.filter_by(id=teacher_id, is_active=True).first()
    if not teacher:
        raise ValidationError("Teacher not found", 404)
    return teacher


def list_teachers(page=1, per_page=10):
    pagination = (
        Teacher.query.filter_by(is_active=True)
        .order_by(Teacher.id.desc())
        .paginate(
            page=page,
            per_page=per_page,
            error_out=False,
        )
    )

    return {
        "teachers": [teacher.to_dict() for teacher in pagination.items],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
        },
    }


def update_teacher(teacher_id, data):
    teacher = get_teacher_by_id(teacher_id)

    invalid_fields = set(data.keys()).difference(UPDATABLE_FIELDS)
    if invalid_fields:
        raise ValidationError(f"Cannot update protected fields: {', '.join(sorted(invalid_fields))}")

    for key, value in data.items():
        setattr(teacher, key, value)

    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ConflictError("Failed to update teacher profile") from exc

    return teacher


def delete_teacher(teacher_id):
    teacher = Teacher.query.filter_by(id=teacher_id).first()
    if not teacher:
        raise ValidationError("Teacher not found", 404)
    if teacher.user:
        teacher.user.is_active = False
    teacher.batches.clear()
    db.session.execute(
        batch_teachers.delete().where(batch_teachers.c.teacher_id == teacher.id)
    )
    Salary.query.filter_by(teacher_id=teacher.id).delete()
    db.session.delete(teacher)
    db.session.commit()
