"""Tests for attendance endpoints."""

import pytest
from datetime import date


class TestCreateAttendance:
    """POST /api/v1/attendance"""

    def test_create_attendance_success(self, client, auth_headers, seed_student, seed_batch):
        payload = {
            "student_id": seed_student["id"],
            "batch_id": seed_batch["id"],
            "attendance_date": date.today().isoformat(),
            "status": "present",
        }
        resp = client.post("/api/v1/attendance", json=payload, headers=auth_headers("coach"))
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["success"] is True
        assert body["data"]["attendance"]["status"] == "present"

    def test_create_attendance_director(self, client, auth_headers, seed_student, seed_batch):
        payload = {
            "student_id": seed_student["id"],
            "batch_id": seed_batch["id"],
            "attendance_date": "2026-03-15",
            "status": "absent",
        }
        resp = client.post("/api/v1/attendance", json=payload, headers=auth_headers("director"))
        assert resp.status_code == 201

    def test_create_attendance_missing_fields(self, client, auth_headers):
        resp = client.post(
            "/api/v1/attendance",
            json={"status": "present"},
            headers=auth_headers("coach"),
        )
        assert resp.status_code == 400

    def test_create_attendance_rbac_student(self, client, auth_headers, seed_student, seed_batch):
        payload = {
            "student_id": seed_student["id"],
            "batch_id": seed_batch["id"],
            "status": "present",
        }
        resp = client.post("/api/v1/attendance", json=payload, headers=auth_headers("student"))
        assert resp.status_code == 403

    def test_create_attendance_duplicate_date(self, client, auth_headers, seed_student, seed_batch):
        payload = {
            "student_id": seed_student["id"],
            "batch_id": seed_batch["id"],
            "attendance_date": "2026-06-01",
            "status": "present",
        }
        headers = auth_headers("coach")
        resp1 = client.post("/api/v1/attendance", json=payload, headers=headers)
        assert resp1.status_code == 201

        resp2 = client.post("/api/v1/attendance", json=payload, headers=headers)
        assert resp2.status_code in (400, 409, 500)  # Unique constraint violation


class TestListAttendance:
    """GET /api/v1/attendance"""

    def test_list_attendance(self, client, auth_headers):
        resp = client.get("/api/v1/attendance", headers=auth_headers("director"))
        assert resp.status_code == 200
        body = resp.get_json()
        assert isinstance(body["data"]["attendance"], list)

    def test_list_attendance_with_filters(self, client, auth_headers, seed_student, seed_batch):
        # Create an attendance first
        client.post(
            "/api/v1/attendance",
            json={
                "student_id": seed_student["id"],
                "batch_id": seed_batch["id"],
                "attendance_date": "2026-05-10",
                "status": "present",
            },
            headers=auth_headers("coach"),
        )

        resp = client.get(
            f"/api/v1/attendance?batch_id={seed_batch['id']}",
            headers=auth_headers("director"),
        )
        assert resp.status_code == 200

    def test_list_attendance_invalid_date_filter(self, client, auth_headers):
        resp = client.get(
            "/api/v1/attendance?attendance_date=not-a-date",
            headers=auth_headers("director"),
        )
        assert resp.status_code == 400


class TestGetAttendance:
    """GET /api/v1/attendance/<id>"""

    def test_get_attendance_success(self, client, auth_headers, seed_student, seed_batch):
        # Create one
        create_resp = client.post(
            "/api/v1/attendance",
            json={
                "student_id": seed_student["id"],
                "batch_id": seed_batch["id"],
                "attendance_date": "2026-07-01",
                "status": "present",
            },
            headers=auth_headers("coach"),
        )
        aid = create_resp.get_json()["data"]["attendance"]["id"]

        resp = client.get(f"/api/v1/attendance/{aid}", headers=auth_headers("director"))
        assert resp.status_code == 200
        assert resp.get_json()["data"]["attendance"]["id"] == aid


class TestUpdateAttendance:
    """PUT /api/v1/attendance/<id>"""

    def test_update_attendance_status(self, client, auth_headers, seed_student, seed_batch):
        # Create one
        create_resp = client.post(
            "/api/v1/attendance",
            json={
                "student_id": seed_student["id"],
                "batch_id": seed_batch["id"],
                "attendance_date": "2026-08-01",
                "status": "present",
            },
            headers=auth_headers("coach"),
        )
        aid = create_resp.get_json()["data"]["attendance"]["id"]

        resp = client.put(
            f"/api/v1/attendance/{aid}",
            json={"status": "absent"},
            headers=auth_headers("coach"),
        )
        assert resp.status_code == 200
        assert resp.get_json()["data"]["attendance"]["status"] == "absent"


class TestDeleteAttendance:
    """DELETE /api/v1/attendance/<id>"""

    def test_delete_attendance(self, client, auth_headers, seed_student, seed_batch):
        create_resp = client.post(
            "/api/v1/attendance",
            json={
                "student_id": seed_student["id"],
                "batch_id": seed_batch["id"],
                "attendance_date": "2026-09-01",
                "status": "present",
            },
            headers=auth_headers("coach"),
        )
        aid = create_resp.get_json()["data"]["attendance"]["id"]

        resp = client.delete(f"/api/v1/attendance/{aid}", headers=auth_headers("director"))
        assert resp.status_code == 200

    def test_delete_attendance_rbac(self, client, auth_headers, seed_student, seed_batch):
        create_resp = client.post(
            "/api/v1/attendance",
            json={
                "student_id": seed_student["id"],
                "batch_id": seed_batch["id"],
                "attendance_date": "2026-09-02",
                "status": "present",
            },
            headers=auth_headers("coach"),
        )
        aid = create_resp.get_json()["data"]["attendance"]["id"]

        # Coach is not allowed to delete, only director
        resp = client.delete(f"/api/v1/attendance/{aid}", headers=auth_headers("coach"))
        assert resp.status_code == 403
