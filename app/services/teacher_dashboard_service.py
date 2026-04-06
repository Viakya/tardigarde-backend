"""
Teacher Dashboard Service - Business logic for teacher-specific operations
"""
from datetime import date, timedelta
from sqlalchemy import func, and_
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ValidationError, ConflictError
from app.extensions import db
from app.models import User, Teacher, Batch, Student, Attendance, Test, TestResult


def get_teacher_by_user_id(user_id):
    """Get teacher profile by user_id"""
    teacher = Teacher.query.filter_by(user_id=user_id, is_active=True).first()
    if not teacher:
        raise ValidationError("Teacher profile not found", 404)
    return teacher


def get_teacher_batches(user_id):
    """Get all batches assigned to a teacher"""
    teacher = get_teacher_by_user_id(user_id)
    
    batches_data = []
    for batch in teacher.batches:
        if not batch.is_active:
            continue
            
        # Count students in the batch
        student_count = Student.query.filter_by(batch_id=batch.id, is_active=True).count()
        
        # Get other teachers in this batch
        other_teachers = [
            {
                "id": t.id,
                "name": t.user.full_name if t.user else "Unknown",
                "specialization": t.specialization
            }
            for t in batch.teachers
            if t.is_active and t.id != teacher.id
        ]
        
        batches_data.append({
            "id": batch.id,
            "batch_name": batch.batch_name,
            "year": batch.year,
            "start_date": batch.start_date.isoformat() if batch.start_date else None,
            "end_date": batch.end_date.isoformat() if batch.end_date else None,
            "student_count": student_count,
            "other_teachers": other_teachers,
        })
    
    return batches_data


def get_batch_students(user_id, batch_id):
    """Get all students in a batch (teacher must be assigned to batch)"""
    teacher = get_teacher_by_user_id(user_id)
    
    # Verify teacher is assigned to this batch
    batch = Batch.query.filter_by(id=batch_id, is_active=True).first()
    if not batch:
        raise ValidationError("Batch not found", 404)
    
    if teacher not in batch.teachers:
        raise ValidationError("You are not assigned to this batch", 403)
    
    students = Student.query.filter_by(batch_id=batch_id, is_active=True).all()
    
    students_data = []
    for student in students:
        # Calculate attendance percentage
        total_attendance = Attendance.query.filter_by(
            student_id=student.id, is_active=True
        ).count()
        present_count = Attendance.query.filter_by(
            student_id=student.id, status="present", is_active=True
        ).count()
        attendance_rate = (present_count / total_attendance * 100) if total_attendance > 0 else 0
        
        # Get average test score
        test_results = db.session.query(
            func.avg(TestResult.marks_obtained),
            func.avg(Test.max_marks)
        ).join(Test).filter(
            TestResult.student_id == student.id,
            TestResult.is_active == True,
            Test.is_active == True
        ).first()
        
        avg_marks = float(test_results[0]) if test_results[0] else 0
        avg_max = float(test_results[1]) if test_results[1] else 0
        avg_percentage = (avg_marks / avg_max * 100) if avg_max > 0 else 0
        
        students_data.append({
            "id": student.id,
            "user_id": student.user_id,
            "full_name": student.user.full_name if student.user else "Unknown",
            "email": student.user.email if student.user else None,
            "phone_number": student.phone_number,
            "enrollment_date": student.enrollment_date.isoformat() if student.enrollment_date else None,
            "attendance_rate": round(attendance_rate, 1),
            "avg_test_score": round(avg_percentage, 1),
        })
    
    return {
        "batch": {
            "id": batch.id,
            "batch_name": batch.batch_name,
            "year": batch.year,
        },
        "students": students_data,
        "total_students": len(students_data),
    }


