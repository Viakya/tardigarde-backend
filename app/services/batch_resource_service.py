from app.core.exceptions import AuthenticationError, ValidationError
from app.extensions import db
from app.models import Batch, BatchResource, Student, Teacher


RESOURCE_UPDATABLE_FIELDS = {"title", "description", "url", "resource_type", "visible_to_students"}


def _get_active_batch(batch_id):
    batch = Batch.query.filter_by(id=batch_id, is_active=True).first()
    if not batch:
        raise ValidationError("Batch not found", 404)
    return batch


def _get_active_resource(resource_id):
    resource = BatchResource.query.filter_by(id=resource_id).first()
    if not resource:
        raise ValidationError("Resource not found", 404)
    return resource


def _get_teacher_for_user(user_id):
    teacher = Teacher.query.filter_by(user_id=user_id, is_active=True).first()
    if not teacher:
        raise ValidationError("Teacher profile not found", 404)
    return teacher


def _get_student_for_user(user_id):
    student = Student.query.filter_by(user_id=user_id, is_active=True).first()
    if not student:
        raise ValidationError("Student profile not found", 404)
    return student


def _ensure_teacher_assigned(batch, user_id):
    teacher = _get_teacher_for_user(user_id)
    if teacher not in batch.teachers:
        raise AuthenticationError("You are not assigned to this batch", 403)


def _ensure_student_in_batch(batch_id, user_id):
    student = _get_student_for_user(user_id)
    if student.batch_id != batch_id:
        raise AuthenticationError("You are not assigned to this batch", 403)
    return student


def list_batch_resources(batch_id, current_user_id, role, include_hidden=False):
    batch = _get_active_batch(batch_id)
    role = (role or "").lower()

    if role == "coach":
        _ensure_teacher_assigned(batch, current_user_id)
    elif role == "student":
        _ensure_student_in_batch(batch_id, current_user_id)
    elif role not in {"admin", "director", "manager"}:
        raise AuthenticationError("You do not have permission to access this resource", 403)

    query = BatchResource.query.filter_by(batch_id=batch.id)
    if role == "student" or not include_hidden:
        query = query.filter(BatchResource.visible_to_students.is_(True))

    resources = query.order_by(BatchResource.created_at.desc(), BatchResource.id.desc()).all()
    return {
        "batch": batch.to_dict(),
        "resources": [resource.to_dict() for resource in resources],
    }


def create_batch_resource(batch_id, data, current_user_id, role):
    batch = _get_active_batch(batch_id)
    role = (role or "").lower()

    if role == "coach":
        _ensure_teacher_assigned(batch, current_user_id)
    elif role not in {"admin", "director", "manager"}:
        raise AuthenticationError("You do not have permission to create resources", 403)

    resource = BatchResource(
        batch_id=batch.id,
        title=data["title"],
        description=data.get("description"),
        url=data["url"],
        resource_type=data.get("resource_type", "link"),
        created_by=current_user_id,
        visible_to_students=data.get("visible_to_students", True),
    )

    db.session.add(resource)
    db.session.commit()
    return resource


def update_batch_resource(resource_id, data, current_user_id, role):
    resource = _get_active_resource(resource_id)
    batch = _get_active_batch(resource.batch_id)
    role = (role or "").lower()

    if role == "coach":
        _ensure_teacher_assigned(batch, current_user_id)
        if resource.created_by != current_user_id:
            raise AuthenticationError("You can only edit resources you created", 403)
    elif role not in {"admin", "director", "manager"}:
        raise AuthenticationError("You do not have permission to update resources", 403)

    invalid_fields = set(data.keys()) - RESOURCE_UPDATABLE_FIELDS
    if invalid_fields:
        raise ValidationError(f"Cannot update protected fields: {', '.join(sorted(invalid_fields))}")

    for key, value in data.items():
        setattr(resource, key, value)

    db.session.commit()
    return resource


def delete_batch_resource(resource_id, current_user_id, role):
    resource = _get_active_resource(resource_id)
    batch = _get_active_batch(resource.batch_id)
    role = (role or "").lower()

    if role == "coach":
        _ensure_teacher_assigned(batch, current_user_id)
        if resource.created_by != current_user_id:
            raise AuthenticationError("You can only delete resources you created", 403)
    elif role not in {"admin", "director", "manager"}:
        raise AuthenticationError("You do not have permission to delete resources", 403)

    db.session.delete(resource)
    db.session.commit()
