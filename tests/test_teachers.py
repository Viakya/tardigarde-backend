"""Tests for teacher endpoints."""

import pytest


class TestCreateTeacher:
    """POST /api/v1/teachers"""

    def test_create_teacher_success(self, client, auth_headers, seed_users):
        payload = {
            "user_id": seed_users["coach"]["id"],
            "specialization": "Physics",
            "phone_number": "9000000001",
        }
        resp = client.post("/api/v1/teachers", json=payload, headers=auth_headers("director"))
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["success"] is True
        assert body["data"]["teacher"]["specialization"] == "Physics"

    def test_create_teacher_non_coach_user(self, client, auth_headers, seed_users):
        """Creating a teacher for a user without 'coach' role should fail."""
        payload = {"user_id": seed_users["student"]["id"]}
        resp = client.post("/api/v1/teachers", json=payload, headers=auth_headers("director"))
        assert resp.status_code == 400

    def test_create_teacher_missing_user_id(self, client, auth_headers):
        resp = client.post(
            "/api/v1/teachers",
            json={"specialization": "Math"},
            headers=auth_headers("director"),
        )
        assert resp.status_code == 400

    def test_create_teacher_duplicate(self, client, auth_headers, seed_teacher, seed_users):
        payload = {"user_id": seed_users["coach"]["id"]}
        resp = client.post("/api/v1/teachers", json=payload, headers=auth_headers("director"))
        assert resp.status_code == 409

    def test_create_teacher_rbac(self, client, auth_headers, seed_users):
        payload = {"user_id": seed_users["coach"]["id"]}
        resp = client.post("/api/v1/teachers", json=payload, headers=auth_headers("student"))
        assert resp.status_code == 403


class TestListTeachers:
    """GET /api/v1/teachers"""

    def test_list_teachers_empty(self, client, auth_headers):
        resp = client.get("/api/v1/teachers", headers=auth_headers("director"))
        assert resp.status_code == 200
        body = resp.get_json()
        assert isinstance(body["data"]["teachers"], list)

    def test_list_teachers_with_data(self, client, auth_headers, seed_teacher):
        resp = client.get("/api/v1/teachers", headers=auth_headers("director"))
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["data"]["pagination"]["total"] >= 1


class TestGetTeacher:
    """GET /api/v1/teachers/<id>"""

    def test_get_teacher_success(self, client, auth_headers, seed_teacher):
        tid = seed_teacher["id"]
        resp = client.get(f"/api/v1/teachers/{tid}", headers=auth_headers("director"))
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["data"]["teacher"]["id"] == tid

    def test_get_teacher_not_found(self, client, auth_headers):
        resp = client.get("/api/v1/teachers/99999", headers=auth_headers("director"))
        assert resp.status_code == 404


class TestUpdateTeacher:
    """PUT /api/v1/teachers/<id>"""

    def test_update_teacher_specialization(self, client, auth_headers, seed_teacher):
        tid = seed_teacher["id"]
        resp = client.put(
            f"/api/v1/teachers/{tid}",
            json={"specialization": "Chemistry"},
            headers=auth_headers("director"),
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["data"]["teacher"]["specialization"] == "Chemistry"

    def test_update_teacher_rbac(self, client, auth_headers, seed_teacher):
        tid = seed_teacher["id"]
        resp = client.put(
            f"/api/v1/teachers/{tid}",
            json={"specialization": "Hacked"},
            headers=auth_headers("student"),
        )
        assert resp.status_code == 403


class TestDeleteTeacher:
    """DELETE /api/v1/teachers/<id>"""

    def test_delete_teacher(self, client, auth_headers, seed_teacher):
        tid = seed_teacher["id"]
        resp = client.delete(f"/api/v1/teachers/{tid}", headers=auth_headers("director"))
        assert resp.status_code == 200

        # Verify soft-deleted
        get_resp = client.get(f"/api/v1/teachers/{tid}", headers=auth_headers("director"))
        assert get_resp.status_code == 404
