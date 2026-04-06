from flask import request
from flask_jwt_extended import get_jwt, get_jwt_identity

from app.core.exceptions import ValidationError
from app.services.quiz_service import (
    close_quiz,
    create_quiz,
    delete_quiz,
    generate_ai_quiz,
    get_quiz_detail,
    list_quizzes,
    publish_quiz,
    submit_quiz,
    update_quiz,
    update_quiz_questions,
)
from app.utils.response import api_response
from app.validators.quiz_validators import (
    validate_ai_generate_quiz_payload,
    validate_create_quiz_payload,
    validate_submit_quiz_payload,
    validate_update_quiz_payload,
    validate_update_quiz_questions_payload,
)


def _get_identity():
    current_user_id = get_jwt_identity()
    try:
        return int(current_user_id)
    except (TypeError, ValueError) as exc:
        raise ValidationError("Invalid user identity") from exc


def generate_ai_quiz_controller():
    payload = request.get_json(silent=True) or {}
    validated = validate_ai_generate_quiz_payload(payload)

    data = generate_ai_quiz(
        topic=validated["topic"],
        instructions=validated.get("instructions"),
        difficulty=validated["difficulty"],
        question_count=validated["question_count"],
    )
    return api_response(True, "AI quiz generated", data, 200)


def create_quiz_controller():
    payload = request.get_json(silent=True) or {}
    validated = validate_create_quiz_payload(payload)
    current_user_id = _get_identity()
    role = (get_jwt().get("role") or "").lower()

    quiz = create_quiz(validated, current_user_id=current_user_id, role=role)
    return api_response(True, "Quiz created successfully", {"quiz": quiz.to_dict(include_questions=True)}, 201)


def list_quizzes_controller(batch_id):
    current_user_id = _get_identity()
    role = (get_jwt().get("role") or "").lower()

    data = list_quizzes(batch_id=batch_id, current_user_id=current_user_id, role=role)
    return api_response(True, "Quizzes fetched successfully", data, 200)


def get_quiz_controller(quiz_id):
    current_user_id = _get_identity()
    role = (get_jwt().get("role") or "").lower()

    quiz = get_quiz_detail(quiz_id=quiz_id, current_user_id=current_user_id, role=role, include_questions=True)
    return api_response(True, "Quiz fetched successfully", {"quiz": quiz}, 200)


def update_quiz_controller(quiz_id):
    payload = request.get_json(silent=True) or {}
    validated = validate_update_quiz_payload(payload)
    current_user_id = _get_identity()
    role = (get_jwt().get("role") or "").lower()

    quiz = update_quiz(quiz_id=quiz_id, data=validated, current_user_id=current_user_id, role=role)
    return api_response(True, "Quiz updated successfully", {"quiz": quiz.to_dict(include_questions=True)}, 200)


def update_quiz_questions_controller(quiz_id):
    payload = request.get_json(silent=True) or {}
    validated = validate_update_quiz_questions_payload(payload)
    current_user_id = _get_identity()
    role = (get_jwt().get("role") or "").lower()

    quiz = update_quiz_questions(
        quiz_id=quiz_id,
        questions=validated["questions"],
        current_user_id=current_user_id,
        role=role,
    )
    return api_response(True, "Quiz questions updated", {"quiz": quiz.to_dict(include_questions=True)}, 200)


def publish_quiz_controller(quiz_id):
    current_user_id = _get_identity()
    role = (get_jwt().get("role") or "").lower()

    quiz = publish_quiz(quiz_id=quiz_id, current_user_id=current_user_id, role=role)
    return api_response(True, "Quiz published", {"quiz": quiz.to_dict()}, 200)


def close_quiz_controller(quiz_id):
    current_user_id = _get_identity()
    role = (get_jwt().get("role") or "").lower()

    quiz = close_quiz(quiz_id=quiz_id, current_user_id=current_user_id, role=role)
    return api_response(True, "Quiz closed", {"quiz": quiz.to_dict()}, 200)


def delete_quiz_controller(quiz_id):
    current_user_id = _get_identity()
    role = (get_jwt().get("role") or "").lower()

    delete_quiz(quiz_id=quiz_id, current_user_id=current_user_id, role=role)
    return api_response(True, "Quiz deleted", {}, 200)


def submit_quiz_controller(quiz_id):
    payload = request.get_json(silent=True) or {}
    validated = validate_submit_quiz_payload(payload)
    current_user_id = _get_identity()
    role = (get_jwt().get("role") or "").lower()

    submission = submit_quiz(quiz_id=quiz_id, answers=validated["answers"], current_user_id=current_user_id, role=role)
    return api_response(True, "Quiz submitted", {"submission": submission.to_dict()}, 201)
