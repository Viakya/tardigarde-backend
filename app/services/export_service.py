from __future__ import annotations

from datetime import date, datetime
from io import BytesIO, StringIO
import csv

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.core.exceptions import ValidationError
from app.models import Attendance, Quiz, QuizSubmission, Test, TestResult
from app.services.reporting_service import get_revenue_by_month


def parse_optional_date(raw: str | None, field_name: str) -> date | None:
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError as exc:
        raise ValidationError(f"{field_name} must be in YYYY-MM-DD format") from exc


def build_attendance_csv(batch_id: int | None = None, start_date: date | None = None, end_date: date | None = None) -> bytes:
    query = Attendance.query.filter(Attendance.is_active.is_(True))

    if batch_id is not None:
        query = query.filter(Attendance.batch_id == batch_id)
    if start_date is not None:
        query = query.filter(Attendance.attendance_date >= start_date)
    if end_date is not None:
        query = query.filter(Attendance.attendance_date <= end_date)

    records = query.order_by(Attendance.attendance_date.desc(), Attendance.id.desc()).all()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "attendance_id",
            "date",
            "student_id",
            "student_name",
            "student_email",
            "batch_id",
            "batch_name",
            "status",
            "remarks",
            "marked_by",
            "marked_by_name",
        ]
    )

    for record in records:
        writer.writerow(
            [
                record.id,
                record.attendance_date.isoformat() if record.attendance_date else "",
                record.student_id,
                record.student.user.full_name if record.student and record.student.user else "",
                record.student.user.email if record.student and record.student.user else "",
                record.batch_id,
                record.batch.batch_name if record.batch else "",
                record.status,
                record.remarks or "",
                record.marked_by,
                record.marker.full_name if record.marker else "",
            ]
        )

    return output.getvalue().encode("utf-8")


