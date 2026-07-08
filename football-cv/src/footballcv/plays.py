"""Play segmentation from the activity signal and camera-cut detection.

A broadcast alternates live plays, huddles, replays, and crowd shots. We
segment plays with two signals:
  1. activity — mean tracked-player speed per analyzed frame. Plays are
     bursts of high activity between near-static pre-snap stretches.
  2. camera cuts — sharp histogram changes. A cut hard-terminates any open
     segment so replays don't get stitched onto live action.
"""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class PlaySegment:
    """One detected play, in analyzed-frame indices."""

    start_frame: int
    end_frame: int

    def duration_seconds(self, fps: float) -> float:
        return (self.end_frame - self.start_frame) / fps if fps > 0 else 0.0


def hist_similarity(frame_a: np.ndarray, frame_b: np.ndarray) -> float:
    """HSV histogram correlation between two frames (1.0 = identical)."""
    hists = []
    for frame in (frame_a, frame_b):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv], [0, 1], None, [32, 32], [0, 180, 0, 256])
        cv2.normalize(hist, hist)
        hists.append(hist)
    return float(cv2.compareHist(hists[0], hists[1], cv2.HISTCMP_CORREL))


def segment_plays(
    activity: list[float],
    frame_indices: list[int],
    cut_frames: set[int],
    fps: float,
    start_speed: float,
    end_speed: float,
    min_play_seconds: float,
    merge_gap_seconds: float,
) -> list[PlaySegment]:
    """Hysteresis-threshold the activity signal into play segments.

    A segment opens when activity rises above start_speed, stays open until
    it falls below end_speed, and is force-closed at camera cuts. After a
    cut closes a segment, activity must first settle below end_speed before
    a new one may open — real plays start from a quiet pre-snap state, so
    still-high activity right after a cut is a replay, not a new play. Short
    segments are dropped; segments separated by a small gap are merged.
    """
    if len(activity) != len(frame_indices):
        raise ValueError("activity and frame_indices must be the same length")

    raw: list[PlaySegment] = []
    open_start: int | None = None
    armed = True

    for value, frame_idx in zip(activity, frame_indices):
        is_cut = frame_idx in cut_frames
        if open_start is None:
            if value < end_speed:
                armed = True
            if armed and value >= start_speed and not is_cut:
                open_start = frame_idx
        elif value < end_speed or is_cut:
            raw.append(PlaySegment(open_start, frame_idx))
            open_start = None
            armed = value < end_speed
    if open_start is not None and frame_indices:
        raw.append(PlaySegment(open_start, frame_indices[-1]))

    merged = _merge_segments(raw, fps, merge_gap_seconds, cut_frames)
    return [seg for seg in merged if seg.duration_seconds(fps) >= min_play_seconds]


def _merge_segments(
    segments: list[PlaySegment],
    fps: float,
    merge_gap_seconds: float,
    cut_frames: set[int],
) -> list[PlaySegment]:
    """Merge segments whose gap is short and contains no camera cut."""
    if not segments or fps <= 0:
        return segments

    max_gap = merge_gap_seconds * fps
    merged = [segments[0]]
    for seg in segments[1:]:
        prev = merged[-1]
        gap = seg.start_frame - prev.end_frame
        cut_between = any(prev.end_frame <= c <= seg.start_frame for c in cut_frames)
        if gap <= max_gap and not cut_between:
            merged[-1] = PlaySegment(prev.start_frame, seg.end_frame)
        else:
            merged.append(seg)
    return merged
