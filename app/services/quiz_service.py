from datetime import datetime
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import AuthenticationError, ConflictError, ValidationError
from app.extensions import db
from app.models import Batch, Quiz, QuizAnswer, QuizQuestion, QuizSubmission, Student, Teacher
from app.services.ai_service import generate_quiz_structure


QUESTION_MAX = 50


def _normalize_ai_questions(questions):
    normalized = []
    for item in questions or []:
        if not isinstance(item, dict):
            continue
        question_text = str(item.get("question") or "").strip()
        options = item.get("options")
        if not question_text or not isinstance(options, list) or len(options) != 4:
            continue
        options = [str(opt).strip() for opt in options]
        correct_index = item.get("correct_index")
        try:
            correct_index = int(correct_index)
        except (TypeError, ValueError):
            continue
        if correct_index not in range(4):
            continue
        explanation = item.get("explanation")
        normalized.append(
            {
                "question": question_text,
                "options": options,
                "correct_index": correct_index,
                "explanation": explanation if isinstance(explanation, str) else None,
            }
        )
    return normalized


def _get_active_batch(batch_id):
    batch = Batch.query.filter_by(id=batch_id, is_active=True).first()
    if not batch:
        raise ValidationError("Batch not found", 404)
    return batch


def _get_quiz(quiz_id):
    quiz = Quiz.query.filter_by(id=quiz_id).first()
    if not quiz:
        raise ValidationError("Quiz not found", 404)
    return quiz


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


def generate_ai_quiz(topic, instructions, difficulty, question_count):
    if question_count < 1 or question_count > QUESTION_MAX:
        raise ValidationError("question_count must be between 1 and 50")

    max_attempts = 3
    attempts = 0
    normalized_questions = []
    seen = set()
    title = None
    parsed_difficulty = None

    while len(normalized_questions) < question_count and attempts < max_attempts:
        remaining = question_count - len(normalized_questions)
        attempt_instructions = instructions or ""
        if normalized_questions:
            sample_existing = "; ".join(q["question"] for q in normalized_questions[:10])
            attempt_instructions = (attempt_instructions + " Avoid repeating these questions: " + sample_existing + ".").strip()

        parsed = generate_quiz_structure(topic, attempt_instructions, difficulty, remaining)
        title = title or parsed.get("title") or topic
        parsed_difficulty = parsed_difficulty or parsed.get("difficulty") or difficulty
        questions = parsed.get("questions") or []
        if not isinstance(questions, list) or not questions:
            attempts += 1
            continue

        for item in _normalize_ai_questions(questions):
            key = item["question"].strip().lower()
            if key in seen:
                continue
            seen.add(key)
            normalized_questions.append(item)
            if len(normalized_questions) >= question_count:
                break

        attempts += 1

    if not normalized_questions:
        raise ValidationError("AI returned invalid question list", 502)

    if len(normalized_questions) > question_count:
        normalized_questions = normalized_questions[:question_count]

    return {
        "title": str(title).strip() or topic,
        "difficulty": str(parsed_difficulty or difficulty).lower(),
        "questions": normalized_questions,
        "warning": "AI returned fewer questions than requested" if len(normalized_questions) < question_count else None,
    }


def create_quiz(data, current_user_id, role):
    batch = _get_active_batch(data["batch_id"])
    role = (role or "").lower()

    if role == "coach":
        _ensure_teacher_assigned(batch, current_user_id)
    elif role not in {"admin", "director", "manager"}:
        raise AuthenticationError("You do not have permission to create quizzes", 403)

    marks_per_q = Decimal("100") / Decimal(str(len(data["questions"])))

    quiz = Quiz(
        batch_id=batch.id,
        title=data["title"],
        description=data.get("description"),
        difficulty=data.get("difficulty", "medium"),
        total_marks=100,
        question_count=len(data["questions"]),
        mode=data.get("mode", "practice"),
        status="draft",
        created_by=current_user_id,
    )

    for item in data["questions"]:
        correct_option = chr(ord("A") + item["correct_index"])
        quiz.questions.append(
            QuizQuestion(
                question_text=item["question"],
                option_a=item["options"][0],
                option_b=item["options"][1],
                option_c=item["options"][2],
                option_d=item["options"][3],
                correct_option=correct_option,
                explanation=item.get("explanation"),
                marks=marks_per_q,
            )
        )

    db.session.add(quiz)
    db.session.commit()
    return quiz


