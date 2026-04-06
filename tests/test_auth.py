"""Tests for authentication endpoints."""

import pytest


class TestRegister:
    """POST /api/v1/auth/register"""

    def test_register_success(self, client):
        payload = {
            "full_name": "New User",
            "email": "newuser@example.com",
            "password": "StrongPass123",
            "role": "student",
        }
        resp = client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["success"] is True
        assert body["data"]["user"]["email"] == "newuser@example.com"
        assert body["data"]["user"]["role"] == "student"
        assert "access_token" in body["data"]

    def test_register_missing_email(self, client):
        payload = {"full_name": "No Email", "password": "StrongPass123", "role": "student"}
        resp = client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 400
        body = resp.get_json()
        assert body["success"] is False

    def test_register_missing_password(self, client):
        payload = {"full_name": "No Pass", "email": "nopass@example.com", "role": "student"}
        resp = client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 400

    def test_register_missing_full_name(self, client):
        payload = {"email": "noname@example.com", "password": "StrongPass123", "role": "student"}
        resp = client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 400

    def test_register_short_password(self, client):
        payload = {
            "full_name": "Short",
            "email": "short@example.com",
            "password": "abc",
            "role": "student",
        }
        resp = client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 400
        body = resp.get_json()
        assert "8 characters" in body["message"]

    def test_register_invalid_role(self, client):
        payload = {
            "full_name": "Bad Role",
            "email": "badrole@example.com",
            "password": "StrongPass123",
            "role": "superadmin",
        }
        resp = client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 400
        body = resp.get_json()
        assert "role must be one of" in body["message"]

    def test_register_duplicate_email(self, client):
        payload = {
            "full_name": "Dup User",
            "email": "dup@example.com",
            "password": "StrongPass123",
            "role": "student",
        }
        resp1 = client.post("/api/v1/auth/register", json=payload)
        assert resp1.status_code == 201

        resp2 = client.post("/api/v1/auth/register", json=payload)
        assert resp2.status_code == 409
        body = resp2.get_json()
        assert body["success"] is False

    def test_register_defaults_to_student_role(self, client):
        payload = {
            "full_name": "Default Role",
            "email": "defaultrole@example.com",
            "password": "StrongPass123",
        }
        resp = client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["data"]["user"]["role"] == "student"


class TestLogin:
    """POST /api/v1/auth/login"""

    def test_login_success(self, client, seed_users):
        payload = {"email": "admin@test.com", "password": "Admin@1234"}
        resp = client.post("/api/v1/auth/login", json=payload)
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert "access_token" in body["data"]
        assert body["data"]["user"]["email"] == "admin@test.com"

    def test_login_wrong_password(self, client, seed_users):
        payload = {"email": "admin@test.com", "password": "WrongPassword"}
        resp = client.post("/api/v1/auth/login", json=payload)
        assert resp.status_code == 401
        body = resp.get_json()
        assert body["success"] is False
        assert "invalid" in body["message"].lower()

    def test_login_nonexistent_email(self, client):
        payload = {"email": "ghost@example.com", "password": "DoesNotMatter"}
        resp = client.post("/api/v1/auth/login", json=payload)
        assert resp.status_code == 401

    def test_login_missing_fields(self, client):
        resp = client.post("/api/v1/auth/login", json={})
        assert resp.status_code == 400
        body = resp.get_json()
        assert "required" in body["message"]

    def test_login_empty_body(self, client):
        resp = client.post(
            "/api/v1/auth/login",
            data="",
            content_type="application/json",
        )
        assert resp.status_code == 400


class TestGetMe:
    """GET /api/v1/auth/me"""

    def test_get_me_success(self, client, auth_headers):
        resp = client.get("/api/v1/auth/me", headers=auth_headers("admin"))
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert body["data"]["user"]["email"] == "admin@test.com"

    def test_get_me_no_token(self, client):
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    def test_get_me_invalid_token(self, client):
        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert resp.status_code == 422


