"""Field calibration: map broadcast pixels to real field coordinates (yards).

Broadcast camera auto-calibration is a research problem in itself, so this
uses a pragmatic approach: the user clicks 4+ landmarks (yard-line/sideline
intersections) once per camera angle and enters their known field positions.
The resulting homography converts pixel positions to yards, unlocking real
speeds and distances. Without a calibration file the pipeline still runs and
reports pixel-based relative metrics.

Field coordinate system: x = 0..120 yd along the sidelines (goal line at
x=10 and x=110), y = 0..53.3 yd across the field.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

FIELD_LENGTH_YD = 120.0
FIELD_WIDTH_YD = 53.3
YDS_PER_SEC_TO_MPH = 3600.0 / 1760.0  # 1 yd/s ≈ 2.045 mph


@dataclass(frozen=True)
class FieldCalibration:
    """Pixel→yards homography built from user-clicked landmark pairs."""

    homography: np.ndarray

    @classmethod
    def from_pairs(
        cls,
        pixel_points: list[tuple[float, float]],
        field_points: list[tuple[float, float]],
    ) -> "FieldCalibration":
        if len(pixel_points) < 4 or len(pixel_points) != len(field_points):
            raise ValueError("Calibration needs at least 4 matched point pairs")
        src = np.array(pixel_points, dtype=np.float64)
        dst = np.array(field_points, dtype=np.float64)
        matrix, _ = cv2.findHomography(src, dst, method=0)
        if matrix is None:
            raise ValueError("Could not compute homography — are the points collinear?")
        return cls(homography=matrix)

    def to_field(self, points_px: np.ndarray) -> np.ndarray:
        """Transform an (N, 2) array of pixel points to field yards."""
        pts = np.asarray(points_px, dtype=np.float64).reshape(-1, 1, 2)
        out = cv2.perspectiveTransform(pts, self.homography)
        return out.reshape(-1, 2)

    def save(self, path: str | Path) -> None:
        Path(path).write_text(
            json.dumps({"homography": self.homography.tolist()}, indent=2),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: str | Path) -> "FieldCalibration":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        matrix = np.array(data["homography"], dtype=np.float64)
        if matrix.shape != (3, 3):
            raise ValueError(f"Invalid homography shape {matrix.shape} in {path}")
        return cls(homography=matrix)