def build_results_excel(batch_id: int | None = None, start_date: date | None = None, end_date: date | None = None) -> bytes:
    query = TestResult.query.filter(TestResult.is_active.is_(True)).join(Test, TestResult.test_id == Test.id)

    if batch_id is not None:
        query = query.filter(Test.batch_id == batch_id)
    if start_date is not None:
        query = query.filter(Test.test_date >= start_date)
    if end_date is not None:
        query = query.filter(Test.test_date <= end_date)

    test_rows = query.order_by(Test.test_date.desc(), TestResult.id.desc()).all()

    test_table_rows = []
    for item in test_rows:
        max_marks = float(item.test.max_marks) if item.test and item.test.max_marks is not None else 0
        obtained = float(item.marks_obtained) if item.marks_obtained is not None else 0
        percentage = round((obtained / max_marks) * 100, 2) if max_marks > 0 else 0

        test_table_rows.append(
            {
                "result_id": item.id,
                "test_id": item.test_id,
                "test_title": item.test.title if item.test else "",
                "subject": item.test.subject if item.test else "",
                "test_date": item.test.test_date.isoformat() if item.test and item.test.test_date else "",
                "batch_id": item.test.batch_id if item.test else None,
                "batch_name": item.test.batch.batch_name if item.test and item.test.batch else "",
                "student_id": item.student_id,
                "student_name": item.student.user.full_name if item.student and item.student.user else "",
                "student_email": item.student.user.email if item.student and item.student.user else "",
                "marks_obtained": obtained,
                "max_marks": max_marks,
                "percentage": percentage,
                "remarks": item.remarks or "",
                "created_at": item.created_at.isoformat() if item.created_at else "",
            }
        )

    quiz_query = QuizSubmission.query.join(Quiz, QuizSubmission.quiz_id == Quiz.id)

    if batch_id is not None:
        quiz_query = quiz_query.filter(Quiz.batch_id == batch_id)

    quiz_submissions = quiz_query.order_by(QuizSubmission.created_at.desc(), QuizSubmission.id.desc()).all()

    quiz_table_rows = []
    for item in quiz_submissions:
        attempt_dt = item.submitted_at or item.created_at
        attempt_date = attempt_dt.date() if attempt_dt else None

        if start_date is not None and attempt_date is not None and attempt_date < start_date:
            continue
        if end_date is not None and attempt_date is not None and attempt_date > end_date:
            continue

        total_marks = float(item.quiz.total_marks) if item.quiz and item.quiz.total_marks is not None else 0
        score = float(item.score) if item.score is not None else 0
        percentage = round((score / total_marks) * 100, 2) if total_marks > 0 else 0

        quiz_table_rows.append(
            {
                "submission_id": item.id,
                "quiz_id": item.quiz_id,
                "quiz_title": item.quiz.title if item.quiz else "",
                "batch_id": item.quiz.batch_id if item.quiz else None,
                "batch_name": item.quiz.batch.batch_name if item.quiz and item.quiz.batch else "",
                "student_id": item.student_id,
                "student_name": item.student.user.full_name if item.student and item.student.user else "",
                "student_email": item.student.user.email if item.student and item.student.user else "",
                "mode": item.quiz.mode if item.quiz else "",
                "status": item.status,
                "score": score,
                "total_marks": total_marks,
                "percentage": percentage,
                "submitted_at": item.submitted_at.isoformat() if item.submitted_at else "",
                "created_at": item.created_at.isoformat() if item.created_at else "",
            }
        )

    if not test_table_rows:
        test_table_rows.append(
            {
                "result_id": "",
                "test_id": "",
                "test_title": "No test results found for selected filters",
                "subject": "",
                "test_date": "",
                "batch_id": "",
                "batch_name": "",
                "student_id": "",
                "student_name": "",
                "student_email": "",
                "marks_obtained": "",
                "max_marks": "",
                "percentage": "",
                "remarks": "",
                "created_at": "",
            }
        )

    if not quiz_table_rows:
        quiz_table_rows.append(
            {
                "submission_id": "",
                "quiz_id": "",
                "quiz_title": "No quiz submissions found for selected filters",
                "batch_id": "",
                "batch_name": "",
                "student_id": "",
                "student_name": "",
                "student_email": "",
                "mode": "",
                "status": "",
                "score": "",
                "total_marks": "",
                "percentage": "",
                "submitted_at": "",
                "created_at": "",
            }
        )

    tests_df = pd.DataFrame(test_table_rows)
    quizzes_df = pd.DataFrame(quiz_table_rows)

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        tests_df.to_excel(writer, index=False, sheet_name="Test Results")
        quizzes_df.to_excel(writer, index=False, sheet_name="Quiz Submissions")
    return buffer.getvalue()


def build_revenue_pdf(year: int | None = None) -> bytes:
    data = get_revenue_by_month(year=year)
    rows = data.get("monthly_revenue", [])

    total_revenue = sum(float(item.get("revenue", 0) or 0) for item in rows)
    total_payments = sum(int(item.get("payments_count", 0) or 0) for item in rows)

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title="Revenue Report",
    )

    styles = getSampleStyleSheet()
    heading = styles["Heading1"]
    heading.fontName = "Helvetica-Bold"
    heading.fontSize = 18
    heading.leading = 22

    sub = ParagraphStyle(
        "sub",
        parent=styles["BodyText"],
        textColor=colors.HexColor("#475569"),
        fontSize=10,
        leading=14,
    )

    story = []
    report_year = str(year) if year is not None else "All Years"
    story.append(Paragraph(f"Revenue Report ({report_year})", heading))
    story.append(Paragraph(f"Generated at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", sub))
    story.append(Spacer(1, 8))
    story.append(Paragraph(f"Total Payments: <b>{total_payments}</b>", styles["BodyText"]))
    story.append(Paragraph(f"Total Revenue: <b>Rs {total_revenue:,.2f}</b>", styles["BodyText"]))
    story.append(Spacer(1, 10))

    table_data = [["Month", "Payments", "Revenue (Rs)"]]
    for item in rows:
        table_data.append(
            [
                item.get("month") or "",
                str(item.get("payments_count") or 0),
                f"{float(item.get('revenue') or 0):,.2f}",
            ]
        )

    if len(table_data) == 1:
        table_data.append(["No data", "0", "0.00"])

    table = Table(table_data, colWidths=[70 * mm, 35 * mm, 55 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    story.append(table)
    doc.build(story)
    return buffer.getvalue()