def get_batch_attendance(user_id, batch_id, attendance_date=None):
    """Get attendance for a batch on a specific date"""
    teacher = get_teacher_by_user_id(user_id)
    
    batch = Batch.query.filter_by(id=batch_id, is_active=True).first()
    if not batch:
        raise ValidationError("Batch not found", 404)
    
    if teacher not in batch.teachers:
        raise ValidationError("You are not assigned to this batch", 403)
    
    if attendance_date is None:
        attendance_date = date.today()
    
    # Get all students in the batch
    students = Student.query.filter_by(batch_id=batch_id, is_active=True).all()
    
    # Get attendance records for this date
    attendance_records = Attendance.query.filter_by(
        batch_id=batch_id,
        attendance_date=attendance_date,
        is_active=True
    ).all()
    
    # Create a dict for quick lookup
    attendance_map = {a.student_id: a for a in attendance_records}
    
    students_attendance = []
    for student in students:
        attendance = attendance_map.get(student.id)
        students_attendance.append({
            "student_id": student.id,
            "full_name": student.user.full_name if student.user else "Unknown",
            "status": attendance.status if attendance else None,
            "remarks": attendance.remarks if attendance else None,
            "attendance_id": attendance.id if attendance else None,
            "marked_by": attendance.marker.full_name if attendance and attendance.marker else None,
        })
    
    return {
        "batch": {
            "id": batch.id,
            "batch_name": batch.batch_name,
        },
        "date": attendance_date.isoformat(),
        "students": students_attendance,
        "summary": {
            "total": len(students),
            "present": sum(1 for s in students_attendance if s["status"] == "present"),
            "absent": sum(1 for s in students_attendance if s["status"] == "absent"),
            "late": sum(1 for s in students_attendance if s["status"] == "late"),
            "unmarked": sum(1 for s in students_attendance if s["status"] is None),
        }
    }


def mark_batch_attendance(user_id, batch_id, attendance_date, attendance_data):
    """
    Mark attendance for multiple students in a batch
    attendance_data: list of {"student_id": int, "status": str, "remarks": str (optional)}
    """
    teacher = get_teacher_by_user_id(user_id)
    user = User.query.get(user_id)
    
    batch = Batch.query.filter_by(id=batch_id, is_active=True).first()
    if not batch:
        raise ValidationError("Batch not found", 404)
    
    if teacher not in batch.teachers:
        raise ValidationError("You are not assigned to this batch", 403)
    
    # Get valid students in the batch
    valid_student_ids = {s.id for s in Student.query.filter_by(batch_id=batch_id, is_active=True).all()}
    
    results = {"created": 0, "updated": 0, "errors": []}
    
    for record in attendance_data:
        student_id = record.get("student_id")
        status = record.get("status")
        remarks = record.get("remarks", "")
        
        if student_id not in valid_student_ids:
            results["errors"].append(f"Student {student_id} not found in batch")
            continue
        
        if status not in ["present", "absent", "late", "excused"]:
            results["errors"].append(f"Invalid status '{status}' for student {student_id}")
            continue
        
        # Check if attendance already exists
        existing = Attendance.query.filter_by(
            student_id=student_id,
            attendance_date=attendance_date,
        ).first()
        
        if existing:
            # Update existing record
            existing.status = status
            existing.remarks = remarks
            existing.marked_by = user_id
            existing.is_active = True
            results["updated"] += 1
        else:
            # Create new record
            attendance = Attendance(
                student_id=student_id,
                batch_id=batch_id,
                attendance_date=attendance_date,
                status=status,
                remarks=remarks,
                marked_by=user_id,
                is_active=True,
            )
            db.session.add(attendance)
            results["created"] += 1
    
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ConflictError("Failed to save attendance") from exc
    
    return results


def get_batch_tests(user_id, batch_id):
    """Get all tests for a batch"""
    teacher = get_teacher_by_user_id(user_id)
    
    batch = Batch.query.filter_by(id=batch_id, is_active=True).first()
    if not batch:
        raise ValidationError("Batch not found", 404)
    
    if teacher not in batch.teachers:
        raise ValidationError("You are not assigned to this batch", 403)
    
    tests = Test.query.filter_by(batch_id=batch_id, is_active=True).order_by(Test.test_date.desc()).all()
    
    tests_data = []
    for test in tests:
        # Count results entered
        results_count = TestResult.query.filter_by(test_id=test.id, is_active=True).count()
        student_count = Student.query.filter_by(batch_id=batch_id, is_active=True).count()
        
        # Calculate average score
        avg_result = db.session.query(
            func.avg(TestResult.marks_obtained)
        ).filter(
            TestResult.test_id == test.id,
            TestResult.is_active == True
        ).scalar()
        
        tests_data.append({
            "id": test.id,
            "title": test.title,
            "subject": test.subject,
            "max_marks": float(test.max_marks) if test.max_marks else 0,
            "test_date": test.test_date.isoformat() if test.test_date else None,
            "results_entered": results_count,
            "total_students": student_count,
            "average_score": round(float(avg_result), 2) if avg_result else None,
            "created_by": test.creator.full_name if test.creator else None,
        })
    
    return {
        "batch": {
            "id": batch.id,
            "batch_name": batch.batch_name,
        },
        "tests": tests_data,
    }


