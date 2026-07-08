"""Interactive field calibration: click landmarks, enter their yard positions.

Usage flow: a window shows a frame from the video. Click 4+ points whose
real field position you know (yard-line × sideline/hash intersections work
best), then enter each point's field coordinates in the terminal. Saves a
homography JSON the pipeline uses to report yards and mph.
"""

from __future__ import annotations

import logging
from pathlib import Path

import cv2

from .field import FIELD_LENGTH_YD, FIELD_WIDTH_YD, FieldCalibration

log = logging.getLogger("footballcv")

_WINDOW = "footballcv calibration — click landmarks, press ENTER when done"


def _grab_frame(video_path: Path, at_seconds: float) -> "cv2.typing.MatLike":
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")
    cap.set(cv2.CAP_PROP_POS_MSEC, at_seconds * 1000.0)
    ok, frame = cap.read()
    cap.release()
    if not ok:
        raise RuntimeError(f"Could not read a frame at {at_seconds}s from {video_path}")
    return frame


def _collect_clicks(frame) -> list[tuple[float, float]]:
    clicks: list[tuple[float, float]] = []
    display = frame.copy()

    def on_mouse(event, x, y, _flags, _param):
        if event == cv2.EVENT_LBUTTONDOWN:
            clicks.append((float(x), float(y)))
            cv2.circle(display, (x, y), 6, (0, 0, 255), -1)
            cv2.putText(display, str(len(clicks)), (x + 8, y - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    cv2.namedWindow(_WINDOW, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(_WINDOW, on_mouse)
    while True:
        cv2.imshow(_WINDOW, display)
        key = cv2.waitKey(30) & 0xFF
        if key in (13, 10):  # ENTER
            break
        if key == 27:  # ESC
            clicks.clear()
            break
    cv2.destroyAllWindows()
    return clicks


def _ask_field_coords(n_points: int) -> list[tuple[float, float]]:
    print("\nField coordinate system:")
    print("  x: 0-120 yards along the sideline (goal lines at x=10 and x=110)")
    print("  y: 0-53.3 yards across the field (0 = near sideline)\n")
    coords: list[tuple[float, float]] = []
    for i in range(1, n_points + 1):
        while True:
            raw = input(f"Point {i} field position as 'x y' (e.g. '30 0'): ").strip()
            try:
                x_str, y_str = raw.split()
                x, y = float(x_str), float(y_str)
            except ValueError:
                print("  Please enter two numbers separated by a space.")
                continue
            if not (0 <= x <= FIELD_LENGTH_YD and 0 <= y <= FIELD_WIDTH_YD):
                print(f"  Out of range (x 0-{FIELD_LENGTH_YD}, y 0-{FIELD_WIDTH_YD}).")
                continue
            coords.append((x, y))
            break
    return coords


def calibrate_interactive(video_path: str | Path, out_path: str | Path, at_seconds: float = 0.0) -> Path:
    """Run the click-and-type calibration flow. Returns the saved JSON path."""
    frame = _grab_frame(Path(video_path), at_seconds)
    clicks = _collect_clicks(frame)
    if len(clicks) < 4:
        raise SystemExit("Calibration cancelled — need at least 4 clicked points.")

    field_pts = _ask_field_coords(len(clicks))
    calibration = FieldCalibration.from_pairs(clicks, field_pts)
    calibration.save(out_path)
    log.info("Calibration saved to %s", out_path)
    return Path(out_path)
