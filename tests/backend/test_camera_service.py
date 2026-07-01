"""Tests for camera_service guard clauses — no hardware needed."""
import importlib

import pytest

from backend.app.core.database import init_db
from backend.app.services import camera_service


def _reset_globals():
    """Reset camera_service module-level globals between tests."""
    camera_service._camera = None
    camera_service._camera_running = False
    camera_service._ai_enabled = False
    camera_service._ai_session = None
    camera_service._ai_task_id = None
    camera_service._ai_latest_events = []
    camera_service._last_frame = None


class TestStartCamera:
    def test_invalid_index_returns_error(self):
        _reset_globals()
        result = camera_service.start(camera_index=99)
        assert result["status"] == "error"

    def test_already_running_returns_status(self):
        _reset_globals()
        camera_service._camera_running = True
        result = camera_service.start(camera_index=0)
        assert result["status"] == "already_running"
        camera_service._camera_running = False


class TestStopCamera:
    def test_stop_when_not_running(self):
        _reset_globals()
        result = camera_service.stop()
        assert result["status"] == "not_running"


class TestGetStatus:
    def test_offline_when_not_running(self):
        _reset_globals()
        result = camera_service.get_status()
        assert result["status"] == "offline"

    def test_online_when_running(self):
        _reset_globals()
        camera_service._camera_running = True
        result = camera_service.get_status()
        assert result["status"] == "online"
        camera_service._camera_running = False


class TestStartAI:
    def test_ai_already_running(self):
        _reset_globals()
        camera_service._ai_enabled = True
        result = camera_service.start_ai({"x": 0, "y": 0, "width": 100, "height": 100})
        assert result["status"] == "error"
        assert "已在运行中" in result.get("message", "")
        camera_service._ai_enabled = False

    def test_camera_not_running(self):
        _reset_globals()
        result = camera_service.start_ai({"x": 0, "y": 0, "width": 100, "height": 100})
        assert result["status"] == "error"
        assert "摄像头未启动" in result.get("message", "")

    def test_model_not_found(self):
        _reset_globals()
        camera_service._camera_running = True
        old_root = camera_service._PROJECT_ROOT
        import tempfile
        import pathlib
        with tempfile.TemporaryDirectory() as tmpdir:
            # Point _PROJECT_ROOT to a temp dir that has no models/
            camera_service._PROJECT_ROOT = pathlib.Path(tmpdir)
            result = camera_service.start_ai({"x": 0, "y": 0, "width": 100, "height": 100})
            assert result["status"] == "error"
            assert "模型文件不存在" in result.get("message", "")
        camera_service._PROJECT_ROOT = old_root
        camera_service._camera_running = False


class TestStopAI:
    def test_ai_not_running(self):
        _reset_globals()
        result = camera_service.stop_ai()
        assert result["status"] == "error"
        assert "AI未在运行" in result.get("message", "")


class TestGetAIStatus:
    def test_returns_disabled_when_not_running(self):
        _reset_globals()
        result = camera_service.get_ai_status()
        assert result["ai_enabled"] is False
        assert result["task_id"] is None
        assert result["frame_count"] == 0
        assert result["active_tracks"] == 0
        assert result["total_events"] == 0
