from __future__ import annotations

from datetime import date, datetime, time, timedelta

from app.core.exceptions import ValidationError
from app.models import Batch, Quiz, Student, Teacher, Test
from app.services.parent_access_service import get_parent_linked_student_ids


def _start_of_day(dt: date) -> datetime:
    return datetime.combine(dt, time.min)


def _end_of_day(dt: date) -> datetime:
    return datetime.combine(dt, time.max)


def _get_accessible_batch_ids(current_user_id: int, role: str) -> set[int] | None:
    normalized_role = (role or "").lower()

    if normalized_role in {"admin", "director", "manager"}:
        return None

    if normalized_role == "coach":
        teacher = Teacher.query.filter_by(user_id=current_user_id, is_active=True).first()
        if not teacher:
            return set()
        return {batch.id for batch in teacher.batches if batch.is_active}

    if normalized_role == "student":
        student = Student.query.filter_by(user_id=current_user_id, is_active=True).first()
        if not student or not student.batch_id:
            return set()
        return {student.batch_id}

    if normalized_role == "parent":
        student_ids = get_parent_linked_student_ids(current_user_id)
        if not student_ids:
            return set()
        students = Student.query.filter(Student.id.in_(student_ids), Student.is_active.is_(True)).all()
        return {student.batch_id for student in students if student.batch_id}

    raise ValidationError("Invalid role for calendar access", 403)


def _append_test_events(events: list[dict], batch_ids: set[int] | None, window_start: date, window_end: date) -> None:
    query = Test.query.filter(
        Test.is_active.is_(True),
        Test.test_date >= window_start,
        Test.test_date <= window_end,
    )

    if batch_ids is not None:
        if not batch_ids:
            return
        query = query.filter(Test.batch_id.in_(batch_ids))

    for test in query.order_by(Test.test_date.asc(), Test.id.asc()).all():
        events.append(
            {
                "id": f"test-{test.id}",
                "type": "test",
                "title": test.title,
                "start": _start_of_day(test.test_date).isoformat(),
                "end": _end_of_day(test.test_date).isoformat(),
                "all_day": True,
                "batch_id": test.batch_id,
                "batch_name": test.batch.batch_name if test.batch else None,
                "meta": {
                    "subject": test.subject,
                    "max_marks": float(test.max_marks) if test.max_marks is not None else None,
                },
            }
        )


def _append_quiz_events(events: list[dict], batch_ids: set[int] | None, window_start: date, window_end: date) -> None:
    query = Quiz.query.filter(
        Quiz.status.in_(["published", "draft", "closed"]),
    )

    if batch_ids is not None:
        if not batch_ids:
            return
        query = query.filter(Quiz.batch_id.in_(batch_ids))

    quizzes = query.order_by(Quiz.id.desc()).all()

    for quiz in quizzes:
        event_start = quiz.open_at or quiz.created_at
        event_end = quiz.close_at or event_start

        if event_start is None:
            continue
        start_day = event_start.date()
        end_day = event_end.date() if event_end else start_day

        if end_day < window_start:
            continue
        if start_day > window_end:
            continue

        events.append(
            {
                "id": f"quiz-{quiz.id}",
                "type": "quiz",
                "title": quiz.title,
                "start": event_start.isoformat() if event_start else None,
                "end": event_end.isoformat() if event_end else None,
                "all_day": False,
                "batch_id": quiz.batch_id,
                "batch_name": quiz.batch.batch_name if quiz.batch else None,
                "meta": {
                    "mode": quiz.mode,
                    "status": quiz.status,
                    "question_count": quiz.question_count,
                    "difficulty": quiz.difficulty,
                },
            }
        )


def _append_batch_schedule_events(events: list[dict], batch_ids: set[int] | None, window_start: date, window_end: date) -> None:
    query = Batch.query.filter(Batch.is_active.is_(True))

    if batch_ids is not None:
        if not batch_ids:
            return
        query = query.filter(Batch.id.in_(batch_ids))

    batches = query.order_by(Batch.year.desc(), Batch.batch_name.asc()).all()

    for batch in batches:
        if not batch.start_date or not batch.end_date:
            continue

        if batch.end_date < window_start or batch.start_date > window_end:
            continue

        bounded_start = max(batch.start_date, window_start)
        bounded_end = min(batch.end_date, window_end)

        events.append(
            {
                "id": f"schedule-{batch.id}",
                "type": "class_schedule",
                "title": f"{batch.batch_name} classes",
                "start": _start_of_day(bounded_start).isoformat(),
                "end": _end_of_day(bounded_end).isoformat(),
                "all_day": True,
                "batch_id": batch.id,
                "batch_name": batch.batch_name,
                "meta": {
                    "year": batch.year,
                    "batch_cost": float(batch.batch_cost) if batch.batch_cost is not None else 0.0,
                },
            }
        )


def get_calendar_events(
    current_user_id: int,
    role: str,
    start_date: date | None = None,
    end_date: date | None = None,
    batch_id: int | None = None,
) -> dict:
    today = date.today()
    window_start = start_date or today
    window_end = end_date or (today + timedelta(days=30))

    if window_end < window_start:
        raise ValidationError("end_date must be greater than or equal to start_date")

    accessible_batch_ids = _get_accessible_batch_ids(current_user_id=current_user_id, role=role)

    if batch_id is not None:
        if accessible_batch_ids is not None and batch_id not in accessible_batch_ids:
            raise ValidationError("You do not have access to this batch", 403)
        scoped_batch_ids = {batch_id}
    else:
        scoped_batch_ids = accessible_batch_ids

    events: list[dict] = []
    _append_test_events(events, scoped_batch_ids, window_start, window_end)
    _append_quiz_events(events, scoped_batch_ids, window_start, window_end)
    _append_batch_schedule_events(events, scoped_batch_ids, window_start, window_end)

    events.sort(key=lambda item: item.get("start") or "")

    return {
        "window": {
            "start_date": window_start.isoformat(),
            "end_date": window_end.isoformat(),
        },
        "total_events": len(events),
        "events": events,
    }
