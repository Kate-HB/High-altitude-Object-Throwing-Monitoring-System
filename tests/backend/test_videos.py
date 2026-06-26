"""Tests for video upload, task query, and analysis endpoints."""

import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def _login() -> str:
    r = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    return r.json()["data"]["token"]


def _auth_header() -> dict:
    return {"Authorization": f"Bearer {_login()}"}


# ── POST /api/videos/upload ─────────────────────────────────────────────

class TestUploadAuth:
    def test_no_token_returns_401(self):
        r = client.post("/api/videos/upload")
        assert r.status_code == 401

    def test_invalid_token_returns_401(self):
        r = client.post(
            "/api/videos/upload",
            headers={"Authorization": "Bearer deadbeef"},
        )
        assert r.status_code == 401


class TestUploadInvalid:
    def test_invalid_extension(self):
        r = client.post(
            "/api/videos/upload",
            files={"file": ("test.txt", io.BytesIO(b"hello"), "text/plain")},
            headers=_auth_header(),
        )
        assert r.status_code == 200
        assert r.json()["code"] == 415

    def test_no_file(self):
        r = client.post(
            "/api/videos/upload",
            headers=_auth_header(),
        )
        assert r.status_code == 422  # FastAPI validation — file is required


# ── GET /api/tasks/{task_id} ────────────────────────────────────────────

class TestTaskQuery:
    def test_not_found(self):
        r = client.get("/api/tasks/99999", headers=_auth_header())
        assert r.status_code == 200
        assert r.json()["code"] == 404

    def test_no_auth(self):
        r = client.get("/api/tasks/1")
        assert r.status_code == 401


# ── POST /api/tasks/{task_id}/analyze ───────────────────────────────────

class TestAnalyzeTask:
    def test_not_found(self):
        r = client.post(
            "/api/tasks/99999/analyze",
            json={"roi_x": 0, "roi_y": 0},
            headers=_auth_header(),
        )
        assert r.status_code == 200
        assert r.json()["code"] == 404

    def test_no_auth(self):
        r = client.post("/api/tasks/1/analyze", json={"roi_x": 0, "roi_y": 0})
        assert r.status_code == 401


# ── Integration: upload → query → analyze ──────────────────────────────

class TestUploadQueryFlow:
    """End-to-end: upload a valid video, query task, verify progress."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path, monkeypatch):
        """Redirect uploads to a temp dir so tests don't pollute real dir."""
        self.upload_dir = tmp_path / "uploads"
        self.upload_dir.mkdir()
        monkeypatch.setattr(
            "backend.app.services.video_service.UPLOAD_DIR",
            self.upload_dir,
        )

    def _fake_mp4_bytes(self) -> bytes:
        """Minimal bytes that won't pass OpenCV but passes extension check."""
        # A valid mp4 would be large; for the upload test we skip OpenCV
        # and test the upload + task creation path by patching get_total_frames.
        return b"\x00\x00\x00\x18ftypmp42"

    def test_upload_and_query(self, monkeypatch):
        # Patch get_total_frames in the API module where it's imported
        monkeypatch.setattr(
            "backend.app.api.videos.get_total_frames",
            lambda _: 240,
        )

        r = client.post(
            "/api/videos/upload",
            files={"file": ("test.mp4", io.BytesIO(self._fake_mp4_bytes()), "video/mp4")},
            headers=_auth_header(),
        )
        assert r.status_code == 200
        body = r.json()
        assert body["code"] == 200
        assert body["data"]["total_frames"] == 240
        assert body["data"]["filename"].endswith("_test.mp4")

        task_id = body["data"]["task_id"]

        # Query the task
        r2 = client.get(f"/api/tasks/{task_id}", headers=_auth_header())
        assert r2.status_code == 200
        task = r2.json()["data"]
        assert task["status"] == "pending"
        assert task["total_frames"] == 240
        assert task["progress"] == 0

    def test_upload_invalid_extension_flow(self):
        r = client.post(
            "/api/videos/upload",
            files={"file": ("doc.pdf", io.BytesIO(b"%PDF"), "application/pdf")},
            headers=_auth_header(),
        )
        assert r.json()["code"] == 415
