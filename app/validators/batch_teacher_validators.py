from app.core.exceptions import ValidationError


def validate_assign_teacher_payload(payload):
    if not isinstance(payload, dict):
        raise ValidationError("Invalid request payload")

    teacher_id = payload.get("teacher_id")
    if teacher_id is None:
        raise ValidationError("teacher_id is required")

    try:
        teacher_id = int(teacher_id)
    except (TypeError, ValueError) as exc:
        raise ValidationError("teacher_id must be an integer") from exc

    return {"teacher_id": teacher_id}