def create_test(user_id, batch_id, data):
    """Create a new test for a batch"""
    teacher = get_teacher_by_user_id(user_id)
    
    batch = Batch.query.filter_by(id=batch_id, is_active=True).first()
    if not batch:
        raise ValidationError("Batch not found", 404)
    
    if teacher not in batch.teachers:
        raise ValidationError("You are not assigned to this batch", 403)
    
    test = Test(
        batch_id=batch_id,
        title=data["title"],
        subject=data.get("subject"),
        max_marks=data["max_marks"],
        test_date=data["test_date"],
        created_by=user_id,
        is_active=True,
    )
    
    db.session.add(test)
    
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ConflictError("Failed to create test") from exc
    
    return test


def get_test_results(user_id, test_id):
    """Get all results for a test"""
    teacher = get_teacher_by_user_id(user_id)
    
    test = Test.query.filter_by(id=test_id, is_active=True).first()
    if not test:
        raise ValidationError("Test not found", 404)
    
    batch = test.batch
    if teacher not in batch.teachers:
        raise ValidationError("You are not assigned to this batch", 403)
    
    # Get all students in the batch
    students = Student.query.filter_by(batch_id=batch.id, is_active=True).all()
    
    # Get existing results
    results = TestResult.query.filter_by(test_id=test_id, is_active=True).all()
    results_map = {r.student_id: r for r in results}
    
    students_results = []
    for student in students:
        result = results_map.get(student.id)
        students_results.append({
            "student_id": student.id,
            "full_name": student.user.full_name if student.user else "Unknown",
            "marks_obtained": float(result.marks_obtained) if result else None,
            "remarks": result.remarks if result else None,
            "result_id": result.id if result else None,
        })
    
    return {
        "test": {
            "id": test.id,
            "title": test.title,
            "subject": test.subject,
            "max_marks": float(test.max_marks) if test.max_marks else 0,
            "test_date": test.test_date.isoformat() if test.test_date else None,
        },
        "batch": {
            "id": batch.id,
            "batch_name": batch.batch_name,
        },
        "results": students_results,
        "summary": {
            "total": len(students),
            "entered": sum(1 for s in students_results if s["marks_obtained"] is not None),
            "pending": sum(1 for s in students_results if s["marks_obtained"] is None),
        }
    }


def save_test_results(user_id, test_id, results_data):
    """
    Save test results for multiple students
    results_data: list of {"student_id": int, "marks_obtained": float, "remarks": str (optional)}
    """
    teacher = get_teacher_by_user_id(user_id)
    
    test = Test.query.filter_by(id=test_id, is_active=True).first()
    if not test:
        raise ValidationError("Test not found", 404)
    
    batch = test.batch
    if teacher not in batch.teachers:
        raise ValidationError("You are not assigned to this batch", 403)
    
    # Get valid students in the batch
    valid_student_ids = {s.id for s in Student.query.filter_by(batch_id=batch.id, is_active=True).all()}
    
    max_marks = float(test.max_marks)
    results = {"created": 0, "updated": 0, "errors": []}
    
    for record in results_data:
        student_id = record.get("student_id")
        marks = record.get("marks_obtained")
        remarks = record.get("remarks", "")
        
        if student_id not in valid_student_ids:
            results["errors"].append(f"Student {student_id} not found in batch")
            continue
        
        if marks is None:
            continue  # Skip if no marks provided
        
        if marks < 0 or marks > max_marks:
            results["errors"].append(f"Invalid marks {marks} for student {student_id}")
            continue
        
        # Check if result already exists
        existing = TestResult.query.filter_by(
            test_id=test_id,
            student_id=student_id,
        ).first()
        
        if existing:
            existing.marks_obtained = marks
            existing.remarks = remarks
            existing.is_active = True
            results["updated"] += 1
        else:
            result = TestResult(
                test_id=test_id,
                student_id=student_id,
                marks_obtained=marks,
                remarks=remarks,
                is_active=True,
            )
            db.session.add(result)
            results["created"] += 1
    
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ConflictError("Failed to save results") from exc
    
    return results


