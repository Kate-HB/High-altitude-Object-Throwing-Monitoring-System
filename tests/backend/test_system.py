"""Tests for GET /api/system/status — requires auth."""

from unittest import mock
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)

SYSTEM_URL = "/api/system/status"


def _login() -> str:
    r = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    return r.json()["data"]["token"]


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestSystemStatusAuth:
    def test_no_token_returns_401(self):
        r = client.get(SYSTEM_URL)
        assert r.status_code == 401

    def test_invalid_token_returns_401(self):
        r = client.get(SYSTEM_URL, headers=_auth_header("bad-token-1234567890abcdef"))
        assert r.status_code == 401

    def test_wrong_bearer_format_returns_401(self):
        r = client.get(SYSTEM_URL, headers={"Authorization": "Token abc"})
        assert r.status_code == 401


class TestSystemStatusSuccess:
    def test_valid_token_returns_200(self):
        token = _login()
        r = client.get(SYSTEM_URL, headers=_auth_header(token))
        assert r.status_code == 200

    def test_valid_token_unified_format(self):
        token = _login()
        r = client.get(SYSTEM_URL, headers=_auth_header(token))
        body = r.json()
        assert body["code"] == 200

    def test_four_dimensions_present(self):
        token = _login()
        r = client.get(SYSTEM_URL, headers=_auth_header(token))
        data = r.json()["data"]
        assert "backend" in data
        assert "database" in data
        assert "algorithm" in data
        assert "device" in data

    def test_backend_status(self):
        token = _login()
        r = client.get(SYSTEM_URL, headers=_auth_header(token))
        backend = r.json()["data"]["backend"]
        assert backend["status"] == "running"

    def test_database_status(self):
        token = _login()
        r = client.get(SYSTEM_URL, headers=_auth_header(token))
        database = r.json()["data"]["database"]
        assert database["status"] == "connected"

    def test_device_info_has_required_fields(self):
        token = _login()
        r = client.get(SYSTEM_URL, headers=_auth_header(token))
        device = r.json()["data"]["device"]
        assert "device_type" in device
        assert device["device_type"] in ("cpu", "gpu")
        assert "cuda_available" in device
        assert "cpu_fallback" in device

    def test_database_error_shows_error_status(self):
        import sqlite3
        token = _login()
        with mock.patch("backend.app.api.system.get_db",
                        side_effect=sqlite3.Error("connection lost")):
            r = client.get(SYSTEM_URL, headers=_auth_header(token))
            database = r.json()["data"]["database"]
            assert database["status"] == "error"
