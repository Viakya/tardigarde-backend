from decimal import Decimal, InvalidOperation

from app.core.exceptions import ValidationError


def _normalize_int(value, field_name):
    if value is None:
        raise ValidationError(f"{field_name} is required")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field_name} must be an integer") from exc


def _normalize_str(value, field_name, max_len=None, required=False):
    if value is None:
        if required:
            raise ValidationError(f"{field_name} is required")
        return None
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string")
    value = value.strip()
    if required and not value:
        raise ValidationError(f"{field_name} is required")
    if max_len and len(value) > max_len:
        raise ValidationError(f"{field_name} is too long")
    return value


def _normalize_questions(questions):
    if not isinstance(questions, list) or not questions:
        raise ValidationError("questions must be a non-empty list")

    normalized = []
    for idx, item in enumerate(questions, start=1):
        if not isinstance(item, dict):
            raise ValidationError(f"Question #{idx} must be an object")

        question_text = _normalize_str(item.get("question"), "question", required=True)
        options = item.get("options")
        if not isinstance(options, list) or len(options) != 4:
            raise ValidationError(f"Question #{idx} must have exactly 4 options")
        options = [str(opt).strip() for opt in options]
        if any(not opt for opt in options):
            raise ValidationError(f"Question #{idx} options cannot be empty")

        correct_index = item.get("correct_index")
        try:
            correct_index = int(correct_index)
        except (TypeError, ValueError):
            raise ValidationError(f"Question #{idx} correct_index must be an integer")
        if correct_index not in range(4):
            raise ValidationError(f"Question #{idx} correct_index must be between 0 and 3")

        explanation = item.get("explanation")
        if explanation is not None and not isinstance(explanation, str):
            raise ValidationError(f"Question #{idx} explanation must be a string")

        normalized.append(
            {
                "question": question_text,
                "options": options,
                "correct_index": correct_index,
                "explanation": explanation,
            }
        )

    return normalized


def validate_ai_generate_quiz_payload(payload):
    if not isinstance(payload, dict):
        raise ValidationError("Invalid request payload")

    topic = _normalize_str(payload.get("topic"), "topic", max_len=180, required=True)
    instructions = _normalize_str(payload.get("instructions"), "instructions", max_len=2000)
    difficulty = _normalize_str(payload.get("difficulty"), "difficulty", max_len=20) or "medium"
    question_count = _normalize_int(payload.get("question_count"), "question_count")

    if question_count < 1 or question_count > 50:
        raise ValidationError("question_count must be between 1 and 50")

    mode = _normalize_str(payload.get("mode"), "mode", max_len=20) or "practice"
    if mode not in {"practice", "graded"}:
        raise ValidationError("mode must be 'practice' or 'graded'")

    return {
        "topic": topic,
        "instructions": instructions,
        "difficulty": difficulty.lower(),
        "question_count": question_count,
        "mode": mode,
    }


def validate_create_quiz_payload(payload):
    if not isinstance(payload, dict):
        raise ValidationError("Invalid request payload")

    batch_id = _normalize_int(payload.get("batch_id"), "batch_id")
    title = _normalize_str(payload.get("title"), "title", max_len=180, required=True)
    description = _normalize_str(payload.get("description"), "description", max_len=2000)
    difficulty = _normalize_str(payload.get("difficulty"), "difficulty", max_len=20) or "medium"
    question_count = _normalize_int(payload.get("question_count"), "question_count")
    mode = _normalize_str(payload.get("mode"), "mode", max_len=20) or "practice"
    if mode not in {"practice", "graded"}:
        raise ValidationError("mode must be 'practice' or 'graded'")

    questions = _normalize_questions(payload.get("questions"))
    if len(questions) != question_count:
        raise ValidationError("question_count must match number of questions")

    return {
        "batch_id": batch_id,
        "title": title,
        "description": description,
        "difficulty": difficulty.lower(),
        "question_count": question_count,
        "mode": mode,
        "questions": questions,
    }


def validate_update_quiz_payload(payload):
    if not isinstance(payload, dict):
        raise ValidationError("Invalid request payload")

    result = {}

    if "title" in payload:
        result["title"] = _normalize_str(payload.get("title"), "title", max_len=180, required=True)
    if "description" in payload:
        result["description"] = _normalize_str(payload.get("description"), "description", max_len=2000)
    if "difficulty" in payload:
        result["difficulty"] = _normalize_str(payload.get("difficulty"), "difficulty", max_len=20)
    if "mode" in payload:
        mode = _normalize_str(payload.get("mode"), "mode", max_len=20)
        if mode not in {"practice", "graded"}:
            raise ValidationError("mode must be 'practice' or 'graded'")
        result["mode"] = mode

    if not result:
        raise ValidationError("At least one field is required for update")
    return result


def validate_update_quiz_questions_payload(payload):
    if not isinstance(payload, dict):
        raise ValidationError("Invalid request payload")
    questions = _normalize_questions(payload.get("questions"))
    return {"questions": questions}


def validate_submit_quiz_payload(payload):
    if not isinstance(payload, dict):
        raise ValidationError("Invalid request payload")

    answers = payload.get("answers")
    if not isinstance(answers, list) or not answers:
        raise ValidationError("answers must be a non-empty list")

    normalized = []
    for idx, item in enumerate(answers, start=1):
        if not isinstance(item, dict):
            raise ValidationError(f"Answer #{idx} must be an object")
        question_id = item.get("question_id")
        try:
            question_id = int(question_id)
        except (TypeError, ValueError):
            raise ValidationError(f"Answer #{idx} question_id must be an integer")
        selected_option = item.get("selected_option")
        if not isinstance(selected_option, str) or selected_option.upper() not in {"A", "B", "C", "D"}:
            raise ValidationError(f"Answer #{idx} selected_option must be A/B/C/D")
        normalized.append({"question_id": question_id, "selected_option": selected_option.upper()})

    return {"answers": normalized}
