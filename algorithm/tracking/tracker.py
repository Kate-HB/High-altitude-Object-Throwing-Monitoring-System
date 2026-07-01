"""DeepSORT multi-object tracker.

Implements the core DeepSORT algorithm:
  - 8-dim Kalman filter (cx, cy, a, h, vx, vy, va, vh)
  - Mahalanobis distance gating with chi-squared threshold
  - Hungarian matching via scipy.optimize.linear_sum_assignment
  - Cascade matching: confirmed tracks matched by time_since_update
  - IOU fallback for unmatched tracks/detections (tentative + overflow)

Outputs TrackingInfo dicts per docs/algorithm-interface.md Section 4.5.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
from scipy.optimize import linear_sum_assignment

# ── Chi-squared thresholds for 95% confidence ──
CHI2_4DOF = 9.4877   # 4-degree measurement: cx, cy, a, h
CHI2_2DOF = 5.9915   # 2-degree IOU gate


class KalmanFilter:
    """8-dim constant-velocity Kalman filter.

    State:  [cx, cy, a, h, vx, vy, va, vh]
    Measurement: [cx, cy, a, h]
    """

    def __init__(self) -> None:
        self._kf_std_weight_pos = 1.0 / 20
        self._kf_std_weight_vel = 1.0 / 160

    def initiate(self, measurement: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Create initial mean and covariance from first measurement."""
        mean = np.zeros(8, dtype=np.float64)
        mean[:4] = measurement
        std = np.array([
            2 * self._kf_std_weight_pos * measurement[3],   # cx
            2 * self._kf_std_weight_pos * measurement[3],   # cy
            1e-2,                                            # a
            2 * self._kf_std_weight_pos * measurement[3],   # h
            10 * self._kf_std_weight_vel * measurement[3],  # vx
            10 * self._kf_std_weight_vel * measurement[3],  # vy
            1e-5,                                            # va
            10 * self._kf_std_weight_vel * measurement[3],  # vh
        ])
        covariance = np.diag(np.square(std))
        return mean, covariance

    def predict(self, mean: np.ndarray, covariance: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Constant-velocity motion model prediction."""
        std_pos = (
            self._kf_std_weight_pos * mean[3]
        )
        std_vel = (
            self._kf_std_weight_vel * mean[3]
        )
        motion_cov = np.diag(np.square([
            std_pos, std_pos, 1e-2, std_pos,
            std_vel, std_vel, 1e-5, std_vel,
        ]))

        # State transition: x_{k+1} = F x_k
        # [cx, cy, a, h, vx, vy, va, vh] += [vx, vy, va, vh, 0,0,0,0] * dt (dt=1)
        F = np.eye(8, dtype=np.float64)
        F[0, 4] = 1.0  # cx += vx
        F[1, 5] = 1.0  # cy += vy
        F[2, 6] = 1.0  # a  += va
        F[3, 7] = 1.0  # h  += vh

        mean = F @ mean
        covariance = F @ covariance @ F.T + motion_cov
        return mean, covariance

    def update(
        self, mean: np.ndarray, covariance: np.ndarray,
        measurement: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Kalman update with 4-dim measurement [cx, cy, a, h]."""
        H = np.zeros((4, 8), dtype=np.float64)
        H[0, 0] = H[1, 1] = H[2, 2] = H[3, 3] = 1.0

        std = self._kf_std_weight_pos * mean[3]
        noise_cov = np.diag(np.square([std, std, 1e-1, std]))
        innovation_cov = H @ covariance @ H.T + noise_cov
        kalman_gain = covariance @ H.T @ np.linalg.inv(innovation_cov)
        innovation = measurement - (H @ mean)
        mean = mean + kalman_gain @ innovation
        covariance = covariance - kalman_gain @ H @ covariance
        return mean, covariance

    def project(
        self, mean: np.ndarray, covariance: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Project state to measurement space."""
        H = np.zeros((4, 8), dtype=np.float64)
        H[0, 0] = H[1, 1] = H[2, 2] = H[3, 3] = 1.0

        std = self._kf_std_weight_pos * mean[3]
        innovation_cov = H @ covariance @ H.T + np.diag(
            np.square([std, std, 1e-1, std])
        )
        return H @ mean, innovation_cov

    def gating_distance(
        self, mean: np.ndarray, covariance: np.ndarray,
        measurements: np.ndarray,
    ) -> np.ndarray:
        """Mahalanobis distances from track to each measurement."""
        projected_mean, projected_cov = self.project(mean, covariance)
        # For singular matrices, use pseudo-inverse
        try:
            inv_cov = np.linalg.inv(projected_cov)
        except np.linalg.LinAlgError:
            inv_cov = np.linalg.pinv(projected_cov)

        diff = measurements - projected_mean
        # Mahalanobis: (x - μ)ᵀ Σ⁻¹ (x - μ)
        distances = np.sum(diff @ inv_cov * diff, axis=1)
        return distances


def _iou(box_a: np.ndarray, box_b: np.ndarray) -> float:
    """IOU between two [x1, y1, x2, y2] boxes."""
    xa = max(float(box_a[0]), float(box_b[0]))
    ya = max(float(box_a[1]), float(box_b[1]))
    xb = min(float(box_a[2]), float(box_b[2]))
    yb = min(float(box_a[3]), float(box_b[3]))
    inter = max(0.0, xb - xa) * max(0.0, yb - ya)
    area_a = (float(box_a[2]) - float(box_a[0])) * (float(box_a[3]) - float(box_a[1]))
    area_b = (float(box_b[2]) - float(box_b[0])) * (float(box_b[3]) - float(box_b[1]))
    denom = area_a + area_b - inter
    return float(inter / denom) if denom > 1e-6 else 0.0


class DeepSORTTracker:
    """DeepSORT multi-object tracker.

    Drop-in replacement for IOUTracker — same output TrackingInfo dicts
    and same ``tracks`` / ``active_track_ids`` interface for pipeline.py.
    """

    def __init__(
        self,
        max_lost: int = 30,
        min_hits: int = 3,
        mahalanobis_threshold: float = CHI2_4DOF,
        iou_threshold: float = 0.3,
    ) -> None:
        self.max_lost = max_lost
        self.min_hits = min_hits
        self.mahalanobis_threshold = mahalanobis_threshold
        self.iou_threshold = iou_threshold
        self._next_id = 1
        self._kf = KalmanFilter()

        # track_id -> {
        #   "mean": np.ndarray (8,),
        #   "covariance": np.ndarray (8,8),
        #   "hits": int,
        #   "time_since_update": int,
        #   "bbox": [x1, y1, x2, y2],
        #   "center": (cx, cy),
        #   "trajectory": [(frame_id, cx, cy, timestamp), ...],
        #   "confidences": [float, ...],
        # }
        self.tracks: dict[int, dict[str, Any]] = {}

    @property
    def active_track_ids(self) -> list[int]:
        """Confirmed track IDs that haven't been lost."""
        return [
            tid for tid, t in self.tracks.items()
            if t["hits"] >= self.min_hits and t["time_since_update"] < self.max_lost
        ]

    def _measurement(self, bbox: list[float]) -> np.ndarray:
        """Convert [x1,y1,x2,y2] bbox to measurement [cx, cy, a, h]."""
        x1, y1, x2, y2 = bbox
        w = max(x2 - x1, 1.0)
        h = max(y2 - y1, 1.0)
        return np.array([(x1 + x2) / 2, (y1 + y2) / 2, w / h, h], dtype=np.float64)

    def _bbox_from_state(self, mean: np.ndarray) -> list[float]:
        """Convert state mean back to [x1, y1, x2, y2]."""
        cx, cy, a, h = mean[0], mean[1], mean[2], mean[3]
        w = max(a * h, 1.0)
        return [float(cx - w / 2), float(cy - h / 2), float(cx + w / 2), float(cy + h / 2)]

    def _predict_all(self) -> None:
        """Run Kalman predict for all active tracks."""
        for t in self.tracks.values():
            t["mean"], t["covariance"] = self._kf.predict(t["mean"], t["covariance"])
            t["time_since_update"] += 1

    def update(
        self,
        detections: list[dict[str, Any]],
        frame_id: int,
        timestamp: float,
    ) -> list[dict[str, Any]]:
        """Match detections to tracks using DeepSORT cascade, return TrackingInfo list."""
        # ── Build detection boxes and measurements ──
        det_boxes: list[list[float]] = []
        meas_list: list[np.ndarray] = []
        for d in detections:
            x1, y1 = float(d["bbox_x"]), float(d["bbox_y"])
            x2, y2 = x1 + float(d["bbox_width"]), y1 + float(d["bbox_height"])
            det_boxes.append([x1, y1, x2, y2])
            meas_list.append(self._measurement([x1, y1, x2, y2]))
        det_measurements = np.stack(meas_list, axis=0) if meas_list else None

        # ── Predict all tracks forward ──
        self._predict_all()

        matched_pairs: list[tuple[int, int]] = []  # (det_idx, track_id)
        matched_det: set[int] = set()

        confirmed = [tid for tid, t in self.tracks.items() if t["hits"] >= self.min_hits]
        tentative = [tid for tid, t in self.tracks.items() if t["hits"] < self.min_hits]

        # ── Step 1: Cascade matching (Mahalanobis) for confirmed tracks ──
        if confirmed and det_measurements is not None and len(det_measurements) > 0:
            unmatched_d = set(range(len(det_boxes)))
            unmatched_t = set(confirmed)

            max_age = max(
                (self.tracks[tid]["time_since_update"] for tid in confirmed), default=0
            )
            for age in range(max_age + 1):
                age_tracks = [tid for tid in unmatched_t
                              if self.tracks[tid]["time_since_update"] == age]
                if not age_tracks or not unmatched_d:
                    break

                det_indices = sorted(unmatched_d)
                meas_subset = det_measurements[det_indices]
                cost = np.zeros((len(age_tracks), len(det_indices)), dtype=np.float64)
                gate = np.zeros((len(age_tracks), len(det_indices)), dtype=bool)

                for i, tid in enumerate(age_tracks):
                    t = self.tracks[tid]
                    distances = self._kf.gating_distance(t["mean"], t["covariance"], meas_subset)
                    cost[i, :] = distances
                    gate[i, :] = distances <= self.mahalanobis_threshold

                cost_masked = np.where(gate, cost, 1e9)
                row_idx, col_idx = linear_sum_assignment(cost_masked)
                for r, c in zip(row_idx, col_idx):
                    if gate[r, c]:
                        tid = age_tracks[r]
                        di = det_indices[c]
                        matched_pairs.append((di, tid))
                        matched_det.add(di)
                        unmatched_d.discard(di)
                        unmatched_t.discard(tid)

        # ── Step 2: IOU matching for tentative + remaining confirmed ──
        matched_trk_set = {p[1] for p in matched_pairs}
        iou_candidates = [t for t in tentative if t not in matched_trk_set]
        iou_candidates += [t for t in confirmed if t not in matched_trk_set]
        unmatched_iou_d = [di for di in range(len(det_boxes)) if di not in matched_det]

        if iou_candidates and unmatched_iou_d:
            cost_iou = np.zeros((len(iou_candidates), len(unmatched_iou_d)), dtype=np.float64)
            for i, tid in enumerate(iou_candidates):
                t_bbox = self.tracks[tid]["bbox"]
                for j, di in enumerate(unmatched_iou_d):
                    cost_iou[i, j] = 1.0 - _iou(np.array(t_bbox), np.array(det_boxes[di]))

            row_idx, col_idx = linear_sum_assignment(cost_iou)
            for r, c in zip(row_idx, col_idx):
                score = 1.0 - cost_iou[r, c]
                if score >= self.iou_threshold:
                    di = unmatched_iou_d[c]
                    tid = iou_candidates[r]
                    matched_pairs.append((di, tid))
                    matched_det.add(di)

        # ── Step 3: Kalman update for matched tracks ──
        matched_trk_final: set[int] = set()
        for di, tid in matched_pairs:
            d = detections[di]
            x1, y1 = float(d["bbox_x"]), float(d["bbox_y"])
            x2, y2 = x1 + float(d["bbox_width"]), y1 + float(d["bbox_height"])
            cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
            t = self.tracks[tid]
            measurement = self._measurement([x1, y1, x2, y2])
            t["mean"], t["covariance"] = self._kf.update(t["mean"], t["covariance"], measurement)
            t["bbox"] = [x1, y1, x2, y2]
            t["center"] = (cx, cy)
            t["hits"] += 1
            t["time_since_update"] = 0
            t["trajectory"].append((frame_id, cx, cy, timestamp))
            t["confidences"].append(d["confidence"])
            matched_trk_final.add(tid)

        # ── Step 4: Unmatched detections → new tracks ──
        for di in range(len(detections)):
            if di not in matched_det:
                d = detections[di]
                x1, y1 = float(d["bbox_x"]), float(d["bbox_y"])
                x2, y2 = x1 + float(d["bbox_width"]), y1 + float(d["bbox_height"])
                cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
                measurement = self._measurement([x1, y1, x2, y2])
                mean, covariance = self._kf.initiate(measurement)
                tid = self._next_id
                self._next_id += 1
                self.tracks[tid] = {
                    "mean": mean,
                    "covariance": covariance,
                    "hits": 1,
                    "time_since_update": 0,
                    "bbox": [x1, y1, x2, y2],
                    "center": (cx, cy),
                    "trajectory": [(frame_id, cx, cy, timestamp)],
                    "confidences": [d["confidence"]],
                }

        # ── Step 5: Prune long-lost tracks ──
        lost_ids = [
            tid for tid, t in self.tracks.items()
            if t["time_since_update"] >= self.max_lost
        ]
        for tid in lost_ids:
            del self.tracks[tid]

        # ── Build TrackingInfo output ──
        results: list[dict[str, Any]] = []
        for tid in self.active_track_ids:
            t = self.tracks[tid]
            x1, y1, x2, y2 = t["bbox"]
            results.append({
                "track_id": tid,
                "frame_id": frame_id,
                "timestamp": timestamp,
                "center_x": float(x1 + x2) / 2,
                "center_y": float(y1 + y2) / 2,
                "bbox_x": float(x1),
                "bbox_y": float(y1),
                "bbox_width": float(x2 - x1),
                "bbox_height": float(y2 - y1),
            })
        return results
