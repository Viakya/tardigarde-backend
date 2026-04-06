"""Tests for reporting/analytics endpoints."""

import pytest


class TestMonthlyAttendanceReport:
    """GET /api/v1/reports/monthly-attendance"""

    def test_monthly_attendance(self, client, auth_headers):
        resp = client.get("/api/v1/reports/monthly-attendance", headers=auth_headers("director"))
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True

    def test_monthly_attendance_with_year(self, client, auth_headers):
        resp = client.get("/api/v1/reports/monthly-attendance?year=2026", headers=auth_headers("director"))
        assert resp.status_code == 200

    def test_monthly_attendance_invalid_year(self, client, auth_headers):
        resp = client.get("/api/v1/reports/monthly-attendance?year=abc", headers=auth_headers("director"))
        assert resp.status_code == 400

    def test_monthly_attendance_rbac(self, client, auth_headers):
        resp = client.get("/api/v1/reports/monthly-attendance", headers=auth_headers("student"))
        assert resp.status_code == 403


class TestRevenueByMonth:
    """GET /api/v1/reports/revenue-by-month"""

    def test_revenue_by_month(self, client, auth_headers):
        resp = client.get("/api/v1/reports/revenue-by-month", headers=auth_headers("director"))
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True

    def test_revenue_by_month_rbac(self, client, auth_headers):
        resp = client.get("/api/v1/reports/revenue-by-month", headers=auth_headers("coach"))
        assert resp.status_code == 403


class TestSalaryExpenseByMonth:
    """GET /api/v1/reports/salary-expense-by-month"""

    def test_salary_expense(self, client, auth_headers):
        resp = client.get("/api/v1/reports/salary-expense-by-month", headers=auth_headers("director"))
        assert resp.status_code == 200

    def test_salary_expense_rbac(self, client, auth_headers):
        resp = client.get("/api/v1/reports/salary-expense-by-month", headers=auth_headers("student"))
        assert resp.status_code == 403


class TestBatchStrength:
    """GET /api/v1/reports/batch-strength"""

    def test_batch_strength(self, client, auth_headers):
        resp = client.get("/api/v1/reports/batch-strength", headers=auth_headers("director"))
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True

    def test_batch_strength_coach_allowed(self, client, auth_headers):
        resp = client.get("/api/v1/reports/batch-strength", headers=auth_headers("coach"))
        assert resp.status_code == 200


class TestActiveVsInactive:
    """GET /api/v1/reports/active-vs-inactive"""

    def test_active_vs_inactive(self, client, auth_headers):
        resp = client.get("/api/v1/reports/active-vs-inactive", headers=auth_headers("director"))
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True

    def test_active_vs_inactive_rbac(self, client, auth_headers):
        resp = client.get("/api/v1/reports/active-vs-inactive", headers=auth_headers("student"))
        assert resp.status_code == 403
