"""Tests for POST /api/auth/login — no auth required."""

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)

LOGIN_URL = "/api/auth/login"


class TestLoginSuccess:
    def test_correct_credentials_returns_200(self):
        r = client.post(LOGIN_URL, json={"username": "admin", "password": "admin123"})
        assert r.status_code == 200

    def test_correct_credentials_unified_format(self):
        r = client.post(LOGIN_URL, json={"username": "admin", "password": "admin123"})
        body = r.json()
        assert body["code"] == 200
        assert body["message"] == "login success"

    def test_correct_credentials_returns_token(self):
        r = client.post(LOGIN_URL, json={"username": "admin", "password": "admin123"})
        data = r.json()["data"]
        assert "token" in data
        assert len(data["token"]) == 32  # token_hex(16) = 32 chars
        assert data["username"] == "admin"
        assert data["role"] == "admin"


class TestLoginFailure:
    def test_wrong_password_returns_401(self):
        r = client.post(LOGIN_URL, json={"username": "admin", "password": "wrong"})
        assert r.status_code == 200  # endpoint returns 200, body has 401

    def test_wrong_password_error_body(self):
        r = client.post(LOGIN_URL, json={"username": "admin", "password": "wrong"})
        body = r.json()
        assert body["code"] == 401
        assert body["message"] == "login failed"

    def test_wrong_username_returns_401(self):
        r = client.post(LOGIN_URL, json={"username": "guest", "password": "admin123"})
        body = r.json()
        assert body["code"] == 401

    def test_empty_body(self):
        r = client.post(LOGIN_URL, json={})
        assert r.status_code == 422  # Pydantic validation error

    def test_missing_password_field(self):
        r = client.post(LOGIN_URL, json={"username": "admin"})
        assert r.status_code == 422
