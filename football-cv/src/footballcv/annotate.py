"""Render the annotated output video: team-colored boxes, IDs, play HUD."""

from __future__ import annotations

import cv2
import numpy as np

from .plays import PlaySegment
from .tracking import TrackStore

_UNASSIGNED_COLOR = (180, 180, 180)
_HUD_LIVE = (60, 200, 60)
_HUD_IDLE = (70, 70, 70)


def _readable(color: tuple[int, int, int]) -> tuple[int, int, int]:
    """Boost very dark cluster colors so boxes stay visible on grass."""
    b, g, r = color
    if b + g + r < 120:
        return (min(b + 80, 255), min(g + 80, 255), min(r + 80, 255))
    return color


def draw_frame(
    frame: np.ndarray,
    frame_idx: int,
    store: TrackStore,
    teams: dict[int, int | None],
    team_colors: list[tuple[int, int, int]],
    active_play: PlaySegment | None,
    play_number: int | None,
    fps: float,
) -> np.ndarray:
    """Draw all annotations for one frame onto a copy and return it."""
    out = frame.copy()

    for track_id, xyxy in store.boxes.get(frame_idx, {}).items():
        team = teams.get(track_id)
        color = _readable(team_colors[team]) if team is not None else _UNASSIGNED_COLOR
        x1, y1, x2, y2 = (int(v) for v in xyxy)
        cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)
        label = f"#{track_id}" + (f" T{team}" if team is not None else "")
        cv2.putText(out, label, (x1, max(12, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2.LINE_AA)

    _draw_hud(out, frame_idx, active_play, play_number, fps)
    return out


def _draw_hud(
    frame: np.ndarray,
    frame_idx: int,
    active_play: PlaySegment | None,
    play_number: int | None,
    fps: float,
) -> None:
    if active_play is not None and play_number is not None:
        elapsed = (frame_idx - active_play.start_frame) / fps if fps > 0 else 0.0
        text = f"PLAY {play_number}  {elapsed:4.1f}s"
        color = _HUD_LIVE
    else:
        text = "between plays"
        color = _HUD_IDLE

    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
    cv2.rectangle(frame, (10, 10), (24 + tw, 26 + th), (0, 0, 0), -1)
    cv2.putText(frame, text, (17, 18 + th), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2, cv2.LINE_AA)


def play_at_frame(
    frame_idx: int, segments: list[PlaySegment]
) -> tuple[PlaySegment | None, int | None]:
    """The play covering this frame, if any, with its 1-based number."""
    for i, seg in enumerate(segments, start=1):
        if seg.start_frame <= frame_idx <= seg.end_frame:
            return seg, i
    return None, None