def list_quizzes(batch_id, current_user_id, role):
    role = (role or "").lower()
    query = Quiz.query.filter_by(batch_id=batch_id)
    if role == "student":
        student = _ensure_student_in_batch(batch_id, current_user_id)
        query = query.filter(Quiz.status.in_(["published", "closed"]))
    elif role == "coach":
        batch = _get_active_batch(batch_id)
        _ensure_teacher_assigned(batch, current_user_id)
    elif role not in {"admin", "director", "manager"}:
        raise AuthenticationError("You do not have permission to view quizzes", 403)

    quizzes = query.order_by(Quiz.created_at.desc()).all()
    payload = [quiz.to_dict() for quiz in quizzes]
    if role == "student":
        if quizzes:
            submissions = QuizSubmission.query.filter(
                QuizSubmission.student_id == student.id,
                QuizSubmission.quiz_id.in_([quiz.id for quiz in quizzes]),
            ).all()
            submissions_map = {sub.quiz_id: sub for sub in submissions}
            for item in payload:
                submission = submissions_map.get(item["id"])
                item["student_submission"] = submission.to_dict() if submission else None
        else:
            for item in payload:
                item["student_submission"] = None
    return {"quizzes": payload}


def get_quiz_detail(quiz_id, current_user_id, role, include_questions=True):
    quiz = _get_quiz(quiz_id)
    role = (role or "").lower()
    student = None

    if role == "student":
        student = _ensure_student_in_batch(quiz.batch_id, current_user_id)
        if quiz.status not in {"published", "closed"}:
            raise AuthenticationError("Quiz is not available", 403)
    elif role == "coach":
        _ensure_teacher_assigned(quiz.batch, current_user_id)
    elif role not in {"admin", "director", "manager"}:
        raise AuthenticationError("You do not have permission to view quizzes", 403)

    payload = quiz.to_dict(include_questions=include_questions)
    if role == "student" and include_questions:
        submission = None
        if student:
            submission = QuizSubmission.query.filter_by(quiz_id=quiz.id, student_id=student.id).first()
        answers_map = {}
        if submission:
            answers_map = {answer.question_id: answer.selected_option for answer in submission.answers}
        payload["student_submission"] = submission.to_dict() if submission else None
        show_correct = quiz.mode == "graded" and quiz.status == "closed"
        show_explanation = show_correct or (quiz.mode == "practice" and submission is not None)
        for question in payload.get("questions", []):
            question["student_answer"] = answers_map.get(question.get("id"))
            if not show_correct:
                question.pop("correct_option", None)
            if not show_explanation:
                question.pop("explanation", None)
    return payload


def update_quiz(quiz_id, data, current_user_id, role):
    quiz = _get_quiz(quiz_id)
    role = (role or "").lower()

    if role == "coach":
        _ensure_teacher_assigned(quiz.batch, current_user_id)
        if quiz.created_by != current_user_id:
            raise AuthenticationError("You can only edit quizzes you created", 403)
    elif role not in {"admin", "director", "manager"}:
        raise AuthenticationError("You do not have permission to update quizzes", 403)

    for key, value in data.items():
        setattr(quiz, key, value)

    db.session.commit()
    return quiz


def update_quiz_questions(quiz_id, questions, current_user_id, role):
    quiz = _get_quiz(quiz_id)
    role = (role or "").lower()

    if role == "coach":
        _ensure_teacher_assigned(quiz.batch, current_user_id)
        if quiz.created_by != current_user_id:
            raise AuthenticationError("You can only edit quizzes you created", 403)
    elif role not in {"admin", "director", "manager"}:
        raise AuthenticationError("You do not have permission to update quizzes", 403)

    quiz.questions.clear()
    marks_per_q = Decimal("100") / Decimal(str(len(questions)))
    for item in questions:
        correct_option = chr(ord("A") + item["correct_index"])
        quiz.questions.append(
            QuizQuestion(
                question_text=item["question"],
                option_a=item["options"][0],
                option_b=item["options"][1],
                option_c=item["options"][2],
                option_d=item["options"][3],
                correct_option=correct_option,
                explanation=item.get("explanation"),
                marks=marks_per_q,
            )
        )

    quiz.question_count = len(questions)
    quiz.total_marks = 100
    db.session.commit()
    return quiz


