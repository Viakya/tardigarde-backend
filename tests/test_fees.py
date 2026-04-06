"""Tests for fee payment endpoints."""

import pytest


class TestCreateFeePayment:
    """POST /api/v1/fee-payments"""

    def test_create_fee_payment_success(self, client, auth_headers, seed_student):
        payload = {
            "student_id": seed_student["id"],
            "amount": 5000,
            "payment_date": "2026-04-01",
            "payment_method": "cash",
        }
        resp = client.post("/api/v1/fee-payments", json=payload, headers=auth_headers("director"))
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["success"] is True
        assert body["data"]["fee_payment"]["amount"] == 5000.0
        assert body["data"]["fee_payment"]["payment_method"] == "cash"

    def test_create_fee_payment_missing_amount(self, client, auth_headers, seed_student):
        payload = {"student_id": seed_student["id"]}
        resp = client.post("/api/v1/fee-payments", json=payload, headers=auth_headers("director"))
        assert resp.status_code == 400

    def test_create_fee_payment_no_token(self, client):
        payload = {"student_id": 1, "amount": 5000, "payment_method": "cash"}
        resp = client.post("/api/v1/fee-payments", json=payload)
        assert resp.status_code == 401


class TestListFeePayments:
    """GET /api/v1/fee-payments"""

    def test_list_fee_payments(self, client, auth_headers):
        resp = client.get("/api/v1/fee-payments", headers=auth_headers("director"))
        assert resp.status_code == 200
        body = resp.get_json()
        assert isinstance(body["data"]["fee_payments"], list)

    def test_list_fee_payments_with_student_filter(self, client, auth_headers, seed_student):
        client.post("/api/v1/fee-payments", json={"student_id": seed_student["id"], "amount": 2000, "payment_method": "cash"}, headers=auth_headers("director"))
        resp = client.get(f"/api/v1/fee-payments?student_id={seed_student['id']}", headers=auth_headers("director"))
        assert resp.status_code == 200

    def test_list_fee_payments_invalid_pagination(self, client, auth_headers):
        resp = client.get("/api/v1/fee-payments?page=0", headers=auth_headers("director"))
        assert resp.status_code == 400

    def test_list_fee_payments_date_filter(self, client, auth_headers, seed_student):
        client.post("/api/v1/fee-payments", json={"student_id": seed_student["id"], "amount": 1000, "payment_date": "2026-03-01", "payment_method": "cash"}, headers=auth_headers("director"))
        resp = client.get("/api/v1/fee-payments?start_date=2026-03-01&end_date=2026-03-31", headers=auth_headers("director"))
        assert resp.status_code == 200

    def test_list_fee_payments_invalid_date(self, client, auth_headers):
        resp = client.get("/api/v1/fee-payments?start_date=not-a-date", headers=auth_headers("director"))
        assert resp.status_code == 400


class TestGetFeePayment:
    """GET /api/v1/fee-payments/<id>"""

    def test_get_fee_payment_success(self, client, auth_headers, seed_student):
        create_resp = client.post("/api/v1/fee-payments", json={"student_id": seed_student["id"], "amount": 7500, "payment_method": "cash"}, headers=auth_headers("director"))
        pid = create_resp.get_json()["data"]["fee_payment"]["id"]
        resp = client.get(f"/api/v1/fee-payments/{pid}", headers=auth_headers("director"))
        assert resp.status_code == 200
        assert resp.get_json()["data"]["fee_payment"]["id"] == pid

    def test_get_fee_payment_not_found(self, client, auth_headers):
        resp = client.get("/api/v1/fee-payments/99999", headers=auth_headers("director"))
        assert resp.status_code == 404
