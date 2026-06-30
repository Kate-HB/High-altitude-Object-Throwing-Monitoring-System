"""Tests for API settings endpoints."""
from unittest import mock

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)
SETTINGS_URL = "/api/settings"


def _login() -> str:
    r = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    return r.json()["data"]["token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestSettingsAPI:
    def test_read_requires_auth(self):
        r = client.get(SETTINGS_URL)
        assert r.status_code == 401

    def test_read_returns_200(self):
        token = _login()
        r = client.get(SETTINGS_URL, headers=_auth(token))
        assert r.status_code == 200
        body = r.json()
        assert body["code"] == 200
        assert "detect_confidence" in body["data"]

    def test_write_requires_auth(self):
        r = client.put(SETTINGS_URL, json={"detect_confidence": 0.5})
        assert r.status_code == 401

    def test_write_and_read_roundtrip(self):
        token = _login()
        body = {"detect_confidence": 0.42, "downward_ratio": 0.55,
                "min_vertical_distance": 50, "min_track_frames": 5,
                "roi_required_ratio": 0.5, "alarm_cooldown_seconds": 10, "imgsz": 960}
        r = client.put(SETTINGS_URL, headers=_auth(token), json=body)
        assert r.status_code == 200
        assert r.json()["data"]["detect_confidence"] == 0.42
        r = client.get(SETTINGS_URL, headers=_auth(token))
        assert r.json()["data"]["detect_confidence"] == 0.42

    def test_write_invalid_range_returns_error(self):
        token = _login()
        body = {"detect_confidence": 2.0, "downward_ratio": 0.55,
                "min_vertical_distance": 50, "min_track_frames": 5,
                "roi_required_ratio": 0.5, "alarm_cooldown_seconds": 10, "imgsz": 960}
        r = client.put(SETTINGS_URL, headers=_auth(token), json=body)
        assert r.json()["code"] == 400

    def test_read_exception_returns_500(self):
        token = _login()
        with mock.patch("backend.app.api.settings.get_settings",
                        side_effect=RuntimeError("db crash")):
            r = client.get(SETTINGS_URL, headers=_auth(token))
            assert r.json()["code"] == 500

    def test_write_exception_returns_500(self):
        token = _login()
        body = {"detect_confidence": 0.5, "downward_ratio": 0.55,
                "min_vertical_distance": 50, "min_track_frames": 5,
                "roi_required_ratio": 0.5, "alarm_cooldown_seconds": 10, "imgsz": 960}
        with mock.patch("backend.app.api.settings.update_settings",
                        side_effect=RuntimeError("db crash")):
            r = client.put(SETTINGS_URL, headers=_auth(token), json=body)
            assert r.json()["code"] == 500
