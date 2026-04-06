from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, ValidationError
from app.extensions import db
from app.models import Batch, Teacher


def _get_active_batch(batch_id):
    batch = Batch.query.filter_by(id=batch_id, is_active=True).first()
    if not batch:
        raise ValidationError("Batch not found", 404)
    return batch


def _get_active_teacher(teacher_id):
    teacher = Teacher.query.filter_by(id=teacher_id, is_active=True).first()
    if not teacher:
        raise ValidationError("Teacher not found", 404)
    return teacher


def assign_teacher_to_batch(batch_id, teacher_id):
    batch = _get_active_batch(batch_id)
    teacher = _get_active_teacher(teacher_id)

    if teacher in batch.teachers:
        raise ConflictError("Teacher is already assigned to this batch")

    batch.teachers.append(teacher)
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ConflictError("Failed to assign teacher to batch") from exc

    return batch, teacher


def remove_teacher_from_batch(batch_id, teacher_id):
    batch = _get_active_batch(batch_id)
    teacher = _get_active_teacher(teacher_id)

    if teacher not in batch.teachers:
        raise ValidationError("Teacher is not assigned to this batch", 404)

    batch.teachers.remove(teacher)
    db.session.commit()


def list_teachers_for_batch(batch_id):
    batch = _get_active_batch(batch_id)

    teachers = [teacher for teacher in batch.teachers if teacher.is_active]

    return {
        "batch": batch.to_dict(),
        "teachers": [teacher.to_dict() for teacher in teachers],
    }


def list_batches_for_teacher(teacher_id):
    teacher = _get_active_teacher(teacher_id)

    batches = [batch for batch in teacher.batches if batch.is_active]

    return {
        "teacher": teacher.to_dict(),
        "batches": [batch.to_dict() for batch in batches],
    }
