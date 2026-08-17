import numpy as np

from gait_research.catalog import NORMALIZED_POINTS, SIDE_CODE_TO_FOOT
from gait_research.events import (
    Event,
    extract_cycles,
    is_alternating,
    parse_events,
    sequence_string,
    contacting_foot_from_heels,
)
from gait_research.normalize import interpolate_columns, normalize_signal
from gait_research.quality import score_cycle


def test_side_map_is_empirical_not_left_equals_one():
    assert SIDE_CODE_TO_FOOT[1] == "R"
    assert SIDE_CODE_TO_FOOT[2] == "L"


def test_parse_and_alternation():
    raw = np.array([[15, 1], [71, 2], [127, 1], [183, 2]])
    events = parse_events(raw)
    assert sequence_string(events) == "R → L → R → L"
    assert is_alternating(events)
    broken = parse_events(np.array([[10, 1], [20, 1], [30, 2]]))
    assert not is_alternating(broken)


def test_contacting_foot_lower_heel():
    assert contacting_foot_from_heels(40.0, 25.0) == "R"
    assert contacting_foot_from_heels(20.0, 40.0) == "L"


def test_extract_left_and_right_cycles():
    fc = parse_events(np.array([[15, 1], [71, 2], [127, 1], [183, 2], [236, 1]]))
    fo = parse_events(np.array([[32, 2], [88, 1], [145, 2], [200, 1]]))
    ms = parse_events(np.array([[51, 2], [107, 1], [164, 2], [218, 1]]))
    cycles = extract_cycles(fc, fo, ms)
    left = [c for c in cycles if c.side == "L"]
    right = [c for c in cycles if c.side == "R"]
    assert len(left) == 1
    assert len(right) == 2
    assert right[0].start_frame == 15 and right[0].end_frame == 127
    assert left[0].start_frame == 71 and left[0].end_frame == 183
    assert right[0].opposite_contact is not None
    assert right[0].opposite_contact.side == "L"
    assert right[0].ipsilateral_foot_off is not None
    assert right[0].ipsilateral_foot_off.side == "R"


def test_normalize_101_points_endpoints():
    t = np.linspace(0, 10, 21)
    arr = np.column_stack([t, t * 2, t * 3])
    out = interpolate_columns(arr, NORMALIZED_POINTS)
    assert out.shape == (101, 3)
    np.testing.assert_allclose(out[0], arr[0], atol=1e-5)
    np.testing.assert_allclose(out[-1], arr[-1], atol=1e-5)


def test_quality_fails_without_opposite_contact():
    fc = parse_events(np.array([[10, 2], [110, 2]]))  # L to L, no right FC
    fo = parse_events(np.array([[80, 2]]))
    ms = parse_events(np.array([[50, 1]]))
    cycles = extract_cycles(fc, fo, ms)
    assert len(cycles) == 1
    dummy = {name: np.ones((200, 3)) for name in ("LASI", "RASI", "LPSI", "RPSI", "LKneeAngles", "RKneeAngles")}
    q = score_cycle(cycles[0], dummy, 100)
    assert q.events_opposite_fc == "FAIL"
    assert q.overall == "FAIL"
    assert q.usable_lower_body is False
