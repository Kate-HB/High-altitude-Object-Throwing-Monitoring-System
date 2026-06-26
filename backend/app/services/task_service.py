"""Task CRUD and background analysis thread."""

from __future__ import annotations

import logging
import threading
from typing import Any

from backend.app.core.database import get_db
from backend.app.services.event_service import (
    batch_insert_detections,
    batch_insert_events,
    batch_insert_tracks,
)

logger = logging.getLogger("backend.task_service")


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

        from algorithm.pipeline import run_video_analysis

        result = run_video_analysis(
            video_path=task["source_path"],
            output_dir="uploads/results",
            roi=roi or {},
            settings=settings,
        )

        if result.status == "success":
            update_task(
                task_id,
                status="success",
                total_frames=result.total_frames or task["total_frames"],
                processed_frames=result.processed_frames or task["total_frames"],
                result_video_path=result.result_video_path,
            )
            batch_insert_events(task_id, result.events)
            batch_insert_detections(task_id, result.detection_results)
            batch_insert_tracks(task_id, result.tracking_results)
        elif result.status == "not_ready":
            update_task(
                task_id,
                status="failed",
                error_message=result.error_message or "算法模块未就绪",
            )
        else:
            update_task(
                task_id,
                status="failed",
                error_message=result.error_message or "未知错误",
            )

        logger.info("Task %d: completed with status=%s", task_id, result.status)

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
