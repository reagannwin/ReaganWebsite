"""Typed configuration loaded from config.yaml."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass(frozen=True)
class VideoConfig:
    frame_stride: int = 3
    max_frames: int = 0


@dataclass(frozen=True)
class DetectionConfig:
    model: str = "yolov8n.pt"
    device: str = "auto"
    confidence: float = 0.35
    imgsz: int = 640


@dataclass(frozen=True)
class TeamsConfig:
    warmup_frames: int = 60
    min_votes: int = 3


@dataclass(frozen=True)
class PlaysConfig:
    start_speed: float = 1.6
    end_speed: float = 0.7
    min_play_seconds: float = 3.0
    merge_gap_seconds: float = 1.5
    cut_threshold: float = 0.5


@dataclass(frozen=True)
class OutputConfig:
    dir: str = "output"


@dataclass(frozen=True)
class PipelineConfig:
    video: VideoConfig = field(default_factory=VideoConfig)
    detection: DetectionConfig = field(default_factory=DetectionConfig)
    teams: TeamsConfig = field(default_factory=TeamsConfig)
    plays: PlaysConfig = field(default_factory=PlaysConfig)
    output: OutputConfig = field(default_factory=OutputConfig)


_SECTIONS = {
    "video": VideoConfig,
    "detection": DetectionConfig,
    "teams": TeamsConfig,
    "plays": PlaysConfig,
    "output": OutputConfig,
}


def load_config(path: str | Path | None = None) -> PipelineConfig:
    """Load config from YAML, falling back to defaults for missing keys."""
    if path is None:
        return PipelineConfig()

    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"Config root must be a mapping, got {type(raw).__name__}")

    kwargs = {}
    for name, cls in _SECTIONS.items():
        section = raw.get(name, {})
        if not isinstance(section, dict):
            raise ValueError(f"Config section '{name}' must be a mapping")
        valid = {f for f in cls.__dataclass_fields__}
        unknown = set(section) - valid
        if unknown:
            raise ValueError(f"Unknown keys in config section '{name}': {sorted(unknown)}")
        kwargs[name] = cls(**section)
    return PipelineConfig(**kwargs)
