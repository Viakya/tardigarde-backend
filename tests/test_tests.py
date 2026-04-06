"""Tests for test & test-result endpoints."""

import pytest


class TestCreateTest:
    """POST /api/v1/tests"""

    def test_create_test_success(self, client, auth_headers, seed_batch):
        payload = {
            "title": "Mid-term Exam",
            "batch_id": seed_batch["id"],
            "test_date": "2026-05-01",
            "max_marks": 100,
        }
        resp = client.post("/api/v1/tests", json=payload, headers=auth_headers("coach"))
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["success"] is True
        assert body["data"]["test"]["title"] == "Mid-term Exam"

    def test_create_test_missing_fields(self, client, auth_headers):
        resp = client.post("/api/v1/tests", json={"title": "Only name"}, headers=auth_headers("coach"))
        assert resp.status_code == 400

    def test_create_test_rbac(self, client, auth_headers, seed_batch):
        payload = {"title": "Nope", "batch_id": seed_batch["id"], "max_marks": 50, "test_date": "2026-05-01"}
        resp = client.post("/api/v1/tests", json=payload, headers=auth_headers("student"))
        assert resp.status_code == 403


class TestListTests:
    """GET /api/v1/tests"""

    def test_list_tests(self, client, auth_headers):
        resp = client.get("/api/v1/tests", headers=auth_headers("director"))
        assert resp.status_code == 200
        body = resp.get_json()
        assert isinstance(body["data"]["tests"], list)


class TestCreateTestResult:
    """POST /api/v1/test-results"""

    def test_create_test_result_success(self, client, auth_headers, seed_batch, seed_student):
        # Create a test first
        test_resp = client.post("/api/v1/tests", json={
            "title": "Unit Test Exam",
            "batch_id": seed_batch["id"],
            "max_marks": 50,
            "test_date": "2026-05-15",
        }, headers=auth_headers("coach"))
        test_id = test_resp.get_json()["data"]["test"]["id"]

        payload = {
            "test_id": test_id,
            "student_id": seed_student["id"],
            "marks_obtained": 42,
        }
        resp = client.post("/api/v1/test-results", json=payload, headers=auth_headers("coach"))
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["data"]["test_result"]["marks_obtained"] == 42.0


class TestListTestResults:
    """GET /api/v1/test-results"""

    def test_list_test_results(self, client, auth_headers):
        resp = client.get("/api/v1/test-results", headers=auth_headers("director"))
        assert resp.status_code == 200
        body = resp.get_json()
        assert isinstance(body["data"]["test_results"], list)


class TestPerformanceMetrics:
    """GET /api/v1/tests/performance-metrics"""

    def test_performance_metrics(self, client, auth_headers):
        resp = client.get("/api/v1/tests/performance-metrics", headers=auth_headers("director"))
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True
