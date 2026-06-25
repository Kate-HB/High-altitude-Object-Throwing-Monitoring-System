"""SQLite initialization and connection management."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from backend.app.core.config import get_settings

_db_path: str | None = None

DDL_STATEMENTS = [
    """CREATE TABLE IF NOT EXISTS system_settings (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        detect_confidence REAL DEFAULT 0.35,
        downward_ratio REAL DEFAULT 0.7,
        min_vertical_distance INTEGER DEFAULT 80,
        min_track_frames INTEGER DEFAULT 5,
        roi_required_ratio REAL DEFAULT 0.7,
        alarm_cooldown_seconds INTEGER DEFAULT 10,
        updated_at TEXT DEFAULT (datetime('now','localtime'))
    )""",
    """CREATE TABLE IF NOT EXISTS video_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_type TEXT NOT NULL CHECK (source_type IN ('upload','camera')),
        source_path TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending'
            CHECK (status IN ('pending','running','success','failed')),
        total_frames INTEGER DEFAULT 0,
        processed_frames INTEGER DEFAULT 0,
        roi_x INTEGER DEFAULT 0,
        roi_y INTEGER DEFAULT 0,
        roi_width INTEGER,
        roi_height INTEGER,
        result_video_path TEXT,
        error_message TEXT,
        created_at TEXT DEFAULT (datetime('now','localtime')),
        updated_at TEXT DEFAULT (datetime('now','localtime'))
    )""",
    """CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        video_task_id INTEGER NOT NULL REFERENCES video_tasks(id),
        track_id INTEGER,
        confidence REAL,
        status TEXT NOT NULL DEFAULT 'unconfirmed'
            CHECK (status IN ('unconfirmed','confirmed','false_alarm')),
        snapshot_path TEXT,
        result_video_path TEXT,
        created_at TEXT DEFAULT (datetime('now','localtime')),
        updated_at TEXT DEFAULT (datetime('now','localtime'))
    )""",
    """CREATE TABLE IF NOT EXISTS detection_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        video_task_id INTEGER NOT NULL REFERENCES video_tasks(id),
        frame_id INTEGER NOT NULL,
        bbox_x REAL, bbox_y REAL, bbox_width REAL, bbox_height REAL,
        confidence REAL,
        class_name TEXT DEFAULT 'falling_object'
    )""",
    """CREATE TABLE IF NOT EXISTS tracking_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        video_task_id INTEGER NOT NULL REFERENCES video_tasks(id),
        track_id INTEGER NOT NULL,
        frame_id INTEGER NOT NULL,
        timestamp REAL,
        center_x REAL, center_y REAL,
        bbox_x REAL, bbox_y REAL, bbox_width REAL, bbox_height REAL
    )""",
    """INSERT OR IGNORE INTO system_settings (id) VALUES (1)""",
]


def get_db_path() -> str:
    global _db_path
    if _db_path is not None:
        return _db_path
    data_dir = Path("backend/data")
    data_dir.mkdir(parents=True, exist_ok=True)
    _db_path = str(data_dir / "system.db")
    return _db_path


def init_db() -> None:
    """Create tables and default data. Idempotent — safe to call on every startup."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    for stmt in DDL_STATEMENTS:
        conn.execute(stmt)
    conn.commit()
    conn.close()


def get_db() -> sqlite3.Connection:
    """Return a new connection with row_factory set."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn
