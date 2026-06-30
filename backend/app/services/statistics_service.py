"""Statistics aggregation queries for the dashboard overview."""

from __future__ import annotations

from typing import Any

from backend.app.core.database import get_db


def get_overview() -> dict[str, Any]:
    """Return 6-part statistics overview for the dashboard."""
    db = get_db()
    try:
        # 1) today_event_count
        today_count = db.execute(
            "SELECT COUNT(*) FROM events WHERE date(created_at) = date('now','localtime')"
        ).fetchone()[0]

        # 2) total_event_count
        total_count = db.execute("SELECT COUNT(*) FROM events").fetchone()[0]

        # 3) recent_events — last 5
        recent = [
            dict(row)
            for row in db.execute(
                "SELECT id, track_id, confidence, status, created_at "
                "FROM events ORDER BY created_at DESC LIMIT 5"
            ).fetchall()
        ]

        # 4) daily_trend — last 7 days
        trend = [
            {"date": row[0], "count": row[1]}
            for row in db.execute(
                "SELECT date(created_at) as d, COUNT(*) as cnt "
                "FROM events "
                "WHERE created_at >= datetime('now','localtime','-6 days') "
                "GROUP BY d ORDER BY d"
            ).fetchall()
        ]

        # 5) confidence_distribution — 3 buckets
        conf_buckets = {"low": 0, "mid": 0, "high": 0}
        for row in db.execute("SELECT confidence FROM events").fetchall():
            c = row[0] or 0
            if c < 0.5:
                conf_buckets["low"] += 1
            elif c < 0.7:
                conf_buckets["mid"] += 1
            else:
                conf_buckets["high"] += 1

        # 6) status_distribution
        status_dist = {"unconfirmed": 0, "confirmed": 0, "false_alarm": 0}
        for row in db.execute(
            "SELECT status, COUNT(*) FROM events GROUP BY status"
        ).fetchall():
            status_dist[row[0]] = row[1]

        return {
            "today_event_count": today_count,
            "total_event_count": total_count,
            "recent_events": recent,
            "daily_trend": trend,
            "confidence_distribution": {
                "low_0.35_0.5": conf_buckets["low"],
                "mid_0.5_0.7": conf_buckets["mid"],
                "high_0.7_1.0": conf_buckets["high"],
            },
            "status_distribution": status_dist,
        }
    finally:
        db.close()
