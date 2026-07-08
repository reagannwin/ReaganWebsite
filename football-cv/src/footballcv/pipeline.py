"""End-to-end analysis pipeline.

Pass 1 walks the video once: detect → track → collect jersey colors →
measure activity → flag camera cuts. After the pass, plays are segmented,
teams are voted, and stats are computed. An optional pass 2 re-reads the
video and renders the fully-annotated output (done second so every frame
can be drawn with final team labels and play numbers).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import cv2

from .annotate import draw_frame, play_at_frame
from .config import PipelineConfig
from .detection import PlayerDetector, split_players_and_ball
from .field import FieldCalibration
from .insights import PlayStats, compute_play_stats
from .plays import PlaySegment, hist_similarity, segment_plays
from .report import write_reports
from .teams import TeamClassifier, assign_teams, jersey_color_feature, torso_crop
from .tracking import PlayerTracker, TrackStore, frame_mean_speed

log = logging.getLogger("footballcv")

_PROGRESS_EVERY = 150


@dataclass
class AnalysisResult:
    """Everything pass 1 + analytics produced, for reporting and rendering."""

    video_path: Path
    fps: float
    store: TrackStore
    teams: dict[int, int | None]
    team_colors: list[tuple[int, int, int]]
    segments: list[PlaySegment]
    plays: list[PlayStats] = field(default_factory=list)


def analyze_video(
    video_path: str | Path,
    config: PipelineConfig,
    calibration: FieldCalibration | None = None,
) -> AnalysisResult:
    """Pass 1 + analytics. Raises FileNotFoundError/RuntimeError on bad input."""
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    stride = max(1, config.video.frame_stride)
    log.info("Analyzing %s (%.1f fps, %d frames, stride %d)", video_path.name, fps, total, stride)

    detector = PlayerDetector(
        config.detection.model,
        config.detection.device,
        config.detection.confidence,
        config.detection.imgsz,
    )
    tracker = PlayerTracker(fps=fps / stride)
    store = TrackStore()
    classifier = TeamClassifier()

    warmup_features: list = []
    track_features: dict[int, list] = {}
    activity: list[float] = []
    frame_indices: list[int] = []
    cut_frames: set[int] = set()

    prev_small = None
    prev_idx: int | None = None
    frame_idx = -1
    analyzed = 0

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frame_idx += 1
            if frame_idx % stride != 0:
                continue
            if config.video.max_frames and analyzed >= config.video.max_frames:
                break
            analyzed += 1

            small = cv2.resize(frame, (320, 180))
            if prev_small is not None and hist_similarity(prev_small, small) < config.plays.cut_threshold:
                cut_frames.add(frame_idx)
                tracker = PlayerTracker(fps=fps / stride)  # cuts invalidate track continuity
            prev_small = small

            detections = detector.detect(frame)
            players, _ball = split_players_and_ball(detections)
            tracked = tracker.update(players)

            for xyxy, track_id in zip(tracked.xyxy, tracked.tracker_id):
                tid = int(track_id)
                store.add(frame_idx, tid, tuple(float(v) for v in xyxy))
                feat = jersey_color_feature(torso_crop(frame, xyxy))
                if feat is not None:
                    track_features.setdefault(tid, []).append(feat)
                    if analyzed <= config.teams.warmup_frames:
                        warmup_features.append(feat)

            frame_indices.append(frame_idx)
            activity.append(0.0 if prev_idx is None else frame_mean_speed(store, frame_idx, prev_idx) / stride)
            prev_idx = frame_idx

            if analyzed % _PROGRESS_EVERY == 0:
                log.info("  frame %d/%d — %d tracks, %d cuts", frame_idx, total, len(store.points), len(cut_frames))
    finally:
        cap.release()

    teams = _classify_teams(classifier, warmup_features, track_features, config.teams.min_votes)
    segments = segment_plays(
        activity,
        frame_indices,
        cut_frames,
        fps=fps / stride,
        start_speed=config.plays.start_speed,
        end_speed=config.plays.end_speed,
        min_play_seconds=config.plays.min_play_seconds,
        merge_gap_seconds=config.plays.merge_gap_seconds,
    )
    log.info("Detected %d plays, %d camera cuts, %d tracks", len(segments), len(cut_frames), len(store.points))

    result = AnalysisResult(
        video_path=video_path,
        fps=fps,
        store=store,
        teams=teams,
        team_colors=classifier.team_colors(),
        segments=segments,
    )
    result.plays = [
        compute_play_stats(i, seg, store, teams, fps, calibration)
        for i, seg in enumerate(segments, start=1)
    ]
    return result


def _classify_teams(
    classifier: TeamClassifier,
    warmup_features: list,
    track_features: dict[int, list],
    min_votes: int,
) -> dict[int, int | None]:
    """Fit team clusters on warmup colors, then majority-vote each track."""
    if not classifier.fit(warmup_features):
        log.warning("Not enough jersey samples to split teams — all tracks unassigned")
        return {tid: None for tid in track_features}

    votes = {
        tid: [classifier.predict(f) for f in feats]
        for tid, feats in track_features.items()
    }
    return assign_teams(votes, min_votes)


def render_video(result: AnalysisResult, config: PipelineConfig, out_dir: Path) -> Path:
    """Pass 2: write the annotated video next to the reports."""
    cap = cv2.VideoCapture(str(result.video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not reopen video for rendering: {result.video_path}")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out_path = out_dir / "annotated.mp4"
    writer = cv2.VideoWriter(
        str(out_path), cv2.VideoWriter_fourcc(*"mp4v"), result.fps, (width, height)
    )
    if not writer.isOpened():
        cap.release()
        raise RuntimeError("Could not open video writer (missing mp4 codec?)")

    stride = max(1, config.video.frame_stride)
    frame_idx = -1
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frame_idx += 1
            # Frames skipped during analysis borrow boxes from the last analyzed frame.
            box_frame = frame_idx - (frame_idx % stride)
            seg, num = play_at_frame(frame_idx, result.segments)
            writer.write(
                draw_frame(
                    frame, box_frame, result.store, result.teams,
                    result.team_colors, seg, num, result.fps,
                )
            )
    finally:
        cap.release()
        writer.release()
    log.info("Annotated video written to %s", out_path)
    return out_path


def run(
    video_path: str | Path,
    config: PipelineConfig,
    calibration_path: str | Path | None = None,
    render: bool = False,
) -> Path:
    """Full pipeline entry point. Returns the output directory."""
    calibration = FieldCalibration.load(calibration_path) if calibration_path else None
    if calibration is None:
        log.info("No calibration file — reporting relative pixel metrics. "
                 "Run the 'calibrate' command to get yards and mph.")

    result = analyze_video(video_path, config, calibration)
    out_dir = Path(config.output.dir) / Path(video_path).stem
    write_reports(result.plays, out_dir, Path(video_path).name)
    if render:
        render_video(result, config, out_dir)
    return out_dir
