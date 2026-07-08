import numpy as np
import pytest

from footballcv.teams import (
    MIN_JERSEY_PIXELS,
    TeamClassifier,
    assign_teams,
    jersey_color_feature,
    torso_crop,
)


def _solid(color, h=40, w=30):
    return np.full((h, w, 3), color, dtype=np.uint8)


class TestJerseyColorFeature:
    def test_solid_jersey_returns_its_color(self):
        feat = jersey_color_feature(_solid((30, 30, 200)))  # red-ish BGR

        assert feat is not None
        np.testing.assert_allclose(feat, [30, 30, 200], atol=1)

    def test_field_green_is_ignored(self):
        crop = _solid((60, 160, 60))  # green turf
        crop[:10, :, :] = (200, 40, 40)  # blue jersey strip on top

        feat = jersey_color_feature(crop)

        assert feat is not None
        np.testing.assert_allclose(feat, [200, 40, 40], atol=1)

    def test_all_green_crop_returns_none(self):
        assert jersey_color_feature(_solid((60, 160, 60))) is None

    def test_tiny_crop_returns_none(self):
        assert jersey_color_feature(np.empty((0, 0, 3), dtype=np.uint8)) is None
        assert jersey_color_feature(_solid((0, 0, 255), h=3, w=3)) is None


class TestTorsoCrop:
    def test_crop_is_inside_box_and_upper_body(self):
        frame = np.zeros((200, 300, 3), dtype=np.uint8)
        crop = torso_crop(frame, (100.0, 50.0, 160.0, 150.0))

        assert crop.shape[0] == 35  # 15%..50% of 100px height
        assert crop.shape[1] == 36  # middle 60% of 60px width

    def test_degenerate_box_returns_empty(self):
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        assert torso_crop(frame, (50.0, 50.0, 51.0, 51.0)).size == 0


class TestTeamClassifier:
    def test_separates_two_jersey_colors(self):
        red = [np.array([30.0, 30.0, 200.0]) + np.random.default_rng(i).normal(0, 5, 3) for i in range(10)]
        white = [np.array([240.0, 240.0, 240.0]) + np.random.default_rng(i).normal(0, 5, 3) for i in range(10)]

        clf = TeamClassifier()
        assert clf.fit(red + white)

        red_teams = {clf.predict(f) for f in red}
        white_teams = {clf.predict(f) for f in white}
        assert len(red_teams) == 1
        assert len(white_teams) == 1
        assert red_teams != white_teams

    def test_fit_fails_with_too_few_samples(self):
        clf = TeamClassifier()
        assert not clf.fit([np.array([1.0, 2.0, 3.0])] * 3)
        assert not clf.is_fitted

    def test_predict_before_fit_raises(self):
        with pytest.raises(RuntimeError):
            TeamClassifier().predict(np.array([1.0, 2.0, 3.0]))

    def test_team_colors_fallback_before_fit(self):
        assert len(TeamClassifier().team_colors()) == 2


class TestAssignTeams:
    def test_majority_vote(self):
        votes = {1: [0, 0, 1, 0], 2: [1, 1, 1]}
        assert assign_teams(votes, min_votes=3) == {1: 0, 2: 1}

    def test_too_few_votes_is_unassigned(self):
        assert assign_teams({7: [1, 1]}, min_votes=3) == {7: None}

    def test_empty_input(self):
        assert assign_teams({}, min_votes=3) == {}
