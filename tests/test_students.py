"""Tests for student endpoints."""

import pytest


class TestCreateStudent:
    """POST /api/v1/students"""

    def test_create_student_success(self, client, auth_headers, seed_users, seed_batch):
        payload = {
            "user_id": seed_users["student"]["id"],
            "batch_id": seed_batch["id"],
            "phone_number": "9876543210",
            "address": "123 Test Lane",
        }
        resp = client.post("/api/v1/students", json=payload, headers=auth_headers("director"))
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["success"] is True
        assert body["data"]["student"]["phone_number"] == "9876543210"
        assert body["data"]["student"]["batch_id"] == seed_batch["id"]

    def test_create_student_missing_user_id(self, client, auth_headers):
        resp = client.post(
            "/api/v1/students",
            json={"phone_number": "1234567890"},
            headers=auth_headers("director"),
        )
        assert resp.status_code == 400
        assert "user_id" in resp.get_json()["message"]

    def test_create_student_non_student_role(self, client, auth_headers, seed_users):
        """Creating a student profile for a non-student user should fail."""
        payload = {"user_id": seed_users["admin"]["id"]}
        resp = client.post("/api/v1/students", json=payload, headers=auth_headers("director"))
        assert resp.status_code == 400
        assert "student" in resp.get_json()["message"].lower()

    def test_create_student_duplicate(self, client, auth_headers, seed_student, seed_users):
        """Duplicate student profile for the same user must be rejected."""
        payload = {"user_id": seed_users["student"]["id"]}
        resp = client.post("/api/v1/students", json=payload, headers=auth_headers("director"))
        assert resp.status_code == 409

    def test_create_student_rbac_student_cannot_create(self, client, auth_headers):
        resp = client.post(
            "/api/v1/students",
            json={"user_id": 999},
            headers=auth_headers("student"),
        )
        assert resp.status_code == 403

    def test_create_student_with_discount(self, client, auth_headers, seed_users, seed_batch):
        payload = {
            "user_id": seed_users["student"]["id"],
            "batch_id": seed_batch["id"],
            "discount_percent": 15.5,
        }
        resp = client.post("/api/v1/students", json=payload, headers=auth_headers("director"))
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["data"]["student"]["discount_percent"] == 15.5


class TestListStudents:
    """GET /api/v1/students"""

    def test_list_students_empty(self, client, auth_headers):
        resp = client.get("/api/v1/students", headers=auth_headers("director"))
        assert resp.status_code == 200
        body = resp.get_json()
        assert isinstance(body["data"]["students"], list)
        assert "pagination" in body["data"]

    def test_list_students_with_data(self, client, auth_headers, seed_student):
        resp = client.get("/api/v1/students", headers=auth_headers("director"))
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["data"]["pagination"]["total"] >= 1

    def test_list_students_pagination(self, client, auth_headers, seed_student):
        resp = client.get(
            "/api/v1/students?page=1&per_page=1",
            headers=auth_headers("director"),
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["data"]["pagination"]["per_page"] == 1

    def test_list_students_invalid_page(self, client, auth_headers):
        resp = client.get(
            "/api/v1/students?page=0",
            headers=auth_headers("director"),
        )
        assert resp.status_code == 400


class TestGetStudent:
    """GET /api/v1/students/<id>"""

    def test_get_student_success(self, client, auth_headers, seed_student):
        sid = seed_student["id"]
        resp = client.get(f"/api/v1/students/{sid}", headers=auth_headers("director"))
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["data"]["student"]["id"] == sid

    def test_get_student_not_found(self, client, auth_headers):
        resp = client.get("/api/v1/students/99999", headers=auth_headers("director"))
        assert resp.status_code == 404


class TestUpdateStudent:
    """PUT /api/v1/students/<id>"""

    def test_update_student_phone(self, client, auth_headers, seed_student):
        sid = seed_student["id"]
        resp = client.put(
            f"/api/v1/students/{sid}",
            json={"phone_number": "1111111111"},
            headers=auth_headers("director"),
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["data"]["student"]["phone_number"] == "1111111111"

    def test_update_student_unsupported_field(self, client, auth_headers, seed_student):
        sid = seed_student["id"]
        resp = client.put(
            f"/api/v1/students/{sid}",
            json={"user_id": 999},
            headers=auth_headers("director"),
        )
        assert resp.status_code == 400
        assert "Unsupported" in resp.get_json()["message"]

    def test_update_student_empty_payload(self, client, auth_headers, seed_student):
        sid = seed_student["id"]
        resp = client.put(
            f"/api/v1/students/{sid}",
            json={},
            headers=auth_headers("director"),
        )
        assert resp.status_code == 400


class TestDeleteStudent:
    """DELETE /api/v1/students/<id>"""

    def test_delete_student_success(self, client, auth_headers, seed_student):
        sid = seed_student["id"]
        resp = client.delete(f"/api/v1/students/{sid}", headers=auth_headers("director"))
        assert resp.status_code == 200

        # Verify soft-deleted — should now 404
        get_resp = client.get(f"/api/v1/students/{sid}", headers=auth_headers("director"))
        assert get_resp.status_code == 404


class TestStudentParentLink:
    """POST/DELETE for parent linking"""

    def test_connect_parent(self, client, auth_headers, seed_student, seed_users):
        sid = seed_student["id"]
        parent = seed_users["parent"]
        resp = client.post(
            f"/api/v1/students/{sid}/parents",
            json={"parent_user_id": parent["id"]},
            headers=auth_headers("director"),
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert parent["id"] in body["data"]["student"]["parent_user_ids"]

    def test_connect_parent_duplicate(self, client, auth_headers, seed_student, seed_users):
        sid = seed_student["id"]
        parent = seed_users["parent"]
        headers = auth_headers("director")

        # Connect once
        client.post(f"/api/v1/students/{sid}/parents", json={"parent_user_id": parent["id"]}, headers=headers)

        # Connect again — should 409
        resp = client.post(f"/api/v1/students/{sid}/parents", json={"parent_user_id": parent["id"]}, headers=headers)
        assert resp.status_code == 409

    def test_disconnect_parent(self, client, auth_headers, seed_student, seed_users):
        sid = seed_student["id"]
        parent = seed_users["parent"]
        headers = auth_headers("director")

        # Connect then disconnect
        client.post(f"/api/v1/students/{sid}/parents", json={"parent_user_id": parent["id"]}, headers=headers)
        resp = client.delete(f"/api/v1/students/{sid}/parents/{parent['id']}", headers=headers)
        assert resp.status_code == 200

    def test_connect_non_parent_role(self, client, auth_headers, seed_student, seed_users):
        """Linking a user without parent role should fail."""
        sid = seed_student["id"]
        admin = seed_users["admin"]
        resp = client.post(
            f"/api/v1/students/{sid}/parents",
            json={"parent_user_id": admin["id"]},
            headers=auth_headers("director"),
        )
        assert resp.status_code == 400
