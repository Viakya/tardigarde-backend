"""Tests for batch-teacher assignment endpoints."""

import pytest


class TestAssignTeacher:
    """POST /api/v1/batches/<batch_id>/teachers"""

    def test_assign_teacher_success(self, client, auth_headers, seed_batch, seed_teacher):
        bid = seed_batch["id"]
        tid = seed_teacher["id"]
        resp = client.post(
            f"/api/v1/batches/{bid}/teachers",
            json={"teacher_id": tid},
            headers=auth_headers("director"),
        )
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["success"] is True

    def test_assign_teacher_duplicate(self, client, auth_headers, seed_batch, seed_teacher):
        bid = seed_batch["id"]
        tid = seed_teacher["id"]
        headers = auth_headers("director")

        client.post(f"/api/v1/batches/{bid}/teachers", json={"teacher_id": tid}, headers=headers)
        resp = client.post(f"/api/v1/batches/{bid}/teachers", json={"teacher_id": tid}, headers=headers)
        assert resp.status_code == 409

    def test_assign_teacher_missing_id(self, client, auth_headers, seed_batch):
        bid = seed_batch["id"]
        resp = client.post(
            f"/api/v1/batches/{bid}/teachers",
            json={},
            headers=auth_headers("director"),
        )
        assert resp.status_code == 400

    def test_assign_teacher_rbac(self, client, auth_headers, seed_batch, seed_teacher):
        bid = seed_batch["id"]
        resp = client.post(
            f"/api/v1/batches/{bid}/teachers",
            json={"teacher_id": seed_teacher["id"]},
            headers=auth_headers("student"),
        )
        assert resp.status_code == 403


class TestRemoveTeacher:
    """DELETE /api/v1/batches/<batch_id>/teachers/<teacher_id>"""

    def test_remove_teacher_success(self, client, auth_headers, seed_batch, seed_teacher):
        bid = seed_batch["id"]
        tid = seed_teacher["id"]
        headers = auth_headers("director")

        # Assign first
        client.post(f"/api/v1/batches/{bid}/teachers", json={"teacher_id": tid}, headers=headers)

        # Then remove
        resp = client.delete(f"/api/v1/batches/{bid}/teachers/{tid}", headers=headers)
        assert resp.status_code == 200


class TestListTeachersForBatch:
    """GET /api/v1/batches/<batch_id>/teachers"""

    def test_list_teachers_for_batch(self, client, auth_headers, seed_batch, seed_teacher):
        bid = seed_batch["id"]
        tid = seed_teacher["id"]
        headers = auth_headers("director")

        client.post(f"/api/v1/batches/{bid}/teachers", json={"teacher_id": tid}, headers=headers)

        resp = client.get(f"/api/v1/batches/{bid}/teachers", headers=headers)
        assert resp.status_code == 200
        body = resp.get_json()
        assert isinstance(body["data"]["teachers"], list)
        assert len(body["data"]["teachers"]) >= 1
