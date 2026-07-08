"""YOLO-based player and ball detection on broadcast frames."""

from __future__ import annotations

import numpy as np

PERSON_CLASS_ID = 0
BALL_CLASS_ID = 32  # COCO "sports ball"


def resolve_device(requested: str) -> str:
    """Map 'auto' to cuda when available, else cpu."""
    if requested != "auto":
        return requested
    try:
        import torch

        return "cuda:0" if torch.cuda.is_available() else "cpu"
    except ImportError:
        return "cpu"


class PlayerDetector:
    """Wraps an Ultralytics YOLO model, returning supervision Detections."""

    def __init__(self, model_path: str, device: str, confidence: float, imgsz: int):
        from ultralytics import YOLO  # deferred: heavy import

        self.model = YOLO(model_path)
        self.device = resolve_device(device)
        self.confidence = confidence
        self.imgsz = imgsz

    def detect(self, frame: np.ndarray):
        """Run detection on one BGR frame. Returns sv.Detections (players + ball)."""
        import supervision as sv

        results = self.model(
            frame,
            imgsz=self.imgsz,
            conf=self.confidence,
            classes=[PERSON_CLASS_ID, BALL_CLASS_ID],
            device=self.device,
            verbose=False,
        )
        return sv.Detections.from_ultralytics(results[0])


def split_players_and_ball(detections):
    """Split combined detections into (players, ball) by class id."""
    players = detections[detections.class_id == PERSON_CLASS_ID]
    ball = detections[detections.class_id == BALL_CLASS_ID]
    return players, ball
