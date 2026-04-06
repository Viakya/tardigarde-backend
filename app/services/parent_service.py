"""
Parent Service - Business logic for parent-specific operations
"""
from datetime import date, timedelta
from decimal import Decimal

from app.core.exceptions import ValidationError
from app.extensions import db
from app.models import User, Student, Batch, FeePayment, Attendance, Quiz, QuizSubmission, Test, TestResult


def get_parent_children(parent_user_id):
    """Get all children (students) linked to a parent"""
    parent = User.query.filter_by(id=parent_user_id, role='parent', is_active=True).first()
    if not parent:
        raise ValidationError("Parent not found", 404)
    
    children = []
    for student in parent.children:
        if student.is_active:
            child_data = student.to_dict()
            
            # Add batch details with teachers
            if student.batch:
                batch = student.batch
                child_data['batch'] = {
                    'id': batch.id,
                    'batch_name': batch.batch_name,
                    'year': batch.year,
                    'batch_cost': float(batch.batch_cost) if batch.batch_cost else 0,
                    'start_date': batch.start_date.isoformat() if batch.start_date else None,
                    'end_date': batch.end_date.isoformat() if batch.end_date else None,
                    'teachers': [
                        {
                            'id': t.id,
                            'name': t.user.full_name if t.user else 'Unknown',
                            'specialization': t.specialization,
                        }
                        for t in batch.teachers if t.is_active
                    ]
                }
            
            children.append(child_data)
    
    return children


def get_child_details(parent_user_id, student_id):
    """Get detailed information about a specific child"""
    parent = User.query.filter_by(id=parent_user_id, role='parent', is_active=True).first()
    if not parent:
        raise ValidationError("Parent not found", 404)
    
    # Verify this student is linked to the parent
    student = Student.query.filter_by(id=student_id, is_active=True).first()
    if not student:
        raise ValidationError("Student not found", 404)
    
    if student not in parent.children:
        raise ValidationError("You don't have access to this student's information", 403)
    
    return student.to_dict()


def get_child_fees(parent_user_id, student_id):
    """Get fee information for a specific child"""
    parent = User.query.filter_by(id=parent_user_id, role='parent', is_active=True).first()
    if not parent:
        raise ValidationError("Parent not found", 404)
    
    student = Student.query.filter_by(id=student_id, is_active=True).first()
    if not student:
        raise ValidationError("Student not found", 404)
    
    if student not in parent.children:
        raise ValidationError("You don't have access to this student's information", 403)
    
    # Get all fee payments for this student
    payments = FeePayment.query.filter_by(student_id=student_id).order_by(FeePayment.payment_date.desc()).all()
    
    # Calculate fee summary
    batch_cost = float(student.batch.batch_cost) if student.batch else 0
    discount_pct = float(student.discount_percent or 0)
    total_fee = batch_cost * (1 - discount_pct / 100)
    total_paid = sum(float(p.amount) for p in payments)
    remaining = max(0, total_fee - total_paid)
    
    return {
        'student_id': student_id,
        'student_name': student.user.full_name if student.user else 'Unknown',
        'batch_name': student.batch.batch_name if student.batch else None,
        'total_fee': total_fee,
        'discount_percent': discount_pct,
        'total_paid': total_paid,
        'remaining': remaining,
        'is_fully_paid': remaining <= 0,
        'payments': [p.to_dict() for p in payments]
    }


def get_child_attendance(parent_user_id, student_id, days=30):
    """Get attendance records for a specific child"""
    parent = User.query.filter_by(id=parent_user_id, role='parent', is_active=True).first()
    if not parent:
        raise ValidationError("Parent not found", 404)
    
    student = Student.query.filter_by(id=student_id, is_active=True).first()
    if not student:
        raise ValidationError("Student not found", 404)
    
    if student not in parent.children:
        raise ValidationError("You don't have access to this student's information", 403)
    
    # Get attendance records for the last N days
    start_date = date.today() - timedelta(days=days)
    records = Attendance.query.filter(
        Attendance.student_id == student_id,
        Attendance.attendance_date >= start_date
    ).order_by(Attendance.attendance_date.desc()).all()
    
    # Calculate summary
    total = len(records)
    present = sum(1 for r in records if r.status == 'present')
    absent = total - present
    rate = round((present / total * 100), 1) if total > 0 else 0
    
    return {
        'student_id': student_id,
        'student_name': student.user.full_name if student.user else 'Unknown',
        'period_days': days,
        'total_classes': total,
        'present': present,
        'absent': absent,
        'attendance_rate': rate,
        'records': [
            {
                'id': r.id,
                'date': r.attendance_date.isoformat() if r.attendance_date else None,
                'status': r.status,
                'remarks': r.remarks,
                'batch_name': r.batch.batch_name if r.batch else None,
            }
            for r in records
        ]
    }


