"""Team assignment from jersey colors.

Approach: crop each player's torso, mask out the green field, take the mean
color as a feature, cluster all features into two teams with KMeans, then
give each track a team by majority vote over its sightings.
"""

from __future__ import annotations

from collections import Counter

import cv2
import numpy as np

MIN_JERSEY_PIXELS = 40

# HSV range treated as field turf and excluded from jersey color.
_GREEN_LO = np.array([35, 40, 40])
_GREEN_HI = np.array([90, 255, 255])


def torso_crop(frame: np.ndarray, xyxy: tuple[float, float, float, float]) -> np.ndarray:
    """Crop the jersey region: middle 60% width, upper-middle 15-50% height."""
    h, w = frame.shape[:2]
    x1, y1, x2, y2 = (int(v) for v in xyxy)
    bw, bh = x2 - x1, y2 - y1
    cx1 = max(0, x1 + int(bw * 0.2))
    cx2 = min(w, x2 - int(bw * 0.2))
    cy1 = max(0, y1 + int(bh * 0.15))
    cy2 = min(h, y1 + int(bh * 0.5))
    if cx2 <= cx1 or cy2 <= cy1:
        return np.empty((0, 0, 3), dtype=frame.dtype)
    return frame[cy1:cy2, cx1:cx2]


def jersey_color_feature(crop: np.ndarray) -> np.ndarray | None:
    """Mean BGR color of the crop with field-green pixels removed.

    Returns None when too few non-green pixels remain to be trustworthy.
    """
    if crop.size == 0:
        return None
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    green = cv2.inRange(hsv, _GREEN_LO, _GREEN_HI)
    keep = crop[green == 0]
    if keep.shape[0] < MIN_JERSEY_PIXELS:
        return None
    return keep.reshape(-1, 3).mean(axis=0)


class TeamClassifier:
    """Two-cluster KMeans over jersey color features."""

    def __init__(self) -> None:
        self._kmeans = None

    @property
    def is_fitted(self) -> bool:
        return self._kmeans is not None

    def fit(self, features: list[np.ndarray]) -> bool:
        """Fit on warmup features. Returns False if there aren't enough samples."""
        if len(features) < 8:
            return False
        from sklearn.cluster import KMeans

        self._kmeans = KMeans(n_clusters=2, n_init=10, random_state=0)
        self._kmeans.fit(np.vstack(features))
        return True

    def predict(self, feature: np.ndarray) -> int:
        if self._kmeans is None:
            raise RuntimeError("TeamClassifier.predict called before fit")
        return int(self._kmeans.predict(feature.reshape(1, -1))[0])

    def team_colors(self) -> list[tuple[int, int, int]]:
        """Cluster-center colors as BGR ints, for annotation."""
        if self._kmeans is None:
            return [(200, 200, 200), (60, 60, 60)]
        return [tuple(int(c) for c in center) for center in self._kmeans.cluster_centers_]


def assign_teams(votes: dict[int, list[int]], min_votes: int) -> dict[int, int | None]:
    """Majority-vote a team per track; None when a track has too few sightings."""
    assignments: dict[int, int | None] = {}
    for track_id, team_votes in votes.items():
        if len(team_votes) < min_votes:
            assignments[track_id] = None
        else:
            assignments[track_id] = Counter(team_votes).most_common(1)[0][0]
    return assignments
