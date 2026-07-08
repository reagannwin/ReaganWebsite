import pytest

from footballcv.config import PipelineConfig, load_config


def test_defaults_without_file():
    config = load_config(None)

    assert isinstance(config, PipelineConfig)
    assert config.detection.model == "yolov8n.pt"
    assert config.video.frame_stride == 3


def test_loads_partial_yaml_with_defaults(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text("detection:\n  model: yolov8m.pt\n", encoding="utf-8")

    config = load_config(path)

    assert config.detection.model == "yolov8m.pt"
    assert config.detection.confidence == 0.35  # default preserved
    assert config.plays.start_speed == 1.6


def test_rejects_unknown_keys(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text("detection:\n  modle: typo.pt\n", encoding="utf-8")

    with pytest.raises(ValueError, match="modle"):
        load_config(path)


def test_rejects_non_mapping_section(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text("video: [1, 2]\n", encoding="utf-8")

    with pytest.raises(ValueError, match="video"):
        load_config(path)


def test_repo_config_file_is_valid():
    from pathlib import Path

    repo_config = Path(__file__).parent.parent / "config.yaml"
    config = load_config(repo_config)

    assert config.video.frame_stride >= 1
    assert 0 < config.detection.confidence < 1
    assert config.plays.end_speed < config.plays.start_speed
