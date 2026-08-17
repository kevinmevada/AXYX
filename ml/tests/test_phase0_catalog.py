from gait_research.catalog import (
    EXPECTED_JOINT_ANGLE_COUNT,
    EXPECTED_JOINT_CENTER_COUNT,
    EXPECTED_MARKER_COUNT,
    EXPECTED_WALKING_SIGNAL_COUNT,
    JOINT_ANGLES,
    JOINT_CENTERS,
    MARKERS,
    SEGMENT_COM,
    WALKING_KINEMATICS,
    WHOLE_BODY_COM,
    classify_signal,
)
from gait_research.sessions import classify_session


def test_catalog_counts():
    assert len(MARKERS) == EXPECTED_MARKER_COUNT == 37
    assert len(JOINT_ANGLES) == EXPECTED_JOINT_ANGLE_COUNT == 26
    assert len(JOINT_CENTERS) == EXPECTED_JOINT_CENTER_COUNT == 6
    assert len(WHOLE_BODY_COM) == 2
    assert len(SEGMENT_COM) == 15
    assert len(WALKING_KINEMATICS) == EXPECTED_WALKING_SIGNAL_COUNT == 86


def test_catalog_unique():
    assert len(set(WALKING_KINEMATICS)) == len(WALKING_KINEMATICS)
    assert set(JOINT_CENTERS) == {"LHJC", "RHJC", "LKJC", "RKJC", "LAJC", "RAJC"}


def test_classify_signal():
    assert classify_signal("LKNE") == "marker"
    assert classify_signal("LHipAngles") == "joint_angle"
    assert classify_signal("LHJC") == "joint_center"
    assert classify_signal("CentreOfMass") == "com"
    assert classify_signal("PelvisCOM") == "segment_com"
    assert classify_signal("not_a_signal") == "other"


def test_classify_session_canonical_walking():
    meta = classify_session("WU01")
    assert meta["session_type"] == "walking"
    assert meta["is_walking"] is True
    assert meta["is_irregular_name"] is False


def test_classify_session_irregular_names_not_renamed():
    wu0 = classify_session("WU0")
    wu3 = classify_session("WU3")
    copy = classify_session("WU01Copy")
    wk = classify_session("WK01Copy")
    static_copy = classify_session("staticCopy")
    assert wu0["is_walking"] is True and wu0["is_irregular_name"] is True
    assert wu3["is_walking"] is True and wu3["is_irregular_name"] is True
    assert copy["is_walking"] is True and copy["is_irregular_name"] is True
    assert wk["session_type"] == "wk_copy" and wk["is_walking"] is False
    assert static_copy["session_type"] == "static" and static_copy["is_irregular_name"] is True
    # names are classified, never rewritten
    assert classify_session("WU01Copy")["name_pattern"] == "WU*Copy"
