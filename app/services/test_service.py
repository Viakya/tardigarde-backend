from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, ValidationError
from app.extensions import db
from app.models import Batch, Student, Test, TestResult
from app.services.parent_access_service import get_parent_linked_student_ids


def _get_active_batch(batch_id):
    batch = Batch.query.filter_by(id=batch_id, is_active=True).first()
    if not batch:
        raise ValidationError("Batch not found", 404)
    return batch


def _get_active_test(test_id):
    test = Test.query.filter_by(id=test_id, is_active=True).first()
    if not test:
        raise ValidationError("Test not found", 404)
    return test


def _get_active_student(student_id):
    student = Student.query.filter_by(id=student_id, is_active=True).first()
    if not student:
        raise ValidationError("Student not found", 404)
    return student


def create_test(data, created_by_user_id):
    _get_active_batch(data["batch_id"])

    test = Test(
        batch_id=data["batch_id"],
        title=data["title"],
        subject=data.get("subject"),
        max_marks=data["max_marks"],
        test_date=data["test_date"],
        created_by=created_by_user_id,
        is_active=True,
    )

    db.session.add(test)
    db.session.commit()
    return test


def list_tests(page=1, per_page=10, batch_id=None, current_user_id=None, current_role=None):
    query = Test.query.filter_by(is_active=True)

    if current_role == "parent":
        if current_user_id is None:
            raise ValidationError("Invalid user identity", 401)

        try:
            parent_user_id = int(current_user_id)
        except (TypeError, ValueError) as exc:
            raise ValidationError("Invalid user identity", 401) from exc

        allowed_student_ids = get_parent_linked_student_ids(parent_user_id)
        linked_batch_subquery = (
            db.session.query(Student.batch_id)
            .filter(Student.id.in_(allowed_student_ids), Student.batch_id.isnot(None))
            .distinct()
            .subquery()
        )
        query = query.filter(Test.batch_id.in_(db.session.query(linked_batch_subquery.c.batch_id)))

    if batch_id is not None:
        query = query.filter(Test.batch_id == batch_id)

    pagination = query.order_by(Test.test_date.desc(), Test.id.desc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False,
    )

    return {
        "tests": [test.to_dict() for test in pagination.items],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
        },
    }


def create_test_result(data):
    test = _get_active_test(data["test_id"])
    student = _get_active_student(data["student_id"])

    if student.batch_id != test.batch_id:
        raise ValidationError("Student does not belong to test batch")

    if Decimal(data["marks_obtained"]) > Decimal(test.max_marks):
        raise ValidationError("marks_obtained cannot exceed test max_marks")

    result = TestResult(
        test_id=test.id,
        student_id=student.id,
        marks_obtained=data["marks_obtained"],
        remarks=data.get("remarks"),
        is_active=True,
    )

    db.session.add(result)
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ConflictError("Result already exists for this student in this test") from exc

    return result


def list_test_results(
    page=1,
    per_page=10,
    test_id=None,
    student_id=None,
    current_user_id=None,
    current_role=None,
):
    query = TestResult.query.filter_by(is_active=True)

    if current_role == "parent":
        if current_user_id is None:
            raise ValidationError("Invalid user identity", 401)

        try:
            parent_user_id = int(current_user_id)
        except (TypeError, ValueError) as exc:
            raise ValidationError("Invalid user identity", 401) from exc

        allowed_student_ids = get_parent_linked_student_ids(parent_user_id)
        query = query.filter(TestResult.student_id.in_(allowed_student_ids))

    if test_id is not None:
        query = query.filter(TestResult.test_id == test_id)
    if student_id is not None:
        query = query.filter(TestResult.student_id == student_id)

    pagination = query.order_by(TestResult.id.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return {
        "test_results": [result.to_dict() for result in pagination.items],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
        },
    }


def get_performance_metrics(batch_id=None, current_user_id=None, current_role=None):
    query = db.session.query(TestResult, Test).join(Test, TestResult.test_id == Test.id).filter(
        TestResult.is_active.is_(True),
        Test.is_active.is_(True),
    )

    if current_role == "parent":
        if current_user_id is None:
            raise ValidationError("Invalid user identity", 401)

        try:
            parent_user_id = int(current_user_id)
        except (TypeError, ValueError) as exc:
            raise ValidationError("Invalid user identity", 401) from exc

        allowed_student_ids = get_parent_linked_student_ids(parent_user_id)
        query = query.filter(TestResult.student_id.in_(allowed_student_ids))

    if batch_id is not None:
        query = query.filter(Test.batch_id == batch_id)

    rows = query.all()
    total_obtained = Decimal("0")
    total_max = Decimal("0")

    for result, test in rows:
        total_obtained += Decimal(result.marks_obtained or 0)
        total_max += Decimal(test.max_marks or 0)

    overall_percentage = float((total_obtained / total_max * 100)) if total_max > 0 else 0.0

    top_students_query = (
        db.session.query(
            TestResult.student_id,
            func.avg((TestResult.marks_obtained / Test.max_marks) * 100).label("avg_percentage"),
        )
        .join(Test, TestResult.test_id == Test.id)
        .filter(TestResult.is_active.is_(True), Test.is_active.is_(True))
    )

    if current_role == "parent":
        try:
            parent_user_id = int(current_user_id)
        except (TypeError, ValueError) as exc:
            raise ValidationError("Invalid user identity", 401) from exc

        allowed_student_ids = get_parent_linked_student_ids(parent_user_id)
        top_students_query = top_students_query.filter(TestResult.student_id.in_(allowed_student_ids))

    if batch_id is not None:
        top_students_query = top_students_query.filter(Test.batch_id == batch_id)

    top_students_rows = (
        top_students_query.group_by(TestResult.student_id)
        .order_by(func.avg((TestResult.marks_obtained / Test.max_marks) * 100).desc())
        .limit(5)
        .all()
    )

    return {
        "batch_id": batch_id,
        "tests_evaluated": len({row[1].id for row in rows}) if rows else 0,
        "results_evaluated": len(rows),
        "overall_percentage": round(overall_percentage, 2),
        "top_students": [
            {
                "student_id": student_id,
                "average_percentage": round(float(avg_percentage), 2),
            }
            for student_id, avg_percentage in top_students_rows
        ],
    }