def get_teacher_dashboard_summary(user_id):
    """Get comprehensive dashboard summary for a teacher"""
    teacher = get_teacher_by_user_id(user_id)
    
    # Batches count
    active_batches = [b for b in teacher.batches if b.is_active]
    batches_count = len(active_batches)
    
    # Total students across all batches
    total_students = 0
    batch_ids = []
    for batch in active_batches:
        batch_ids.append(batch.id)
        total_students += Student.query.filter_by(batch_id=batch.id, is_active=True).count()
    
    # Today's attendance stats
    today = date.today()
    today_attendance = Attendance.query.filter(
        Attendance.batch_id.in_(batch_ids),
        Attendance.attendance_date == today,
        Attendance.is_active == True
    ).all()
    
    present_today = sum(1 for a in today_attendance if a.status == "present")
    attendance_rate = (present_today / len(today_attendance) * 100) if today_attendance else 0
    
    # Recent tests (last 30 days)
    thirty_days_ago = today - timedelta(days=30)
    recent_tests = Test.query.filter(
        Test.batch_id.in_(batch_ids),
        Test.test_date >= thirty_days_ago,
        Test.is_active == True
    ).count()
    
    # Pending results (tests with incomplete results)
    pending_results = 0
    tests = Test.query.filter(
        Test.batch_id.in_(batch_ids),
        Test.is_active == True
    ).all()
    
    for test in tests:
        batch_student_count = Student.query.filter_by(batch_id=test.batch_id, is_active=True).count()
        results_count = TestResult.query.filter_by(test_id=test.id, is_active=True).count()
        if results_count < batch_student_count:
            pending_results += 1
    
    # Upcoming tests (next 7 days)
    next_week = today + timedelta(days=7)
    upcoming_tests = Test.query.filter(
        Test.batch_id.in_(batch_ids),
        Test.test_date >= today,
        Test.test_date <= next_week,
        Test.is_active == True
    ).order_by(Test.test_date).all()
    
    # Recent activity - last 5 attendance records marked by this teacher
    recent_attendance = Attendance.query.filter_by(
        marked_by=user_id,
        is_active=True
    ).order_by(Attendance.created_at.desc()).limit(5).all()
    
    return {
        "teacher": {
            "id": teacher.id,
            "name": teacher.user.full_name if teacher.user else "Unknown",
            "specialization": teacher.specialization,
        },
        "stats": {
            "batches_count": batches_count,
            "total_students": total_students,
            "today_attendance_rate": round(attendance_rate, 1),
            "recent_tests": recent_tests,
            "pending_results": pending_results,
        },
        "upcoming_tests": [
            {
                "id": t.id,
                "title": t.title,
                "subject": t.subject,
                "test_date": t.test_date.isoformat(),
                "batch_name": t.batch.batch_name if t.batch else None,
            }
            for t in upcoming_tests
        ],
        "recent_activity": [
            {
                "type": "attendance",
                "batch_name": a.batch.batch_name if a.batch else None,
                "date": a.attendance_date.isoformat(),
                "count": Attendance.query.filter_by(
                    marked_by=user_id,
                    attendance_date=a.attendance_date,
                    batch_id=a.batch_id
                ).count(),
            }
            for a in recent_attendance
        ][:5],
        "batches": [
            {
                "id": b.id,
                "batch_name": b.batch_name,
                "year": b.year,
                "student_count": Student.query.filter_by(batch_id=b.id, is_active=True).count(),
            }
            for b in active_batches
        ],
    }


