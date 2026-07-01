"""Tests for API statistics endpoint."""
from unittest import mock

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)
STATS_URL = "/api/statistics/overview"


def _login() -> str:
    r = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    return r.json()["data"]["token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestStatisticsAPI:
    def test_requires_auth(self):
        r = client.get(STATS_URL)
        assert r.status_code == 401

    def test_returns_200_with_valid_token(self):
        token = _login()
        r = client.get(STATS_URL, headers=_auth(token))
        assert r.status_code == 200
        body = r.json()
        assert body["code"] == 200
        assert "today_event_count" in body["data"]
        assert "total_event_count" in body["data"]
        assert "recent_events" in body["data"]
        assert "daily_trend" in body["data"]
        assert "confidence_distribution" in body["data"]
        assert "status_distribution" in body["data"]

    def test_exception_returns_500(self):
        token = _login()
        with mock.patch("backend.app.api.statistics.get_overview",
                        side_effect=RuntimeError("db crash")):
            r = client.get(STATS_URL, headers=_auth(token))
            assert r.json()["code"] == 500
