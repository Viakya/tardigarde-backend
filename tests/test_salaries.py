"""Tests for salary endpoints."""

import pytest


class TestCreateSalary:
    """POST /api/v1/salaries"""

    def test_create_salary_success(self, client, auth_headers, seed_teacher):
        payload = {
            "teacher_id": seed_teacher["id"],
            "amount": 25000,
            "payment_date": "2026-04-01",
            "payment_method": "bank_transfer",
        }
        resp = client.post("/api/v1/salaries", json=payload, headers=auth_headers("director"))
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["success"] is True
        assert body["data"]["salary"]["amount"] == 25000.0

    def test_create_salary_missing_fields(self, client, auth_headers):
        resp = client.post("/api/v1/salaries", json={"amount": 10000}, headers=auth_headers("director"))
        assert resp.status_code == 400

    def test_create_salary_rbac(self, client, auth_headers, seed_teacher):
        payload = {"teacher_id": seed_teacher["id"], "amount": 25000, "payment_method": "cash"}
        resp = client.post("/api/v1/salaries", json=payload, headers=auth_headers("student"))
        assert resp.status_code == 403

    def test_create_salary_manager_allowed(self, client, auth_headers, seed_teacher):
        payload = {"teacher_id": seed_teacher["id"], "amount": 20000, "payment_method": "cash"}
        resp = client.post("/api/v1/salaries", json=payload, headers=auth_headers("manager"))
        assert resp.status_code == 201


class TestListSalaries:
    """GET /api/v1/salaries"""

    def test_list_salaries(self, client, auth_headers):
        resp = client.get("/api/v1/salaries", headers=auth_headers("director"))
        assert resp.status_code == 200
        assert isinstance(resp.get_json()["data"]["salaries"], list)

    def test_list_salaries_with_teacher_filter(self, client, auth_headers, seed_teacher):
        client.post("/api/v1/salaries", json={"teacher_id": seed_teacher["id"], "amount": 30000, "payment_method": "cash"}, headers=auth_headers("director"))
        resp = client.get(f"/api/v1/salaries?teacher_id={seed_teacher['id']}", headers=auth_headers("director"))
        assert resp.status_code == 200


class TestUpdateSalary:
    """PUT /api/v1/salaries/<id>"""

    def test_update_salary(self, client, auth_headers, seed_teacher):
        create_resp = client.post("/api/v1/salaries", json={"teacher_id": seed_teacher["id"], "amount": 18000, "payment_method": "cash"}, headers=auth_headers("director"))
        sid = create_resp.get_json()["data"]["salary"]["id"]
        resp = client.put(f"/api/v1/salaries/{sid}", json={"amount": 22000}, headers=auth_headers("director"))
        assert resp.status_code == 200
        assert resp.get_json()["data"]["salary"]["amount"] == 22000.0


class TestDeleteSalary:
    """DELETE /api/v1/salaries/<id>"""

    def test_delete_salary(self, client, auth_headers, seed_teacher):
        create_resp = client.post("/api/v1/salaries", json={"teacher_id": seed_teacher["id"], "amount": 12000, "payment_method": "cash"}, headers=auth_headers("director"))
        sid = create_resp.get_json()["data"]["salary"]["id"]
        resp = client.delete(f"/api/v1/salaries/{sid}", headers=auth_headers("director"))
        assert resp.status_code == 200


class TestSalarySummary:
    """GET /api/v1/salaries/summary"""

    def test_salary_summary(self, client, auth_headers):
        resp = client.get("/api/v1/salaries/summary", headers=auth_headers("director"))
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True

    def test_salary_summary_rbac(self, client, auth_headers):
        resp = client.get("/api/v1/salaries/summary", headers=auth_headers("student"))
        assert resp.status_code == 403