class TestProtectedRoute:
    """GET /api/v1/auth/protected"""

    def test_protected_route_with_token(self, client, auth_headers):
        resp = client.get("/api/v1/auth/protected", headers=auth_headers("student"))
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert body["data"]["role"] == "student"

    def test_protected_route_without_token(self, client):
        resp = client.get("/api/v1/auth/protected")
        assert resp.status_code == 401


class TestAdminOnlyRoute:
    """GET /api/v1/auth/admin-only"""

    def test_admin_only_with_admin(self, client, auth_headers):
        resp = client.get("/api/v1/auth/admin-only", headers=auth_headers("admin"))
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["data"]["scope"] == "admin"

    def test_admin_only_with_director(self, client, auth_headers):
        resp = client.get("/api/v1/auth/admin-only", headers=auth_headers("director"))
        assert resp.status_code == 403

    def test_admin_only_with_student(self, client, auth_headers):
        resp = client.get("/api/v1/auth/admin-only", headers=auth_headers("student"))
        assert resp.status_code == 403


class TestUsersSummary:
    """GET /api/v1/auth/users-summary"""

    def test_users_summary_admin(self, client, auth_headers):
        resp = client.get("/api/v1/auth/users-summary", headers=auth_headers("admin"))
        assert resp.status_code == 200
        body = resp.get_json()
        assert "total_registered_users" in body["data"]
        assert "admins" in body["data"]

    def test_users_summary_non_admin(self, client, auth_headers):
        resp = client.get("/api/v1/auth/users-summary", headers=auth_headers("student"))
        assert resp.status_code == 403


class TestRegisteredUsers:
    """GET /api/v1/auth/registered-users"""

    def test_registered_users_admin(self, client, auth_headers):
        resp = client.get("/api/v1/auth/registered-users", headers=auth_headers("admin"))
        assert resp.status_code == 200
        body = resp.get_json()
        assert isinstance(body["data"]["users"], list)

    def test_registered_users_director(self, client, auth_headers):
        resp = client.get("/api/v1/auth/registered-users", headers=auth_headers("director"))
        assert resp.status_code == 200

    def test_registered_users_student(self, client, auth_headers):
        resp = client.get("/api/v1/auth/registered-users", headers=auth_headers("student"))
        assert resp.status_code == 403


class TestUpdateUser:
    """PUT /api/v1/auth/users/<user_id>"""

    def test_update_user_name(self, client, auth_headers, seed_users):
        user = seed_users["student"]
        payload = {"full_name": "Updated Student Name"}
        resp = client.put(
            f"/api/v1/auth/users/{user['id']}",
            json=payload,
            headers=auth_headers("admin"),
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["data"]["user"]["full_name"] == "Updated Student Name"

    def test_update_user_no_fields(self, client, auth_headers, seed_users):
        user = seed_users["student"]
        resp = client.put(
            f"/api/v1/auth/users/{user['id']}",
            json={"random_field": "ignored"},
            headers=auth_headers("admin"),
        )
        assert resp.status_code == 400

    def test_update_user_rbac(self, client, auth_headers, seed_users):
        user = seed_users["student"]
        resp = client.put(
            f"/api/v1/auth/users/{user['id']}",
            json={"full_name": "Hacked"},
            headers=auth_headers("student"),
        )
        assert resp.status_code == 403


class TestDeleteUser:
    """DELETE /api/v1/auth/users/<user_id>"""

    def test_soft_delete_user(self, client, auth_headers, seed_users):
        # Register a throwaway user to delete
        reg_resp = client.post("/api/v1/auth/register", json={
            "full_name": "To Delete",
            "email": "todelete@example.com",
            "password": "ToDelete@123",
            "role": "student",
        })
        user_id = reg_resp.get_json()["data"]["user"]["id"]

        resp = client.delete(
            f"/api/v1/auth/users/{user_id}",
            headers=auth_headers("admin"),
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["data"]["user"]["is_active"] is False

    def test_delete_user_rbac(self, client, auth_headers, seed_users):
        user = seed_users["coach"]
        resp = client.delete(
            f"/api/v1/auth/users/{user['id']}",
            headers=auth_headers("student"),
        )
        assert resp.status_code == 403
