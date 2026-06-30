"""System settings read/write."""

from __future__ import annotations

from typing import Any

from backend.app.core.database import get_db

# Parameter validation ranges
VALID_RANGES = {
    "detect_confidence": (0.1, 1.0),
    "downward_ratio": (0.1, 1.0),
    "min_vertical_distance": (10, 500),
    "min_track_frames": (1, 100),
    "roi_required_ratio": (0.0, 1.0),
    "alarm_cooldown_seconds": (0, 300),
    "imgsz": (320, 1920),
}


def get_settings() -> dict[str, Any]:
    """Read the single-row system_settings."""
    db = get_db()
    row = db.execute("SELECT * FROM system_settings WHERE id = 1").fetchone()
    db.close()
    if row is None:
        return {}
    return dict(row)


def update_settings(data: dict[str, Any]) -> dict[str, Any]:
    """Validate and update system_settings. Only updates provided keys."""
    for key, value in data.items():
        if key in VALID_RANGES:
            lo, hi = VALID_RANGES[key]
            if not (lo <= value <= hi):
                raise ValueError(f"{key} 值 {value} 超出范围 [{lo}, {hi}]")

    db = get_db()
    set_clauses = [f"{k} = ?" for k in data if k in VALID_RANGES]
    values = [data[k] for k in data if k in VALID_RANGES]

    if set_clauses:
        set_clauses.append("updated_at = datetime('now','localtime')")
        sql = f"UPDATE system_settings SET {', '.join(set_clauses)} WHERE id = 1"
        db.execute(sql, values)
        db.commit()

    row = db.execute("SELECT * FROM system_settings WHERE id = 1").fetchone()
    db.close()
    return dict(row)
