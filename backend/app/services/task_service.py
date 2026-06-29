"""Task CRUD and background analysis thread."""

from __future__ import annotations

import json
import logging
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any

from backend.app.core.database import get_db
from backend.app.services.event_service import (
    batch_insert_detections,
    batch_insert_events,
    batch_insert_tracks,
)

logger = logging.getLogger("backend.task_service")

# Conda Python path (has torch + ultralytics)
_CONDA_PYTHON = r"D:\Soft\Conda\python.exe"
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_PIPELINE_CLI = _PROJECT_ROOT / "scripts" / "pipeline_cli.py"


# ── Task CRUD ──────────────────────────────────────────────────────────

def create_task(
    source_type: str,
    source_path: str,
    total_frames: int = 0,
    roi: dict[str, int] | None = None,
) -> int:
    """INSERT a video_tasks row and return the new task id."""
    db = get_db()
    cursor = db.execute(
        """INSERT INTO video_tasks (source_type, source_path, total_frames,
           roi_x, roi_y, roi_width, roi_height)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            source_type,
            source_path,
            total_frames,
            roi.get("x", 0) if roi else 0,
            roi.get("y", 0) if roi else 0,
            roi.get("width") if roi else None,
            roi.get("height") if roi else None,
        ),
    )
    db.commit()
    task_id = cursor.lastrowid
    db.close()
    return task_id


def get_task(task_id: int) -> dict | None:
    """SELECT a single task row with computed progress percent."""
    db = get_db()
    row = db.execute(
        "SELECT * FROM video_tasks WHERE id = ?", (task_id,)
    ).fetchone()
    if row is None:
        db.close()
        return None

    task = dict(row)
    total = task.get("total_frames", 0)
    processed = task.get("processed_frames", 0)

    # Read live progress from pipeline for running tasks
    if task.get("status") == "running":
        progress_file = _PROJECT_ROOT / "outputs" / f"task_{task_id}" / "progress.json"
        try:
            if progress_file.is_file():
                data = json.loads(progress_file.read_text(encoding="utf-8"))
                live_processed = data.get("frame", 0)
                if live_processed > processed:
                    processed = live_processed
                    task["processed_frames"] = processed
        except Exception:
            pass

    task["progress"] = round(processed / total * 100, 1) if total > 0 else 0

    # Attach related events
    events = db.execute(
        "SELECT * FROM events WHERE video_task_id = ?", (task_id,)
    ).fetchall()
    task["events"] = [dict(e) for e in events]
    db.close()
    return task


def update_task(task_id: int, **kwargs: Any) -> None:
    """UPDATE video_tasks row. Only updates provided keyword columns."""
    if not kwargs:
        return
    set_parts = [f"{k} = ?" for k in kwargs]
    set_parts.append("updated_at = datetime('now','localtime')")
    values = list(kwargs.values())
    db = get_db()
    db.execute(
        f"UPDATE video_tasks SET {', '.join(set_parts)} WHERE id = ?",
        values + [task_id],
    )
    db.commit()
    db.close()


# ── Background analysis ────────────────────────────────────────────────

def _run_analysis(task_id: int, roi: dict[str, int], settings: dict[str, Any]) -> None:
    """Background thread target: run algorithm pipeline, update DB."""
    try:
        logger.info("Task %d: analysis started", task_id)
        update_task(task_id, status="running")

        db = get_db()
        task = db.execute(
            "SELECT * FROM video_tasks WHERE id = ?", (task_id,)
        ).fetchone()
        db.close()

        if task is None:
            logger.error("Task %d: not found", task_id)
            return

        # Save ROI to DB (#003 fix)
        if roi:
            update_task(
                task_id,
                roi_x=roi.get("x", 0),
                roi_y=roi.get("y", 0),
                roi_width=roi.get("width"),
                roi_height=roi.get("height"),
            )

        output_dir = f"outputs/task_{task_id}"

        # Run algorithm via subprocess (needs Conda Python for torch/ultralytics)
        cmd = [
            _CONDA_PYTHON,
            str(_PIPELINE_CLI),
            "--video", task["source_path"],
            "--output-dir", output_dir,
            "--roi", json.dumps(roi or {}),
            "--settings", json.dumps(settings),
            "--model", str(_PROJECT_ROOT / "models" / "best.pt"),
        ]
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,
            cwd=str(_PROJECT_ROOT),
            env={**__import__("os").environ, "KMP_DUPLICATE_LIB_OK": "1"},
        )
        if proc.returncode != 0:
            logger.error("Task %d: pipeline subprocess failed, rc=%d stderr=%s", task_id, proc.returncode, proc.stderr[-500:])
            update_task(task_id, status="failed", error_message="算法子进程异常退出")
            return

        result_data = json.loads(proc.stdout)
        status_val = result_data.get("status", "failed")

        if status_val == "success":
            update_task(
                task_id,
                status="success",
                total_frames=result_data.get("total_frames", task["total_frames"]),
                processed_frames=result_data.get("processed_frames", task["total_frames"]),
                result_video_path=result_data.get("result_video_path"),
            )
            events = result_data.get("events", [])
            detections = result_data.get("detection_results", [])
            tracks = result_data.get("tracking_results", [])
            if events:
                batch_insert_events(task_id, events)
            if detections:
                batch_insert_detections(task_id, detections)
            if tracks:
                batch_insert_tracks(task_id, tracks)
        else:
            update_task(
                task_id,
                status="failed",
                error_message=result_data.get("error_message") or "未知错误",
            )

        logger.info("Task %d: completed with status=%s", task_id, status_val)

    except Exception:
        logger.exception("Task %d: unhandled exception", task_id)
        update_task(task_id, status="failed", error_message="后台分析异常")


def start_analysis(task_id: int, roi: dict[str, int], settings: dict[str, Any]) -> None:
    """Spawn a background thread to run the algorithm pipeline."""
    thread = threading.Thread(
        target=_run_analysis,
        args=(task_id, roi, settings),
        daemon=True,
        name=f"analysis-{task_id}",
    )
    thread.start()
    logger.info("Task %d: background thread started", task_id)
