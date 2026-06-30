"""Tests for file-serving endpoint."""
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)
FILES_URL = "/api/files"
_PROJECT = Path(__file__).resolve().parent.parent.parent


class TestFilesAPI:
    def test_missing_path_param_returns_422(self):
        r = client.get(FILES_URL)
        assert r.status_code == 422

    def test_disallowed_path_returns_403(self):
        r = client.get(FILES_URL, params={"path": "data/videos/demo.mp4"})
        assert r.status_code == 403

    def test_nonexistent_file_returns_404(self):
        r = client.get(FILES_URL, params={"path": "uploads/nonexistent.xyz"})
        assert r.status_code == 404

    def test_valid_file_returns_200(self):
        uploads = _PROJECT / "uploads"
        uploads.mkdir(parents=True, exist_ok=True)
        test_file = uploads / "_test_serve.txt"
        test_file.write_text("hello")
        try:
            r = client.get(FILES_URL, params={"path": "uploads/_test_serve.txt"})
            assert r.status_code == 200
        finally:
            test_file.unlink(missing_ok=True)
