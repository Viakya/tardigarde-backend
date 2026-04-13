from datetime import date, timedelta

from sqlalchemy import case, func

from app.extensions import db
from app.models import Attendance, Batch, FeePayment, Salary, Student, Teacher, User
from app.models.quiz import QuizSubmission
from app.models.test_result import TestResult


def get_monthly_attendance_percentage(year=None, batch_id=None):
    month_expr = func.date_trunc("month", Attendance.attendance_date)

    query = db.session.query(
        month_expr.label("month_start"),
        func.count(Attendance.id).label("total_records"),
        func.sum(case((Attendance.status == "present", 1), else_=0)).label("present_count"),
        func.sum(case((Attendance.status == "late", 1), else_=0)).label("late_count"),
        func.sum(case((Attendance.status == "absent", 1), else_=0)).label("absent_count"),
    ).filter(Attendance.is_active.is_(True))

    if year is not None:
        query = query.filter(func.extract("year", Attendance.attendance_date) == year)

    if batch_id is not None:
        query = query.filter(Attendance.batch_id == batch_id)

    rows = query.group_by(month_expr).order_by(month_expr.asc()).all()

    result = []
    for row in rows:
        total = int(row.total_records or 0)
        present = int(row.present_count or 0)
        late = int(row.late_count or 0)
        absent = int(row.absent_count or 0)

        attendance_percentage = (present / total * 100) if total > 0 else 0.0

        result.append(
            {
                "month": row.month_start.strftime("%Y-%m") if row.month_start else None,
                "total_records": total,
                "present_count": present,
                "late_count": late,
                "absent_count": absent,
                "attendance_percentage": round(attendance_percentage, 2),
            }
        )

    return {
        "year": year,
        "batch_id": batch_id,
        "monthly_attendance": result,
    }


def get_revenue_by_month(year=None):
    month_expr = func.date_trunc("month", FeePayment.payment_date)

    query = db.session.query(
        month_expr.label("month_start"),
        func.count(FeePayment.id).label("payments_count"),
        func.coalesce(func.sum(FeePayment.amount), 0).label("revenue"),
    )

    if year is not None:
        query = query.filter(func.extract("year", FeePayment.payment_date) == year)

    rows = query.group_by(month_expr).order_by(month_expr.asc()).all()

    return {
        "year": year,
        "monthly_revenue": [
            {
                "month": row.month_start.strftime("%Y-%m") if row.month_start else None,
                "payments_count": int(row.payments_count or 0),
                "revenue": float(row.revenue or 0),
            }
            for row in rows
        ],
    }


def get_salary_expense_by_month(year=None):
    month_expr = func.date_trunc("month", Salary.payment_date)

    query = db.session.query(
        month_expr.label("salary_month"),
        func.count(Salary.id).label("salary_records"),
        func.coalesce(func.sum(Salary.amount), 0).label("total_budgeted"),
        func.coalesce(func.sum(Salary.amount), 0).label("total_paid"),
    )

    if year is not None:
        query = query.filter(func.extract("year", Salary.payment_date) == year)

    rows = query.group_by(month_expr).order_by(month_expr.asc()).all()

    return {
        "year": year,
        "monthly_salary_expense": [
            {
                "month": row.salary_month.strftime("%Y-%m") if row.salary_month else None,
                "salary_records": int(row.salary_records or 0),
                "total_budgeted": float(row.total_budgeted or 0),
                "total_paid": float(row.total_paid or 0),
                "total_pending": float((row.total_budgeted or 0) - (row.total_paid or 0)),
            }
            for row in rows
        ],
    }


