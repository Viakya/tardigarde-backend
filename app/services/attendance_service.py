from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, ValidationError
from app.extensions import db
from app.models import Attendance, Batch, Student, User
from app.services.parent_access_service import get_parent_linked_student_ids


UPDATABLE_FIELDS = {"status", "remarks", "is_active"}
MARKER_ALLOWED_ROLES = {"coach", "director"}


def _get_active_student(student_id):
    student = Student.query.filter_by(id=student_id, is_active=True).first()
    if not student:
        raise ValidationError("Student not found", 404)
    return student


def _get_active_batch(batch_id):
    batch = Batch.query.filter_by(id=batch_id, is_active=True).first()
    if not batch:
        raise ValidationError("Batch not found", 404)
    return batch


def _get_marker(marker_user_id):
    marker = db.session.get(User, marker_user_id)
    if not marker or not marker.is_active:
        raise ValidationError("Marker user not found", 404)

    if (marker.role or "").lower() not in MARKER_ALLOWED_ROLES:
        raise ValidationError("Only coach or director can mark attendance", 403)

    return marker


def create_attendance(data, marker_user_id):
    student = _get_active_student(data["student_id"])
    batch = _get_active_batch(data["batch_id"])
    marker = _get_marker(marker_user_id)

    if student.batch_id != batch.id:
        raise ValidationError("Student is not assigned to the provided batch")

    existing = Attendance.query.filter_by(
        student_id=student.id,
        attendance_date=data["attendance_date"],
    ).first()

    if existing and existing.is_active:
        raise ConflictError("Attendance already marked for this student on this date")

    if existing and not existing.is_active:
        existing.batch_id = batch.id
        existing.status = data["status"]
        existing.marked_by = marker.id
        existing.remarks = data.get("remarks")
        existing.is_active = data.get("is_active", True)
        db.session.commit()
        return existing

    attendance = Attendance(
        student_id=student.id,
        batch_id=batch.id,
        attendance_date=data["attendance_date"],
        status=data["status"],
        marked_by=marker.id,
        remarks=data.get("remarks"),
        is_active=data.get("is_active", True),
    )

    db.session.add(attendance)
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ConflictError("Failed to create attendance") from exc

    return attendance


def get_attendance_by_id(attendance_id, current_user_id=None, current_role=None):
    attendance = Attendance.query.filter_by(id=attendance_id, is_active=True).first()
    if not attendance:
        raise ValidationError("Attendance not found", 404)

    if current_role == "parent":
        if current_user_id is None:
            raise ValidationError("Invalid user identity", 401)

        try:
            parent_user_id = int(current_user_id)
        except (TypeError, ValueError) as exc:
            raise ValidationError("Invalid user identity", 401) from exc

        allowed_student_ids = get_parent_linked_student_ids(parent_user_id)
        if attendance.student_id not in allowed_student_ids:
            raise ValidationError("Attendance not found", 404)

    return attendance


def list_attendance(
    page=1,
    per_page=10,
    student_id=None,
    batch_id=None,
    attendance_date=None,
    current_user_id=None,
    current_role=None,
):
    query = Attendance.query.filter_by(is_active=True)

    if current_role == "parent":
        if current_user_id is None:
            raise ValidationError("Invalid user identity", 401)

        try:
            parent_user_id = int(current_user_id)
        except (TypeError, ValueError) as exc:
            raise ValidationError("Invalid user identity", 401) from exc

        allowed_student_ids = get_parent_linked_student_ids(parent_user_id)
        query = query.filter(Attendance.student_id.in_(allowed_student_ids))

    if student_id is not None:
        query = query.filter(Attendance.student_id == student_id)

    if batch_id is not None:
        query = query.filter(Attendance.batch_id == batch_id)

    if attendance_date is not None:
        query = query.filter(Attendance.attendance_date == attendance_date)

    pagination = query.order_by(Attendance.attendance_date.desc(), Attendance.id.desc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False,
    )

    return {
        "attendance": [record.to_dict() for record in pagination.items],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
        },
    }


def update_attendance(attendance_id, data, marker_user_id):
    _get_marker(marker_user_id)
    attendance = get_attendance_by_id(attendance_id)

    invalid_fields = set(data.keys()).difference(UPDATABLE_FIELDS)
    if invalid_fields:
        raise ValidationError(f"Cannot update protected fields: {', '.join(sorted(invalid_fields))}")

    for key, value in data.items():
        setattr(attendance, key, value)

    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ConflictError("Failed to update attendance") from exc

    return attendance


def delete_attendance(attendance_id):
    attendance = get_attendance_by_id(attendance_id)
    attendance.is_active = False
    db.session.commit()