def get_child_test_results(parent_user_id, student_id):
    """Get test results for a specific child"""
    parent = User.query.filter_by(id=parent_user_id, role='parent', is_active=True).first()
    if not parent:
        raise ValidationError("Parent not found", 404)
    
    student = Student.query.filter_by(id=student_id, is_active=True).first()
    if not student:
        raise ValidationError("Student not found", 404)
    
    if student not in parent.children:
        raise ValidationError("You don't have access to this student's information", 403)
    
    # Get all test results for this student
    results = TestResult.query.filter_by(student_id=student_id).all()
    
    # Calculate summary
    total_tests = len(results)
    if total_tests > 0:
        avg_percentage = sum(
            (float(r.marks_obtained) / float(r.test.max_marks) * 100) if r.test else 0
            for r in results
        ) / total_tests
    else:
        avg_percentage = 0
    
    return {
        'student_id': student_id,
        'student_name': student.user.full_name if student.user else 'Unknown',
        'total_tests': total_tests,
        'average_percentage': round(avg_percentage, 1),
        'results': [
            {
                'id': r.id,
                'test_id': r.test_id,
                'test_title': r.test.title if r.test else 'Unknown',
                'subject': r.test.subject if r.test else None,
                'test_date': r.test.test_date.isoformat() if r.test and r.test.test_date else None,
                'marks_obtained': float(r.marks_obtained) if r.marks_obtained else 0,
                'max_marks': float(r.test.max_marks) if r.test else 0,
                'percentage': round((float(r.marks_obtained) / float(r.test.max_marks) * 100), 1) if r.test and float(r.test.max_marks) > 0 else 0,
                'remarks': r.remarks,
            }
            for r in results
        ]
    }


def get_child_quiz_results(parent_user_id, student_id):
    """Get quiz results for a specific child"""
    parent = User.query.filter_by(id=parent_user_id, role='parent', is_active=True).first()
    if not parent:
        raise ValidationError("Parent not found", 404)

    student = Student.query.filter_by(id=student_id, is_active=True).first()
    if not student:
        raise ValidationError("Student not found", 404)

    if student not in parent.children:
        raise ValidationError("You don't have access to this student's information", 403)

    quizzes = Quiz.query.filter(
        Quiz.batch_id == student.batch_id,
        Quiz.status.in_(["published", "closed"]),
    ).order_by(Quiz.created_at.desc()).all()

    submissions_map = {}
    if quizzes:
        submissions = QuizSubmission.query.filter(
            QuizSubmission.student_id == student.id,
            QuizSubmission.quiz_id.in_([quiz.id for quiz in quizzes]),
        ).all()
        submissions_map = {submission.quiz_id: submission for submission in submissions}

    quiz_payload = []
    for quiz in quizzes:
        payload = quiz.to_dict()
        submission = submissions_map.get(quiz.id)
        payload["student_submission"] = submission.to_dict() if submission else None
        quiz_payload.append(payload)

    def _score_percent(q):
        submission = q.get("student_submission")
        if not submission or submission.get("score") is None:
            return None
        total = q.get("total_marks") or 100
        if not total:
            return None
        return round(float(submission.get("score")) / float(total) * 100, 1)

    practice_scores = [
        _score_percent(q)
        for q in quiz_payload
        if q.get("mode") == "practice"
    ]
    practice_scores = [s for s in practice_scores if s is not None]

    graded_scores = [
        _score_percent(q)
        for q in quiz_payload
        if q.get("mode") == "graded" and q.get("status") == "closed"
    ]
    graded_scores = [s for s in graded_scores if s is not None]

    return {
        "student_id": student.id,
        "student_name": student.user.full_name if student.user else "Unknown",
        "practice_count": len([q for q in quiz_payload if q.get("mode") == "practice"]),
        "graded_count": len([q for q in quiz_payload if q.get("mode") == "graded"]),
        "practice_average": round(sum(practice_scores) / len(practice_scores), 1) if practice_scores else 0,
        "graded_average": round(sum(graded_scores) / len(graded_scores), 1) if graded_scores else 0,
        "quizzes": quiz_payload,
    }


