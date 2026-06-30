"""Tests for backend.app.services.task_service CRUD operations."""
import pytest

from backend.app.core.database import init_db
from backend.app.services.task_service import create_task, get_task, update_task


class TestCreateTask:
    def test_returns_int_id(self):
        init_db()
        task_id = create_task("upload", "test_video.mp4")
        assert isinstance(task_id, int)
        assert task_id > 0

    def test_stores_source_fields(self):
        init_db()
        task_id = create_task("camera", "camera://0", total_frames=500,
                              roi={"x": 10, "y": 20, "width": 300, "height": 200})
        task = get_task(task_id)
        assert task is not None
        assert task["source_type"] == "camera"
        assert task["source_path"] == "camera://0"
        assert task["total_frames"] == 500
        assert task["roi_x"] == 10
        assert task["roi_y"] == 20
        assert task["roi_width"] == 300
        assert task["roi_height"] == 200

    def test_roi_none_uses_zero(self):
        init_db()
        task_id = create_task("upload", "v.mp4", roi=None)
        task = get_task(task_id)
        assert task["roi_x"] == 0
        assert task["roi_y"] == 0


class TestGetTask:
    def test_nonexistent_returns_none(self):
        init_db()
        assert get_task(99999) is None

    def test_new_task_has_pending_status(self):
        init_db()
        task_id = create_task("upload", "v.mp4")
        task = get_task(task_id)
        assert task["status"] == "pending"
        assert task["progress"] == 0


class TestUpdateTask:
    def test_updates_status_and_frames(self):
        init_db()
        task_id = create_task("upload", "v.mp4", total_frames=100)
        update_task(task_id, status="success", processed_frames=100,
                    result_video_path="outputs/task_1/result.mp4")
        task = get_task(task_id)
        assert task["status"] == "success"
        assert task["processed_frames"] == 100
        assert task["result_video_path"] == "outputs/task_1/result.mp4"
        assert task["progress"] == 100.0

    def test_update_empty_kwargs_does_nothing(self):
        init_db()
        task_id = create_task("upload", "v.mp4")
        update_task(task_id)  # no kwargs → early return
        task = get_task(task_id)
        assert task["status"] == "pending"
