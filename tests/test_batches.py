"""Tests for batch endpoints."""

import pytest


class TestCreateBatch:
    """POST /api/v1/batches"""

    def test_create_batch_success(self, client, auth_headers):
        payload = {
            "batch_name": "Science Plus",
            "year": 2026,
            "batch_cost": 20000,
        }
        resp = client.post("/api/v1/batches", json=payload, headers=auth_headers("director"))
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["success"] is True
        assert body["data"]["batch"]["batch_name"] == "Science Plus"
        assert body["data"]["batch"]["year"] == 2026
        assert body["data"]["batch"]["batch_cost"] == 20000.0

    def test_create_batch_manager_allowed(self, client, auth_headers):
        payload = {"batch_name": "Manager Batch", "year": 2026, "batch_cost": 10000}
        resp = client.post("/api/v1/batches", json=payload, headers=auth_headers("manager"))
        assert resp.status_code == 201

    def test_create_batch_duplicate(self, client, auth_headers):
        payload = {"batch_name": "Dup Batch", "year": 2026, "batch_cost": 10000}
        headers = auth_headers("director")
        resp1 = client.post("/api/v1/batches", json=payload, headers=headers)
        assert resp1.status_code == 201

        resp2 = client.post("/api/v1/batches", json=payload, headers=headers)
        assert resp2.status_code == 409

    def test_create_batch_missing_name(self, client, auth_headers):
        resp = client.post(
            "/api/v1/batches",
            json={"year": 2026},
            headers=auth_headers("director"),
        )
        assert resp.status_code == 400

    def test_create_batch_rbac_student(self, client, auth_headers):
        payload = {"batch_name": "No Way", "year": 2026}
        resp = client.post("/api/v1/batches", json=payload, headers=auth_headers("student"))
        assert resp.status_code == 403

    def test_create_batch_rbac_coach(self, client, auth_headers):
        payload = {"batch_name": "No Way Coach", "year": 2026}
        resp = client.post("/api/v1/batches", json=payload, headers=auth_headers("coach"))
        assert resp.status_code == 403


class TestListBatches:
    """GET /api/v1/batches"""

    def test_list_batches_empty(self, client, auth_headers):
        resp = client.get("/api/v1/batches", headers=auth_headers("director"))
        assert resp.status_code == 200
        body = resp.get_json()
        assert isinstance(body["data"]["batches"], list)
        assert "pagination" in body["data"]

    def test_list_batches_with_data(self, client, auth_headers, seed_batch):
        resp = client.get("/api/v1/batches", headers=auth_headers("director"))
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["data"]["pagination"]["total"] >= 1

    def test_list_batches_pagination(self, client, auth_headers, seed_batch):
        resp = client.get("/api/v1/batches?page=1&per_page=1", headers=auth_headers("director"))
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["data"]["pagination"]["per_page"] == 1


class TestGetBatch:
    """GET /api/v1/batches/<id>"""

    def test_get_batch_success(self, client, auth_headers, seed_batch):
        bid = seed_batch["id"]
        resp = client.get(f"/api/v1/batches/{bid}", headers=auth_headers("director"))
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["data"]["batch"]["id"] == bid

    def test_get_batch_not_found(self, client, auth_headers):
        resp = client.get("/api/v1/batches/99999", headers=auth_headers("director"))
        assert resp.status_code == 404


class TestUpdateBatch:
    """PUT /api/v1/batches/<id>"""

    def test_update_batch_name(self, client, auth_headers, seed_batch):
        bid = seed_batch["id"]
        resp = client.put(
            f"/api/v1/batches/{bid}",
            json={"batch_name": "Updated Batch"},
            headers=auth_headers("director"),
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["data"]["batch"]["batch_name"] == "Updated Batch"

    def test_update_batch_cost(self, client, auth_headers, seed_batch):
        bid = seed_batch["id"]
        resp = client.put(
            f"/api/v1/batches/{bid}",
            json={"batch_cost": 25000},
            headers=auth_headers("director"),
        )
        assert resp.status_code == 200
        assert resp.get_json()["data"]["batch"]["batch_cost"] == 25000.0

    def test_update_batch_rbac(self, client, auth_headers, seed_batch):
        bid = seed_batch["id"]
        resp = client.put(
            f"/api/v1/batches/{bid}",
            json={"batch_name": "Hacked"},
            headers=auth_headers("student"),
        )
        assert resp.status_code == 403


class TestDeleteBatch:
    """DELETE /api/v1/batches/<id>"""

    def test_delete_batch(self, client, auth_headers, seed_batch):
        bid = seed_batch["id"]
        resp = client.delete(f"/api/v1/batches/{bid}", headers=auth_headers("director"))
        assert resp.status_code == 200

        # Verify soft-deleted
        get_resp = client.get(f"/api/v1/batches/{bid}", headers=auth_headers("director"))
        assert get_resp.status_code == 404


class TestBatchProfile:
    """GET /api/v1/batches/<id>/profile"""

    def test_batch_profile(self, client, auth_headers, seed_batch):
        bid = seed_batch["id"]
        resp = client.get(f"/api/v1/batches/{bid}/profile", headers=auth_headers("director"))
        assert resp.status_code == 200
        body = resp.get_json()
        assert "financial_summary" in body["data"]
        assert "students" in body["data"]
        assert "teachers" in body["data"]
        assert body["data"]["batch"]["id"] == bid

    def test_batch_profile_rbac(self, client, auth_headers, seed_batch):
        bid = seed_batch["id"]
        resp = client.get(f"/api/v1/batches/{bid}/profile", headers=auth_headers("student"))
        assert resp.status_code == 403