def get_batch_strength_report(include_inactive_students=False):
    active_case = case((Student.is_active.is_(True), 1), else_=0)
    inactive_case = case((Student.is_active.is_(False), 1), else_=0)

    query = (
        db.session.query(
            Batch.id.label("batch_id"),
            Batch.batch_name.label("batch_name"),
            Batch.year.label("year"),
            Batch.is_active.label("batch_is_active"),
            func.count(Student.id).label("total_students"),
            func.coalesce(func.sum(active_case), 0).label("active_students"),
            func.coalesce(func.sum(inactive_case), 0).label("inactive_students"),
        )
        .outerjoin(Student, Student.batch_id == Batch.id)
        .group_by(Batch.id)
        .order_by(Batch.year.desc(), Batch.batch_name.asc())
    )

    rows = query.all()

    result = []
    for row in rows:
        active_students = int(row.active_students or 0)
        inactive_students = int(row.inactive_students or 0)
        total_students = int(row.total_students or 0)

        payload = {
            "batch_id": row.batch_id,
            "batch_name": row.batch_name,
            "year": row.year,
            "batch_is_active": bool(row.batch_is_active),
            "total_students": total_students,
            "active_students": active_students,
            "inactive_students": inactive_students,
        }

        if include_inactive_students or active_students > 0 or total_students == 0:
            result.append(payload)

    return {"batch_strength": result}


def _active_inactive_counts(model):
    active_count = db.session.query(func.count(model.id)).filter(model.is_active.is_(True)).scalar() or 0
    inactive_count = db.session.query(func.count(model.id)).filter(model.is_active.is_(False)).scalar() or 0
    return {
        "active": int(active_count),
        "inactive": int(inactive_count),
        "total": int(active_count + inactive_count),
    }


def get_active_vs_inactive_report():
    return {
        "users": _active_inactive_counts(User),
        "students": _active_inactive_counts(Student),
        "teachers": _active_inactive_counts(Teacher),
        "batches": _active_inactive_counts(Batch),
        "attendance_records": _active_inactive_counts(Attendance),
    }


def _build_student_financial_map():
    students = Student.query.filter(Student.is_active.is_(True)).all()

    paid_rows = (
        db.session.query(FeePayment.student_id, func.coalesce(func.sum(FeePayment.amount), 0).label("paid_total"))
        .group_by(FeePayment.student_id)
        .all()
    )
    paid_map = {int(row.student_id): float(row.paid_total or 0) for row in paid_rows}

    financial = {}
    for student in students:
        student_id = int(student.id)
        batch_cost = float(student.batch.batch_cost) if student.batch and student.batch.batch_cost is not None else 0.0
        discount = float(student.discount_percent or 0)
        expected = max(0.0, batch_cost - (batch_cost * discount / 100.0))
        paid = paid_map.get(student_id, 0.0)
        outstanding = max(0.0, expected - paid)
        financial[student_id] = {
            "student_id": student_id,
            "student_name": student.user.full_name if student.user else f"Student #{student_id}",
            "batch_name": student.batch.batch_name if student.batch else "Unassigned",
            "expected": expected,
            "paid": paid,
            "outstanding": outstanding,
        }
    return financial


