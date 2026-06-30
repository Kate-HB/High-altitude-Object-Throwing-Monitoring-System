"""Tests for _run_analysis background task — mocking subprocess."""
import json
import subprocess
from unittest import mock

from backend.app.core.database import init_db
from backend.app.services import task_service
from backend.app.services.task_service import create_task, get_task, update_task


def _seed_task():
    """Create a test task and return its id."""
    init_db()
    task_id = create_task("upload", "data/videos/demo.mp4", total_frames=300,
                          roi={"x": 10, "y": 20, "width": 640, "height": 480})
    return task_id


class TestRunAnalysis:
    def test_subprocess_failure_marks_task_failed(self):
        task_id = _seed_task()
        with mock.patch.object(subprocess, "run") as m_run:
            m_run.return_value = mock.Mock(
                returncode=1, stdout="", stderr="crash"
            )
            task_service._run_analysis(task_id, {}, {})
        task = get_task(task_id)
        assert task["status"] == "failed"
        assert task["error_message"] is not None

    def test_empty_stdout_marks_task_failed(self):
        task_id = _seed_task()
        with mock.patch.object(subprocess, "run") as m_run:
            m_run.return_value = mock.Mock(
                returncode=0, stdout="", stderr=""
            )
            task_service._run_analysis(task_id, {}, {})
        task = get_task(task_id)
        assert task["status"] == "failed"
        assert "子进程无输出" in (task["error_message"] or "")

    def test_success_stdout_updates_task(self):
        task_id = _seed_task()
        success_result = {
            "status": "success",
            "total_frames": 300,
            "processed_frames": 300,
            "result_video_path": "outputs/task_1/result.mp4",
            "events": [],
            "detection_results": [],
            "tracking_results": [],
        }
        with mock.patch.object(subprocess, "run") as m_run:
            m_run.return_value = mock.Mock(
                returncode=0,
                stdout=json.dumps(success_result, ensure_ascii=False),
                stderr="",
            )
            task_service._run_analysis(task_id, {}, {})
        task = get_task(task_id)
        assert task["status"] == "success"
        assert task["processed_frames"] == 300

    def test_stdout_with_leading_noise_parses_correctly(self):
        """stdout may have ultralytics loading info before JSON."""
        task_id = _seed_task()
        success_result = {
            "status": "success",
            "total_frames": 100,
            "processed_frames": 100,
            "result_video_path": "outputs/task_2/result.mp4",
            "events": [],
            "detection_results": [],
            "tracking_results": [],
        }
        noisy_stdout = (
            "Loading model...\n"
            + json.dumps(success_result, ensure_ascii=False)
        )
        with mock.patch.object(subprocess, "run") as m_run:
            m_run.return_value = mock.Mock(
                returncode=0, stdout=noisy_stdout, stderr=""
            )
            task_service._run_analysis(task_id, {}, {})
        task = get_task(task_id)
        assert task["status"] == "success"

    def test_failed_status_in_json(self):
        task_id = _seed_task()
        fail_result = {
            "status": "failed",
            "error_message": "模型加载失败",
            "total_frames": 0,
            "processed_frames": 0,
            "events": [],
            "detection_results": [],
            "tracking_results": [],
        }
        with mock.patch.object(subprocess, "run") as m_run:
            m_run.return_value = mock.Mock(
                returncode=0,
                stdout=json.dumps(fail_result, ensure_ascii=False),
                stderr="",
            )
            task_service._run_analysis(task_id, {}, {})
        task = get_task(task_id)
        assert task["status"] == "failed"
        assert "模型加载失败" in (task["error_message"] or "")

    def test_nonexistent_task_does_not_crash(self):
        """Calling _run_analysis on a non-existent task should not raise."""
        with mock.patch.object(subprocess, "run") as m_run:
            # Should not reach subprocess — task not found returns early
            task_service._run_analysis(99999, {}, {})
        # Should not have called subprocess
        m_run.assert_not_called()

    def test_exception_during_analysis_marks_failed(self):
        task_id = _seed_task()
        with mock.patch.object(subprocess, "run") as m_run:
            m_run.side_effect = OSError("process killed")
            task_service._run_analysis(task_id, {}, {})
        task = get_task(task_id)
        assert task["status"] == "failed"