def publish_quiz(quiz_id, current_user_id, role):
    quiz = _get_quiz(quiz_id)
    role = (role or "").lower()

    if role == "coach":
        _ensure_teacher_assigned(quiz.batch, current_user_id)
        if quiz.created_by != current_user_id:
            raise AuthenticationError("You can only publish quizzes you created", 403)
    elif role not in {"admin", "director", "manager"}:
        raise AuthenticationError("You do not have permission to publish quizzes", 403)

    quiz.status = "published"
    quiz.open_at = quiz.open_at or datetime.utcnow()
    quiz.published_at = datetime.utcnow()
    db.session.commit()
    return quiz


def close_quiz(quiz_id, current_user_id, role):
    quiz = _get_quiz(quiz_id)
    role = (role or "").lower()

    if role == "coach":
        _ensure_teacher_assigned(quiz.batch, current_user_id)
        if quiz.created_by != current_user_id:
            raise AuthenticationError("You can only close quizzes you created", 403)
    elif role not in {"admin", "director", "manager"}:
        raise AuthenticationError("You do not have permission to close quizzes", 403)

    quiz.status = "closed"
    quiz.close_at = quiz.close_at or datetime.utcnow()
    quiz.closed_at = datetime.utcnow()

    if quiz.mode == "graded":
        student_ids = [s.id for s in Student.query.filter_by(batch_id=quiz.batch_id, is_active=True).all()]
        if student_ids:
            submitted_ids = {
                row.student_id
                for row in QuizSubmission.query.filter(
                    QuizSubmission.quiz_id == quiz.id,
                    QuizSubmission.student_id.in_(student_ids),
                ).all()
            }
            missing = [student_id for student_id in student_ids if student_id not in submitted_ids]
            for student_id in missing:
                submission = QuizSubmission(
                    quiz_id=quiz.id,
                    student_id=student_id,
                    submitted_at=datetime.utcnow(),
                    score=Decimal("0"),
                    status="auto_zero",
                )
                db.session.add(submission)

    db.session.commit()
    return quiz


def submit_quiz(quiz_id, answers, current_user_id, role):
    role = (role or "").lower()
    if role != "student":
        raise AuthenticationError("Only students can submit quizzes", 403)

    quiz = _get_quiz(quiz_id)
    if quiz.status != "published":
        raise AuthenticationError("Quiz is not open for submissions", 403)

    student = _ensure_student_in_batch(quiz.batch_id, current_user_id)

    existing = QuizSubmission.query.filter_by(quiz_id=quiz.id, student_id=student.id).first()

    questions_map = {q.id: q for q in quiz.questions}
    if not questions_map:
        raise ValidationError("Quiz has no questions")

    total_score = Decimal("0")
    if existing:
        submission = existing
        submission.submitted_at = datetime.utcnow()
        submission.status = "submitted"
        submission.score = None
        submission.answers.clear()
    else:
        submission = QuizSubmission(
            quiz_id=quiz.id,
            student_id=student.id,
            submitted_at=datetime.utcnow(),
            status="submitted",
        )
        db.session.add(submission)

    for answer in answers:
        question = questions_map.get(answer["question_id"])
        if not question:
            raise ValidationError("Invalid question_id")
        selected = answer["selected_option"]
        is_correct = selected.upper() == question.correct_option
        marks_awarded = question.marks if is_correct else Decimal("0")
        total_score += Decimal(marks_awarded or 0)

        submission.answers.append(
            QuizAnswer(
                question_id=question.id,
                selected_option=selected.upper(),
                is_correct=is_correct,
                marks_awarded=marks_awarded,
            )
        )

    submission.score = total_score

    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ConflictError("Failed to submit quiz") from exc

    return submission


def delete_quiz(quiz_id, current_user_id, role):
    quiz = _get_quiz(quiz_id)
    role = (role or "").lower()

    if role == "coach":
        _ensure_teacher_assigned(quiz.batch, current_user_id)
        if quiz.created_by != current_user_id:
            raise AuthenticationError("You can only delete quizzes you created", 403)
    elif role not in {"admin", "director", "manager"}:
        raise AuthenticationError("You do not have permission to delete quizzes", 403)

    db.session.delete(quiz)
    db.session.commit()
