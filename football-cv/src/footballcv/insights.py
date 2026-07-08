"""Per-play and per-player metrics computed from track histories.

With a field calibration, distances are yards and speeds are mph. Without
one, the same math runs on pixels and units are labeled accordingly —
still useful for relative comparisons within a fixed camera angle.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from .field import YDS_PER_SEC_TO_MPH, FieldCalibration
from .plays import PlaySegment
from .tracking import TrackStore

# Broadcast-tracking speeds above this (mph) are homography/ID-switch noise.
MAX_PLAUSIBLE_MPH = 25.0


@dataclass(frozen=True)
class PlayerPlayStats:
    """One player's movement summary within a single play."""

    track_id: int
    team: int | None
    distance: float
    avg_speed: float
    max_speed: float
    n_points: int


@dataclass(frozen=True)
class PlayStats:
    """Aggregate stats for one detected play."""

    play_number: int
    start_frame: int
    end_frame: int
    start_time_s: float
    duration_s: float
    n_players: int
    units: str  # "yards/mph" or "pixels(relative)"
    players: list[PlayerPlayStats]


def _positions(
    points: list, calibration: FieldCalibration | None
) -> np.ndarray:
    px = np.array([[p.x, p.y] for p in points], dtype=np.float64)
    if calibration is not None:
        return calibration.to_field(px)
    return px


def player_stats_for_play(
    track_id: int,
    points: list,
    team: int | None,
    fps: float,
    calibration: FieldCalibration | None,
) -> PlayerPlayStats | None:
    """Distance and speed for one track inside a play window."""
    if len(points) < 2 or fps <= 0:
        return None

    pos = _positions(points, calibration)
    frames = np.array([p.frame_idx for p in points], dtype=np.float64)
    dt = np.diff(frames) / fps
    valid = dt > 0
    if not valid.any():
        return None

    steps = np.linalg.norm(np.diff(pos, axis=0), axis=1)[valid]
    speeds = steps / dt[valid]

    if calibration is not None:
        speeds_mph = speeds * YDS_PER_SEC_TO_MPH
        # Clamp physically impossible spikes from ID switches / homography edges.
        speeds_mph = speeds_mph[speeds_mph <= MAX_PLAUSIBLE_MPH]
        if speeds_mph.size == 0:
            return None
        return PlayerPlayStats(
            track_id=track_id,
            team=team,
            distance=round(float(steps.sum()), 2),
            avg_speed=round(float(speeds_mph.mean()), 2),
            max_speed=round(float(speeds_mph.max()), 2),
            n_points=len(points),
        )

    return PlayerPlayStats(
        track_id=track_id,
        team=team,
        distance=round(float(steps.sum()), 2),
        avg_speed=round(float(speeds.mean()), 2),
        max_speed=round(float(speeds.max()), 2),
        n_points=len(points),
    )


def compute_play_stats(
    play_number: int,
    segment: PlaySegment,
    store: TrackStore,
    teams: dict[int, int | None],
    fps: float,
    calibration: FieldCalibration | None,
) -> PlayStats:
    """Aggregate every visible player's stats within one play segment."""
    players: list[PlayerPlayStats] = []
    for track_id, points in store.points.items():
        in_play = [p for p in points if segment.start_frame <= p.frame_idx <= segment.end_frame]
        stats = player_stats_for_play(
            track_id, in_play, teams.get(track_id), fps, calibration
        )
        if stats is not None:
            players.append(stats)

    players.sort(key=lambda s: s.max_speed, reverse=True)
    return PlayStats(
        play_number=play_number,
        start_frame=segment.start_frame,
        end_frame=segment.end_frame,
        start_time_s=round(segment.start_frame / fps, 2) if fps > 0 else 0.0,
        duration_s=round(segment.duration_seconds(fps), 2),
        n_players=len(players),
        units="yards/mph" if calibration is not None else "pixels(relative)",
        players=players,
    )


def summarize(all_plays: list[PlayStats]) -> dict:
    """Game-level rollup across every detected play."""
    if not all_plays:
        return {"n_plays": 0}

    durations = [p.duration_s for p in all_plays]
    top_speeds = [pl.max_speed for p in all_plays for pl in p.players]
    per_team: dict[str, dict] = {}
    for play in all_plays:
        for pl in play.players:
            key = str(pl.team) if pl.team is not None else "unknown"
            bucket = per_team.setdefault(key, {"distance": 0.0, "max_speed": 0.0})
            bucket["distance"] = round(bucket["distance"] + pl.distance, 2)
            bucket["max_speed"] = max(bucket["max_speed"], pl.max_speed)

    return {
        "n_plays": len(all_plays),
        "avg_play_duration_s": round(float(np.mean(durations)), 2),
        "longest_play_s": round(max(durations), 2),
        "top_speed_observed": max(top_speeds) if top_speeds else None,
        "units": all_plays[0].units,
        "per_team": per_team,
    }


def play_stats_to_dict(play: PlayStats) -> dict:
    return asdict(play)
