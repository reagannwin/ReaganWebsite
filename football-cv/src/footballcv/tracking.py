"""Multi-object tracking and per-track position history."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TrackPoint:
    """One sighting of a tracked player: frame index and feet position (px)."""

    frame_idx: int
    x: float
    y: float


@dataclass
class TrackStore:
    """Accumulates the feet-position history of every track across the video."""

    points: dict[int, list[TrackPoint]] = field(default_factory=dict)
    boxes: dict[int, dict[int, tuple[float, float, float, float]]] = field(
        default_factory=dict
    )

    def add(self, frame_idx: int, track_id: int, xyxy: tuple[float, float, float, float]) -> None:
        x1, y1, x2, y2 = xyxy
        foot = TrackPoint(frame_idx, (x1 + x2) / 2.0, y2)  # bottom-center = feet
        self.points.setdefault(track_id, []).append(foot)
        self.boxes.setdefault(frame_idx, {})[track_id] = (x1, y1, x2, y2)

    def track_ids(self) -> list[int]:
        return sorted(self.points)


class PlayerTracker:
    """ByteTrack wrapper that keeps stable IDs across frames."""

    def __init__(self, fps: float):
        import supervision as sv

        self.tracker = sv.ByteTrack(frame_rate=max(1, round(fps)))

    def update(self, detections):
        """Assign track IDs to this frame's detections."""
        return self.tracker.update_with_detections(detections)


def frame_mean_speed(store: TrackStore, frame_idx: int, prev_idx: int) -> float:
    """Mean per-frame displacement (px) of tracks seen in both frames.

    Used as the raw 'activity' signal for play segmentation. Returns 0.0
    when fewer than 2 tracks are visible in both frames (unreliable signal).
    """
    prev = store.boxes.get(prev_idx, {})
    cur = store.boxes.get(frame_idx, {})
    common = prev.keys() & cur.keys()
    if len(common) < 2:
        return 0.0

    total = 0.0
    for tid in common:
        px1, py1, px2, py2 = prev[tid]
        cx1, cy1, cx2, cy2 = cur[tid]
        pfx, pfy = (px1 + px2) / 2.0, py2
        cfx, cfy = (cx1 + cx2) / 2.0, cy2
        total += ((cfx - pfx) ** 2 + (cfy - pfy) ** 2) ** 0.5
    return total / len(common)
