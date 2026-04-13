"""Tests for health and root endpoints."""


class TestHealthEndpoint:
    """GET /api/v1/health"""

    def test_health_returns_200(self, client):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert "healthy" in body["message"].lower()


class TestRootEndpoints:
    """GET / and GET /api/v1"""

    def test_root_returns_200(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert body["data"]["base_url"] == "/api/v1"

    def test_api_v1_root_returns_200(self, client):
        resp = client.get("/api/v1")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert "reachable" in body["message"].lower()

    def test_unknown_route_returns_404(self, client):
        resp = client.get("/api/v1/nonexistent")
        assert resp.status_code == 404
        body = resp.get_json()
        assert body["success"] is False
