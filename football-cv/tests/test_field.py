import numpy as np
import pytest

from footballcv.field import FieldCalibration


# A synthetic camera: field rectangle (10,10)-(50,40) yards seen as a
# quadrilateral in a 1280x720 frame.
PIXEL_PTS = [(200.0, 600.0), (1080.0, 600.0), (900.0, 200.0), (380.0, 200.0)]
FIELD_PTS = [(10.0, 10.0), (50.0, 10.0), (50.0, 40.0), (10.0, 40.0)]


def test_calibration_roundtrips_reference_points():
    cal = FieldCalibration.from_pairs(PIXEL_PTS, FIELD_PTS)

    out = cal.to_field(np.array(PIXEL_PTS))

    np.testing.assert_allclose(out, FIELD_PTS, atol=1e-6)


def test_interior_point_maps_inside_field_region():
    cal = FieldCalibration.from_pairs(PIXEL_PTS, FIELD_PTS)

    center_px = np.array([[640.0, 400.0]])
    x, y = cal.to_field(center_px)[0]

    assert 10.0 < x < 50.0
    assert 10.0 < y < 40.0


def test_requires_four_point_pairs():
    with pytest.raises(ValueError):
        FieldCalibration.from_pairs(PIXEL_PTS[:3], FIELD_PTS[:3])
    with pytest.raises(ValueError):
        FieldCalibration.from_pairs(PIXEL_PTS, FIELD_PTS[:3])


def test_save_and_load_roundtrip(tmp_path):
    cal = FieldCalibration.from_pairs(PIXEL_PTS, FIELD_PTS)
    path = tmp_path / "calibration.json"

    cal.save(path)
    loaded = FieldCalibration.load(path)

    np.testing.assert_allclose(loaded.homography, cal.homography)


def test_load_rejects_bad_shape(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text('{"homography": [[1, 2], [3, 4]]}', encoding="utf-8")

    with pytest.raises(ValueError):
        FieldCalibration.load(path)
