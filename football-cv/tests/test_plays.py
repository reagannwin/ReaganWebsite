from footballcv.plays import PlaySegment, segment_plays

FPS = 10.0  # analyzed-frame rate for these tests


def _run(activity, cuts=frozenset(), **overrides):
    frame_indices = list(range(len(activity)))
    params = dict(
        fps=FPS,
        start_speed=2.0,
        end_speed=1.0,
        min_play_seconds=1.0,
        merge_gap_seconds=0.5,
    )
    params.update(overrides)
    return segment_plays(activity, frame_indices, set(cuts), **params)


def test_returns_empty_when_nothing_moves():
    assert _run([0.5] * 40) == []


def test_detects_single_activity_burst():
    activity = [0.2] * 10 + [3.0] * 20 + [0.2] * 10
    plays = _run(activity)

    assert len(plays) == 1
    assert plays[0].start_frame == 10
    assert plays[0].end_frame == 30


def test_hysteresis_keeps_play_open_through_mid_dip():
    # Dips to 1.5 — below start (2.0) but above end (1.0) — must not split the play.
    activity = [0.2] * 5 + [3.0] * 10 + [1.5] * 5 + [3.0] * 10 + [0.2] * 5
    plays = _run(activity)

    assert len(plays) == 1


def test_camera_cut_terminates_play():
    activity = [0.2] * 5 + [3.0] * 30 + [0.2] * 5
    plays = _run(activity, cuts={20})

    assert len(plays) == 1
    assert plays[0].end_frame == 20


def test_short_bursts_are_discarded():
    activity = [0.2] * 10 + [3.0] * 5 + [0.2] * 10  # 0.5s burst < 1.0s minimum
    assert _run(activity) == []


def test_nearby_segments_merge():
    activity = [0.2] * 5 + [3.0] * 15 + [0.4] * 3 + [3.0] * 15 + [0.2] * 5
    plays = _run(activity)

    assert len(plays) == 1
    assert plays[0].start_frame == 5


def test_segments_do_not_merge_across_cut():
    activity = [0.2] * 5 + [3.0] * 15 + [0.4] * 3 + [3.0] * 15 + [0.2] * 5
    plays = _run(activity, cuts={21})

    assert len(plays) == 2


def test_play_open_at_video_end_is_closed():
    activity = [0.2] * 5 + [3.0] * 20
    plays = _run(activity)

    assert len(plays) == 1
    assert plays[0].end_frame == 24


def test_mismatched_lengths_raise():
    import pytest

    with pytest.raises(ValueError):
        segment_plays(
            [1.0, 2.0], [0], set(), fps=FPS,
            start_speed=2.0, end_speed=1.0,
            min_play_seconds=1.0, merge_gap_seconds=0.5,
        )


def test_duration_seconds():
    assert PlaySegment(10, 40).duration_seconds(10.0) == 3.0
    assert PlaySegment(10, 40).duration_seconds(0.0) == 0.0
