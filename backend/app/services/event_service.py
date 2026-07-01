"""Event CRUD service — query, update, and batch-write events/detections/tracks."""

from __future__ import annotations

import logging
from typing import Any

from backend.app.core.database import get_db

logger = logging.getLogger("backend.event_service")


# ── Event query ────────────────────────────────────────────────────────

def list_events(
    task_id: int | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """List events, optionally filtered by task_id and/or status."""
    db = get_db()
    clauses: list[str] = []
    params: list[Any] = []

    if task_id is not None:
        clauses.append("video_task_id = ?")
        params.append(task_id)
    if status is not None:
        clauses.append("status = ?")
        params.append(status)

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    query = f"""SELECT e.*, t.result_video_path AS task_result_video_path
                FROM events e
                LEFT JOIN video_tasks t ON e.video_task_id = t.id
                {where}
                ORDER BY e.created_at DESC LIMIT ? OFFSET ?"""
    params.extend([limit, offset])

    rows = db.execute(query, params).fetchall()
    db.close()
    return [dict(r) for r in rows]


def get_event(event_id: int) -> dict[str, Any] | None:
    """Get a single event by id, with related detections and tracks."""
    db = get_db()
    row = db.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
    if row is None:
        db.close()
        return None

    event = dict(row)
    task_id = event["video_task_id"]

    detections = db.execute(
        "SELECT * FROM detection_results WHERE video_task_id = ? ORDER BY frame_id",
        (task_id,),
    ).fetchall()
    event["detections"] = [dict(d) for d in detections]

    tracks = db.execute(
        "SELECT * FROM tracking_results WHERE video_task_id = ? ORDER BY frame_id",
        (task_id,),
    ).fetchall()
    event["tracks"] = [dict(t) for t in tracks]

    db.close()
    return event


def update_event_status(event_id: int, status: str) -> bool:
    """Update event status. Returns True if a row was changed."""
    db = get_db()
    cursor = db.execute(
        """UPDATE events SET status = ?, updated_at = datetime('now','localtime')
           WHERE id = ?""",
        (status, event_id),
    )
    db.commit()
    changed = cursor.rowcount > 0
    db.close()
    return changed


# ── Batch write (called from background analysis) ──────────────────────

def batch_insert_events(task_id: int, events: list[dict[str, Any]]) -> int:
    """Insert event rows in batch. Returns count inserted."""
    if not events:
        return 0
    db = get_db()
    for evt in events:
        db.execute(
            """INSERT INTO events (video_task_id, track_id, confidence, status,
               snapshot_path, result_video_path)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                task_id,
                evt.get("track_id"),
                evt.get("confidence"),
                evt.get("status", "unconfirmed"),
                evt.get("snapshot_path"),
                evt.get("result_video_path"),
            ),
        )
    db.commit()
    db.close()
    logger.info("Batch inserted %d events for task %d", len(events), task_id)
    return len(events)


def batch_insert_detections(task_id: int, detections: list[dict[str, Any]]) -> int:
    """Insert detection rows in batch. Returns count inserted."""
    if not detections:
        return 0
    db = get_db()
    for det in detections:
        db.execute(
            """INSERT INTO detection_results (video_task_id, frame_id,
               bbox_x, bbox_y, bbox_width, bbox_height, confidence, class_name)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                task_id,
                det.get("frame_id"),
                det.get("bbox_x"),
                det.get("bbox_y"),
                det.get("bbox_width"),
                det.get("bbox_height"),
                det.get("confidence"),
                det.get("class_name", "falling_object"),
            ),
        )
    db.commit()
    db.close()
    logger.info("Batch inserted %d detections for task %d", len(detections), task_id)
    return len(detections)


def batch_insert_tracks(task_id: int, tracks: list[dict[str, Any]]) -> int:
    """Insert tracking rows in batch. Returns count inserted."""
    if not tracks:
        return 0
    db = get_db()
    for trk in tracks:
        db.execute(
            """INSERT INTO tracking_results (video_task_id, track_id, frame_id,
               timestamp, center_x, center_y, bbox_x, bbox_y, bbox_width, bbox_height)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                task_id,
                trk.get("track_id"),
                trk.get("frame_id"),
                trk.get("timestamp"),
                trk.get("center_x"),
                trk.get("center_y"),
                trk.get("bbox_x"),
                trk.get("bbox_y"),
                trk.get("bbox_width"),
                trk.get("bbox_height"),
            ),
        )
    db.commit()
    db.close()
    logger.info("Batch inserted %d tracks for task %d", len(tracks), task_id)
    return len(tracks)