def get_director_risk_summary(days=30):
    since = date.today() - timedelta(days=max(1, int(days)))

    financial = _build_student_financial_map()

    attendance_rows = (
        db.session.query(
            Attendance.student_id,
            func.count(Attendance.id).label("total_sessions"),
            func.sum(case((Attendance.status == "present", 1), else_=0)).label("present_count"),
            func.sum(case((Attendance.status == "absent", 1), else_=0)).label("absent_count"),
            func.sum(case((Attendance.status == "late", 1), else_=0)).label("late_count"),
        )
        .filter(Attendance.is_active.is_(True), Attendance.attendance_date >= since)
        .group_by(Attendance.student_id)
        .all()
    )
    attendance_map = {
        int(row.student_id): {
            "total": int(row.total_sessions or 0),
            "present": int(row.present_count or 0),
            "absent": int(row.absent_count or 0),
            "late": int(row.late_count or 0),
        }
        for row in attendance_rows
    }

    # Compute test percentage in Python to keep query logic simple and portable.
    test_rows = TestResult.query.filter(TestResult.is_active.is_(True)).all()
    test_map = {}
    for row in test_rows:
        if not row.test or not row.test.max_marks:
            continue
        sid = int(row.student_id)
        pct = float(row.marks_obtained or 0) / float(row.test.max_marks) * 100.0
        state = test_map.setdefault(sid, {"sum": 0.0, "count": 0})
        state["sum"] += pct
        state["count"] += 1

    quiz_rows = (
        db.session.query(QuizSubmission.student_id, func.count(QuizSubmission.id).label("submitted"))
        .group_by(QuizSubmission.student_id)
        .all()
    )
    quiz_map = {int(row.student_id): int(row.submitted or 0) for row in quiz_rows}

    at_risk = []
    attention_fees = 0
    attention_attendance = 0
    attention_scores = 0

    for student_id, fin in financial.items():
        att = attendance_map.get(student_id, {"total": 0, "present": 0, "absent": 0, "late": 0})
        total_att = max(1, att["total"])
        attendance_pct = (att["present"] / total_att) * 100.0 if att["total"] > 0 else 0.0
        avg_test_pct = (test_map.get(student_id, {"sum": 0.0, "count": 0})["sum"] / test_map.get(student_id, {"sum": 0.0, "count": 0})["count"]) if test_map.get(student_id, {"count": 0})["count"] > 0 else 0.0
        quiz_attempts = quiz_map.get(student_id, 0)

        risk_score = 0
        reasons = []

        if fin["outstanding"] > 0:
            attention_fees += 1
            risk_score += 40
            reasons.append("Fee outstanding")

        if attendance_pct < 75:
            attention_attendance += 1
            risk_score += 35
            reasons.append(f"Attendance low ({attendance_pct:.0f}%)")

        if avg_test_pct > 0 and avg_test_pct < 45:
            attention_scores += 1
            risk_score += 25
            reasons.append(f"Low scores ({avg_test_pct:.0f}%)")

        if quiz_attempts == 0:
            risk_score += 10
            reasons.append("No quiz attempts")

        if risk_score <= 0:
            continue

        at_risk.append(
            {
                "student_id": student_id,
                "student_name": fin["student_name"],
                "batch_name": fin["batch_name"],
                "risk_score": min(risk_score, 100),
                "attendance_percentage": round(attendance_pct, 1),
                "avg_test_percentage": round(avg_test_pct, 1),
                "outstanding_amount": round(fin["outstanding"], 2),
                "quiz_attempts": quiz_attempts,
                "reasons": reasons,
            }
        )

    at_risk.sort(key=lambda item: item["risk_score"], reverse=True)

    return {
        "window_days": int(days),
        "summary": {
            "students_at_risk": len(at_risk),
            "fee_attention_count": attention_fees,
            "attendance_attention_count": attention_attendance,
            "score_attention_count": attention_scores,
        },
        "top_risks": at_risk[:8],
    }


def get_smart_nudges(limit=8):
    report = get_director_risk_summary(days=30)
    top = report.get("top_risks", [])
    items = []

    for row in top:
        if row["outstanding_amount"] > 0:
            items.append(
                {
                    "type": "fee_followup",
                    "severity": "high" if row["outstanding_amount"] >= 5000 else "medium",
                    "title": f"Fee follow-up: {row['student_name']}",
                    "message": f"Outstanding Rs {row['outstanding_amount']:.0f} in {row['batch_name']}",
                    "target_section": "fees",
                }
            )

        if row["attendance_percentage"] < 75:
            items.append(
                {
                    "type": "attendance_intervention",
                    "severity": "high" if row["attendance_percentage"] < 60 else "medium",
                    "title": f"Attendance intervention: {row['student_name']}",
                    "message": f"Attendance at {row['attendance_percentage']}% - schedule coach check-in",
                    "target_section": "students",
                }
            )

        if row["avg_test_percentage"] > 0 and row["avg_test_percentage"] < 45:
            items.append(
                {
                    "type": "academic_support",
                    "severity": "medium",
                    "title": f"Academic support: {row['student_name']}",
                    "message": f"Average score {row['avg_test_percentage']}% - assign revision plan",
                    "target_section": "students",
                }
            )

    if not items:
        items.append(
            {
                "type": "system",
                "severity": "low",
                "title": "All clear",
                "message": "No critical nudges right now. Keep monitoring dashboard trends.",
                "target_section": "dashboard",
            }
        )

    severity_order = {"high": 0, "medium": 1, "low": 2}
    items.sort(key=lambda item: severity_order.get(item["severity"], 3))

    return {
        "nudges": items[: max(1, int(limit))],
        "generated_from_window_days": report.get("window_days", 30),
    }
