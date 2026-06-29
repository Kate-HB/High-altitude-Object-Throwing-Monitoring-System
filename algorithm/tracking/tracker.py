"""IOU-based multi-object tracker — simplified fallback for DeepSORT.

Outputs TrackingInfo dicts per docs/algorithm-interface.md Section 4.5.
Field format identical to DeepSORT output for drop-in replacement.
"""

from __future__ import annotations

from typing import Any


def _iou(box_a: list[float], box_b: list[float]) -> float:
    """IOU between two [x1, y1, x2, y2] boxes."""
    xa = max(box_a[0], box_b[0])
    ya = max(box_a[1], box_b[1])
    xb = min(box_a[2], box_b[2])
    yb = min(box_a[3], box_b[3])
    inter = max(0.0, xb - xa) * max(0.0, yb - ya)
    area_a = (box_a[2] - box_a[0]) * (box_a[3] - box_a[1])
    area_b = (box_b[2] - box_b[0]) * (box_b[3] - box_b[1])
    denom = area_a + area_b - inter
    return inter / denom if denom > 1e-6 else 0.0


class IOUTracker:
    """Simple IOU-based multi-object tracker.

    Drop-in compatible with DeepSORT — output TrackingInfo dicts
    always have the same 9 fields defined in docs/algorithm-interface.md.
    """

    def __init__(
        self,
        iou_threshold: float = 0.3,
        max_lost: int = 30,
        min_hits: int = 3,
    ) -> None:
        self.iou_threshold = iou_threshold
        self.max_lost = max_lost
        self.min_hits = min_hits
        self._next_id = 1

        # track_id -> {
        #   "bbox": [x1, y1, x2, y2],
        #   "center": (cx, cy),
        #   "lost": int,
        #   "hits": int,
        #   "trajectory": [(frame_id, cx, cy, timestamp), ...],
        #   "confidences": [float, ...],
        #   "bbox_history": [(x1, y1, x2, y2), ...],
        # }
        self.tracks: dict[int, dict[str, Any]] = {}

    @property
    def active_track_ids(self) -> list[int]:
        """Confirmed track IDs that haven't been lost."""
        return [
            tid for tid, t in self.tracks.items()
            if t["hits"] >= self.min_hits and t["lost"] < self.max_lost
        ]

    def update(
        self,
        detections: list[dict[str, Any]],
        frame_id: int,
        timestamp: float,
    ) -> list[dict[str, Any]]:
        """Match detections to tracks, return TrackingInfo list for this frame.

        Args:
            detections: DetectionInfo dicts from detector.predict_frame().
            frame_id: Current frame number.
            timestamp: Frame timestamp in seconds.

        Returns:
            List of TrackingInfo dicts (9 fields per contract).
        """
        # Build bbox list from detections
        det_boxes: list[list[float]] = []
        for d in detections:
            x1, y1 = d["bbox_x"], d["bbox_y"]
            x2, y2 = x1 + d["bbox_width"], y1 + d["bbox_height"]
            det_boxes.append([x1, y1, x2, y2])

        # Get active tracks (not yet removed)
        active_ids = [tid for tid, t in self.tracks.items() if t["lost"] < self.max_lost]

        matched_det: set[int] = set()
        matched_trk: set[int] = set()

        # Greedy IOU matching
        pairs: list[tuple[float, int, int]] = []
        if det_boxes and active_ids:
            for di, dbox in enumerate(det_boxes):
                for tid in active_ids:
                    tbox = self.tracks[tid]["bbox"]
                    score = _iou(dbox, tbox)
                    if score >= self.iou_threshold:
                        pairs.append((score, di, tid))
            pairs.sort(key=lambda x: x[0], reverse=True)
            for _, di, tid in pairs:
                if di not in matched_det and tid not in matched_trk:
                    matched_det.add(di)
                    matched_trk.add(tid)

        # Update matched tracks
        for di, tid in ((d, t) for _, d, t in pairs if d in matched_det and t in matched_trk):
            d = detections[di]
            x1, y1 = d["bbox_x"], d["bbox_y"]
            x2, y2 = x1 + d["bbox_width"], y1 + d["bbox_height"]
            cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
            t = self.tracks[tid]
            t["bbox"] = [x1, y1, x2, y2]
            t["center"] = (cx, cy)
            t["lost"] = 0
            t["hits"] += 1
            t["trajectory"].append((frame_id, cx, cy, timestamp))
            t["confidences"].append(d["confidence"])

        # Unmatched detections → new tracks
        for di in range(len(detections)):
            if di not in matched_det:
                d = detections[di]
                x1, y1 = d["bbox_x"], d["bbox_y"]
                x2, y2 = x1 + d["bbox_width"], y1 + d["bbox_height"]
                cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
                tid = self._next_id
                self._next_id += 1
                self.tracks[tid] = {
                    "bbox": [x1, y1, x2, y2],
                    "center": (cx, cy),
                    "lost": 0,
                    "hits": 1,
                    "trajectory": [(frame_id, cx, cy, timestamp)],
                    "confidences": [d["confidence"]],
                }

        # Unmatched active tracks → increment lost counter
        for tid in active_ids:
            if tid not in matched_trk:
                self.tracks[tid]["lost"] += 1

        # Prune long-lost tracks
        lost_ids = [tid for tid, t in self.tracks.items() if t["lost"] >= self.max_lost]
        for tid in lost_ids:
            del self.tracks[tid]

        # Build TrackingInfo output for all active (confirmed) tracks this frame
        results: list[dict[str, Any]] = []
        for tid in self.active_track_ids:
            t = self.tracks[tid]
            x1, y1, x2, y2 = t["bbox"]
            results.append({
                "track_id": tid,
                "frame_id": frame_id,
                "timestamp": timestamp,
                "center_x": float(t["center"][0]),
                "center_y": float(t["center"][1]),
                "bbox_x": float(x1),
                "bbox_y": float(y1),
                "bbox_width": float(x2 - x1),
                "bbox_height": float(y2 - y1),
            })
        return results
