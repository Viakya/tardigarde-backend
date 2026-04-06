from flask import request

from app.services.batch_teacher_service import (
    assign_teacher_to_batch,
    list_batches_for_teacher,
    list_teachers_for_batch,
    remove_teacher_from_batch,
)
from app.utils.response import api_response
from app.validators.batch_teacher_validators import validate_assign_teacher_payload


def assign_teacher_to_batch_controller(batch_id):
    payload = request.get_json(silent=True) or {}
    validated = validate_assign_teacher_payload(payload)

    batch, teacher = assign_teacher_to_batch(batch_id=batch_id, teacher_id=validated["teacher_id"])
    return api_response(
        True,
        "Teacher assigned to batch successfully",
        {
            "batch": batch.to_dict(),
            "teacher": teacher.to_dict(),
        },
        201,
    )


def remove_teacher_from_batch_controller(batch_id, teacher_id):
    remove_teacher_from_batch(batch_id=batch_id, teacher_id=teacher_id)
    return api_response(True, "Teacher removed from batch successfully", {}, 200)


def list_teachers_for_batch_controller(batch_id):
    data = list_teachers_for_batch(batch_id=batch_id)
    return api_response(True, "Batch teachers fetched successfully", data, 200)


def list_batches_for_teacher_controller(teacher_id):
    data = list_batches_for_teacher(teacher_id=teacher_id)
    return api_response(True, "Teacher batches fetched successfully", data, 200)
