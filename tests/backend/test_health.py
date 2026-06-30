"""Tests for GET /api/health — no auth required."""

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    def test_returns_200(self):
        r = client.get("/api/health")
        assert r.status_code == 200

    def test_top_level_status_is_ok(self):
        """API returns unified format with code:200 and data.status:running."""
        r = client.get("/api/health")
        body = r.json()
        assert body["code"] == 200
        assert body["data"]["status"] == "running"

    def test_unified_response_format(self):
        r = client.get("/api/health")
        body = r.json()
        assert body["code"] == 200
        assert body["message"] == "success"
        assert "data" in body

    def test_data_contains_required_fields(self):
        r = client.get("/api/health")
        data = r.json()["data"]
        assert data["status"] == "running"
        assert "service" in data
        assert "version" in data
        assert "time" in data

    def test_time_format(self):
        r = client.get("/api/health")
        time_str = r.json()["data"]["time"]
        # YYYY-MM-DD HH:MM:SS
        parts = time_str.split(" ")
        assert len(parts) == 2
        date_parts = parts[0].split("-")
        assert len(date_parts) == 3
        time_parts = parts[1].split(":")
        assert len(time_parts) == 3
