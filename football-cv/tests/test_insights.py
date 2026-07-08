import numpy as np

from footballcv.field import FieldCalibration
from footballcv.insights import (
    compute_play_stats,
    player_stats_for_play,
    summarize,
)
from footballcv.plays import PlaySegment
from footballcv.tracking import TrackPoint, TrackStore

FPS = 30.0


def _identity_calibration():
    """Pixels == yards, so expected values are easy to reason about."""
    px = [(0.0, 0.0), (100.0, 0.0), (100.0, 50.0), (0.0, 50.0)]
    return FieldCalibration.from_pairs(px, px)


def _straight_run(n=31, step=0.2):
    """A track moving `step` units per frame along x: speed = step*FPS units/s."""
    return [TrackPoint(i, i * step, 10.0) for i in range(n)]


class TestPlayerStats:
    def test_distance_and_speed_in_yards(self):
        # 0.2 yd/frame at 30fps = 6 yd/s ≈ 12.27 mph
        stats = player_stats_for_play(1, _straight_run(), 0, FPS, _identity_calibration())

        assert stats is not None
        assert stats.distance == 6.0
        assert 12.2 <= stats.max_speed <= 12.4
        assert stats.avg_speed == stats.max_speed  # constant speed run

    def test_pixel_fallback_without_calibration(self):
        stats = player_stats_for_play(1, _straight_run(), None, FPS, None)

        assert stats is not None
        assert stats.distance == 6.0
        assert stats.max_speed == 6.0  # px/s, no mph conversion

    def test_implausible_speeds_are_clamped(self):
        # 2 yd/frame at 30fps = 60 yd/s — impossible; all samples get dropped.
        points = [TrackPoint(i, i * 2.0, 10.0) for i in range(10)]
        stats = player_stats_for_play(1, points, 0, FPS, _identity_calibration())

        assert stats is None

    def test_single_point_returns_none(self):
        assert player_stats_for_play(1, [TrackPoint(0, 0.0, 0.0)], 0, FPS, None) is None

    def test_zero_fps_returns_none(self):
        assert player_stats_for_play(1, _straight_run(), 0, 0.0, None) is None


class TestComputePlayStats:
    def _store(self):
        store = TrackStore()
        for point in _straight_run():
            store.add(point.frame_idx, 1, (point.x - 1, point.y - 2, point.x + 1, point.y))
        # Track 2 only exists outside the play window.
        store.add(100, 2, (0.0, 0.0, 2.0, 2.0))
        store.add(101, 2, (1.0, 0.0, 3.0, 2.0))
        return store

    def test_only_in_window_tracks_are_counted(self):
        play = compute_play_stats(
            1, PlaySegment(0, 30), self._store(), {1: 0, 2: 1}, FPS, None
        )

        assert play.n_players == 1
        assert play.players[0].track_id == 1
        assert play.players[0].team == 0
        assert play.units == "pixels(relative)"

    def test_duration_and_start_time(self):
        play = compute_play_stats(1, PlaySegment(30, 120), TrackStore(), {}, FPS, None)

        assert play.start_time_s == 1.0
        assert play.duration_s == 3.0


class TestSummarize:
    def test_empty(self):
        assert summarize([]) == {"n_plays": 0}

    def test_rollup(self):
        store = TrackStore()
        for point in _straight_run():
            store.add(point.frame_idx, 1, (point.x - 1, point.y - 2, point.x + 1, point.y))
        play = compute_play_stats(1, PlaySegment(0, 30), store, {1: 0}, FPS, None)

        summary = summarize([play, play])

        assert summary["n_plays"] == 2
        assert summary["avg_play_duration_s"] == play.duration_s
        assert summary["top_speed_observed"] == 6.0
        assert summary["per_team"]["0"]["distance"] == 12.0