def get_student_profile(user_id, student_id):
    """Get detailed profile of a student (teacher must be assigned to the student's batch)"""
    teacher = get_teacher_by_user_id(user_id)

    student = Student.query.filter_by(id=student_id, is_active=True).first()
    if not student:
        raise ValidationError("Student not found", 404)

    batch = Batch.query.filter_by(id=student.batch_id, is_active=True).first()
    if not batch:
        raise ValidationError("Student's batch not found", 404)

    if teacher not in batch.teachers:
        raise ValidationError("You are not assigned to this student's batch", 403)

    # Attendance stats
    total_attendance = Attendance.query.filter_by(student_id=student.id, is_active=True).count()
    present_count = Attendance.query.filter_by(student_id=student.id, status="present", is_active=True).count()
    absent_count = Attendance.query.filter_by(student_id=student.id, status="absent", is_active=True).count()
    late_count = Attendance.query.filter_by(student_id=student.id, status="late", is_active=True).count()
    attendance_rate = (present_count / total_attendance * 100) if total_attendance > 0 else 0

    # Recent attendance (last 30 records)
    recent_attendance = Attendance.query.filter_by(
        student_id=student.id, is_active=True
    ).order_by(Attendance.attendance_date.desc()).limit(30).all()

    # Test results
    test_results = db.session.query(TestResult, Test).join(Test).filter(
        TestResult.student_id == student.id,
        TestResult.is_active == True,
        Test.is_active == True,
    ).order_by(Test.test_date.desc()).all()

    avg_marks = 0
    avg_max = 0
    if test_results:
        total_obtained = sum(float(r.marks_obtained) for r, _ in test_results if r.marks_obtained is not None)
        total_max = sum(float(t.max_marks) for _, t in test_results if t.max_marks is not None)
        avg_marks = total_obtained / len(test_results) if test_results else 0
        avg_max = total_max / len(test_results) if test_results else 0
    avg_percentage = (avg_marks / avg_max * 100) if avg_max > 0 else 0

    return {
        "student": {
            "id": student.id,
            "user_id": student.user_id,
            "full_name": student.user.full_name if student.user else "Unknown",
            "email": student.user.email if student.user else None,
            "phone_number": student.phone_number,
            "address": student.address,
            "date_of_birth": student.date_of_birth.isoformat() if student.date_of_birth else None,
            "enrollment_date": student.enrollment_date.isoformat() if student.enrollment_date else None,
            "is_active": student.is_active,
        },
        "batch": {
            "id": batch.id,
            "batch_name": batch.batch_name,
            "year": batch.year,
        },
        "attendance": {
            "total": total_attendance,
            "present": present_count,
            "absent": absent_count,
            "late": late_count,
            "rate": round(attendance_rate, 1),
            "recent": [
                {
                    "date": a.attendance_date.isoformat(),
                    "status": a.status,
                    "remarks": a.remarks,
                }
                for a in recent_attendance
            ],
        },
        "tests": {
            "total_taken": len(test_results),
            "avg_percentage": round(avg_percentage, 1),
            "results": [
                {
                    "test_id": t.id,
                    "title": t.title,
                    "subject": t.subject,
                    "test_date": t.test_date.isoformat() if t.test_date else None,
                    "max_marks": float(t.max_marks) if t.max_marks else 0,
                    "marks_obtained": float(r.marks_obtained) if r.marks_obtained is not None else None,
                    "percentage": round(float(r.marks_obtained) / float(t.max_marks) * 100, 1)
                    if r.marks_obtained is not None and t.max_marks
                    else None,
                    "remarks": r.remarks,
                }
                for r, t in test_results
            ],
        },
    }


def get_attendance_history(user_id, batch_id, start_date=None, end_date=None):
    """Get attendance history for a batch"""
    teacher = get_teacher_by_user_id(user_id)
    
    batch = Batch.query.filter_by(id=batch_id, is_active=True).first()
    if not batch:
        raise ValidationError("Batch not found", 404)
    
    if teacher not in batch.teachers:
        raise ValidationError("You are not assigned to this batch", 403)
    
    if start_date is None:
        start_date = date.today() - timedelta(days=30)
    if end_date is None:
        end_date = date.today()
    
    # Get all attendance records in date range
    attendance_records = Attendance.query.filter(
        Attendance.batch_id == batch_id,
        Attendance.attendance_date >= start_date,
        Attendance.attendance_date <= end_date,
        Attendance.is_active == True
    ).order_by(Attendance.attendance_date.desc()).all()
    
    # Group by date
    date_stats = {}
    for record in attendance_records:
        date_key = record.attendance_date.isoformat()
        if date_key not in date_stats:
            date_stats[date_key] = {"present": 0, "absent": 0, "late": 0, "excused": 0, "total": 0}
        date_stats[date_key][record.status] = date_stats[date_key].get(record.status, 0) + 1
        date_stats[date_key]["total"] += 1
    
    return {
        "batch": {
            "id": batch.id,
            "batch_name": batch.batch_name,
        },
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "daily_stats": [
            {
                "date": date_key,
                **stats,
                "attendance_rate": round(stats["present"] / stats["total"] * 100, 1) if stats["total"] > 0 else 0
            }
            for date_key, stats in sorted(date_stats.items(), reverse=True)
        ],
        "records": [r.to_dict() for r in attendance_records],
    }