def get_child_quiz_detail(parent_user_id, student_id, quiz_id):
    """Get quiz detail with student answers for a specific child"""
    parent = User.query.filter_by(id=parent_user_id, role='parent', is_active=True).first()
    if not parent:
        raise ValidationError("Parent not found", 404)

    student = Student.query.filter_by(id=student_id, is_active=True).first()
    if not student:
        raise ValidationError("Student not found", 404)

    if student not in parent.children:
        raise ValidationError("You don't have access to this student's information", 403)

    quiz = Quiz.query.filter_by(id=quiz_id).first()
    if not quiz or quiz.batch_id != student.batch_id:
        raise ValidationError("Quiz not found", 404)

    payload = quiz.to_dict(include_questions=True)
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


def get_parent_dashboard_summary(parent_user_id):
    """Get comprehensive dashboard summary for a parent"""
    parent = User.query.filter_by(id=parent_user_id, role='parent', is_active=True).first()
    if not parent:
        raise ValidationError("Parent not found", 404)
    
    children = [s for s in parent.children if s.is_active]
    
    # Calculate aggregate stats
    total_children = len(children)
    total_pending_fees = 0
    total_attendance_rate = 0
    recent_quizzes_count = 0
    
    children_summary = []
    
    for student in children:
        # Fee calculation
        batch_cost = float(student.batch.batch_cost) if student.batch else 0
        discount_pct = float(student.discount_percent or 0)
        total_fee = batch_cost * (1 - discount_pct / 100)
        payments = FeePayment.query.filter_by(student_id=student.id).all()
        total_paid = sum(float(p.amount) for p in payments)
        pending = max(0, total_fee - total_paid)
        total_pending_fees += pending
        
        # Attendance calculation (last 30 days)
        start_date = date.today() - timedelta(days=30)
        attendance_records = Attendance.query.filter(
            Attendance.student_id == student.id,
            Attendance.attendance_date >= start_date
        ).all()
        att_total = len(attendance_records)
        att_present = sum(1 for r in attendance_records if r.status == 'present')
        att_rate = round((att_present / att_total * 100), 1) if att_total > 0 else 0
        total_attendance_rate += att_rate
        
        # Recent quizzes (last 30 days)
        recent_quizzes = QuizSubmission.query.join(Quiz).filter(
            QuizSubmission.student_id == student.id,
            QuizSubmission.submitted_at >= start_date,
        ).all()
        recent_quizzes_count += len(recent_quizzes)

        quiz_scores = [
            float(q.score) / float((q.quiz.total_marks or 100)) * 100
            for q in recent_quizzes
            if q.score is not None
        ]
        avg_score = sum(quiz_scores) / len(quiz_scores) if quiz_scores else 0
        
        children_summary.append({
            'id': student.id,
            'name': student.user.full_name if student.user else 'Unknown',
            'email': student.user.email if student.user else None,
            'batch_name': student.batch.batch_name if student.batch else None,
            'batch_id': student.batch_id,
            'attendance_rate': att_rate,
            'pending_fee': pending,
            'total_fee': total_fee,
            'fee_paid': total_paid,
            'is_fee_paid': pending <= 0,
            'quiz_average': round(avg_score, 1),
            'total_quizzes': len(recent_quizzes),
            'recent_quizzes': len(recent_quizzes),
        })
    
    avg_attendance = round(total_attendance_rate / total_children, 1) if total_children > 0 else 0
    
    return {
        'parent_id': parent_user_id,
        'parent_name': parent.full_name,
        'total_children': total_children,
        'total_pending_fees': total_pending_fees,
        'average_attendance': avg_attendance,
    'recent_quizzes_count': recent_quizzes_count,
        'children': children_summary,
    }
