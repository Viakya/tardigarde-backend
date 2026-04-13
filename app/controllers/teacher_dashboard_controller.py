"""
Teacher Dashboard Controller - HTTP handlers for teacher-specific operations
"""
from datetime import datetime
from flask_jwt_extended import get_jwt_identity

from app.utils.response import api_response
from app.services.teacher_dashboard_service import (
    get_teacher_batches,
    get_batch_students,
    get_batch_attendance,
    mark_batch_attendance,
    get_batch_tests,
    create_test,
    get_test_results,
    save_test_results,
    get_teacher_dashboard_summary,
    get_attendance_history,
    get_student_profile,
    get_batch_quiz_performance,
)


def get_dashboard_summary_controller():
    """Get teacher dashboard summary"""
    user_id = get_jwt_identity()
    result = get_teacher_dashboard_summary(user_id)
    return api_response(True, "Dashboard summary retrieved", data=result)


def get_my_batches_controller():
    """Get all batches assigned to the teacher"""
    user_id = get_jwt_identity()
    result = get_teacher_batches(user_id)
    return api_response(True, "Batches retrieved", data={"batches": result})


def get_batch_students_controller(batch_id):
    """Get all students in a batch"""
    user_id = get_jwt_identity()
    result = get_batch_students(user_id, batch_id)
    return api_response(True, "Students retrieved", data=result)


def get_batch_attendance_controller(batch_id, request):
    """Get attendance for a batch on a specific date"""
    user_id = get_jwt_identity()
    
    date_str = request.args.get("date")
    attendance_date = None
    if date_str:
        try:
            attendance_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return api_response(False, "Invalid date format. Use YYYY-MM-DD", status_code=400)
    
    result = get_batch_attendance(user_id, batch_id, attendance_date)
    return api_response(True, "Attendance retrieved", data=result)


def mark_attendance_controller(batch_id, request):
    """Mark attendance for students in a batch"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return api_response(False, "Request body required", status_code=400)
    
    date_str = data.get("date")
    attendance_data = data.get("attendance", [])
    
    if not date_str:
        return api_response(False, "Date is required", status_code=400)
    
    if not attendance_data:
        return api_response(False, "Attendance data is required", status_code=400)
    
    try:
        attendance_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return api_response(False, "Invalid date format. Use YYYY-MM-DD", status_code=400)
    
    result = mark_batch_attendance(user_id, batch_id, attendance_date, attendance_data)
    return api_response(True, "Attendance saved successfully", data=result)


def get_batch_tests_controller(batch_id):
    """Get all tests for a batch"""
    user_id = get_jwt_identity()
    result = get_batch_tests(user_id, batch_id)
    return api_response(True, "Tests retrieved", data=result)


def create_test_controller(batch_id, request):
    """Create a new test for a batch"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return api_response(False, "Request body required", status_code=400)
    
    required_fields = ["title", "max_marks", "test_date"]
    for field in required_fields:
        if not data.get(field):
            return api_response(False, f"{field} is required", status_code=400)
    
    try:
        data["test_date"] = datetime.strptime(data["test_date"], "%Y-%m-%d").date()
    except ValueError:
        return api_response(False, "Invalid date format. Use YYYY-MM-DD", status_code=400)
    
    test = create_test(user_id, batch_id, data)
    return api_response(True, "Test created successfully", data={"test": test.to_dict()}, status_code=201)


def get_test_results_controller(test_id):
    """Get results for a test"""
    user_id = get_jwt_identity()
    result = get_test_results(user_id, test_id)
    return api_response(True, "Test results retrieved", data=result)


def save_test_results_controller(test_id, request):
    """Save test results for students"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return api_response(False, "Request body required", status_code=400)
    
    results_data = data.get("results", [])
    if not results_data:
        return api_response(False, "Results data is required", status_code=400)
    
    result = save_test_results(user_id, test_id, results_data)
    return api_response(True, "Results saved successfully", data=result)


def get_attendance_history_controller(batch_id, request):
    """Get attendance history for a batch"""
    user_id = get_jwt_identity()
    
    start_date = None
    end_date = None
    
    start_str = request.args.get("start_date")
    end_str = request.args.get("end_date")
    
    if start_str:
        try:
            start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
        except ValueError:
            return api_response(False, "Invalid start_date format. Use YYYY-MM-DD", status_code=400)
    
    if end_str:
        try:
            end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
        except ValueError:
            return api_response(False, "Invalid end_date format. Use YYYY-MM-DD", status_code=400)
    
    result = get_attendance_history(user_id, batch_id, start_date, end_date)
    return api_response(True, "Attendance history retrieved", data=result)


def get_student_profile_controller(student_id):
    """Get detailed student profile (only for students in teacher's batches)"""
    user_id = get_jwt_identity()
    result = get_student_profile(user_id, student_id)
    return api_response(True, "Student profile retrieved", data=result)


def get_batch_quiz_performance_controller(batch_id):
    """Get quiz reports and rankings for a batch"""
    user_id = get_jwt_identity()
    result = get_batch_quiz_performance(user_id, batch_id)
    return api_response(True, "Quiz performance retrieved", data=result)
