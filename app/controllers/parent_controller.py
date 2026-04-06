"""
Parent Controller - Handle HTTP requests for parent-specific operations
"""
from flask import request
from flask_jwt_extended import get_jwt_identity

from app.services.parent_service import (
    get_parent_children,
    get_child_details,
    get_child_fees,
    get_child_attendance,
    get_child_test_results,
    get_child_quiz_results,
    get_child_quiz_detail,
    get_parent_dashboard_summary,
)
from app.utils.response import api_response


def get_my_children_controller():
    """Get all children linked to the current parent"""
    current_user_id = get_jwt_identity()
    children = get_parent_children(current_user_id)
    return api_response(True, "Children fetched successfully", {"children": children}, 200)


def get_child_details_controller(student_id):
    """Get detailed information about a specific child"""
    current_user_id = get_jwt_identity()
    child = get_child_details(current_user_id, student_id)
    return api_response(True, "Child details fetched successfully", {"child": child}, 200)


def get_child_fees_controller(student_id):
    """Get fee information for a specific child"""
    current_user_id = get_jwt_identity()
    fees = get_child_fees(current_user_id, student_id)
    return api_response(True, "Fee information fetched successfully", {"fees": fees}, 200)


def get_child_attendance_controller(student_id):
    """Get attendance records for a specific child"""
    current_user_id = get_jwt_identity()
    days = request.args.get('days', default=30, type=int)
    if days < 1 or days > 365:
        days = 30
    attendance = get_child_attendance(current_user_id, student_id, days)
    return api_response(True, "Attendance records fetched successfully", {"attendance": attendance}, 200)


def get_child_test_results_controller(student_id):
    """Get test results for a specific child"""
    current_user_id = get_jwt_identity()
    results = get_child_test_results(current_user_id, student_id)
    return api_response(True, "Test results fetched successfully", {"test_results": results}, 200)


def get_child_quiz_results_controller(student_id):
    """Get quiz results for a specific child"""
    current_user_id = get_jwt_identity()
    results = get_child_quiz_results(current_user_id, student_id)
    return api_response(True, "Quiz results fetched successfully", {"quiz_results": results}, 200)


def get_child_quiz_detail_controller(student_id, quiz_id):
    """Get quiz detail for a specific child"""
    current_user_id = get_jwt_identity()
    quiz = get_child_quiz_detail(current_user_id, student_id, quiz_id)
    return api_response(True, "Quiz detail fetched successfully", {"quiz": quiz}, 200)


def get_parent_dashboard_controller():
    """Get comprehensive dashboard summary for the current parent"""
    current_user_id = get_jwt_identity()
    summary = get_parent_dashboard_summary(current_user_id)
    return api_response(True, "Dashboard summary fetched successfully", {"summary": summary}, 200)
