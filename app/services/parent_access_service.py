from app.extensions import db
from app.core.exceptions import ValidationError
from app.models import Student, User


def validate_parent_users(parent_user_ids):
    if parent_user_ids is None:
        return []

    parents = User.query.filter(User.id.in_(parent_user_ids), User.is_active.is_(True)).all()
    found_ids = {parent.id for parent in parents}
    missing_ids = sorted(set(parent_user_ids) - found_ids)
    if missing_ids:
        raise ValidationError(f"Parent user(s) not found: {', '.join(str(item) for item in missing_ids)}", 404)

    invalid_role_ids = sorted(parent.id for parent in parents if (parent.role or "").lower() != "parent")
    if invalid_role_ids:
        raise ValidationError(
            "All parent_user_ids must belong to users with role 'parent': "
            + ", ".join(str(item) for item in invalid_role_ids)
        )

    return parents


def get_parent_linked_student_ids(parent_user_id):
    rows = (
        db.session.query(Student.id)
        .join(Student.parents)
        .filter(
            User.id == parent_user_id,
            User.is_active.is_(True),
            db.func.lower(User.role) == "parent",
            Student.is_active.is_(True),
        )
        .all()
    )
    return {student_id for (student_id,) in rows}


def is_parent_allowed_student(parent_user_id, student_id):
    return student_id in get_parent_linked_student_ids(parent_user_id)
