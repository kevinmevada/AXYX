"""Anatomy metadata for Phase 2 features. No group labels."""

from __future__ import annotations

SIGNAL_ANATOMY: dict[str, dict[str, str]] = {
    "LASI": {"region": "pelvis", "side": "left", "related": "LASI", "unit": "mm"},
    "RASI": {"region": "pelvis", "side": "right", "related": "RASI", "unit": "mm"},
    "LPSI": {"region": "pelvis", "side": "left", "related": "LPSI", "unit": "mm"},
    "RPSI": {"region": "pelvis", "side": "right", "related": "RPSI", "unit": "mm"},
    "LHJC": {"region": "hip", "side": "left", "related": "LHJC", "unit": "mm"},
    "RHJC": {"region": "hip", "side": "right", "related": "RHJC", "unit": "mm"},
    "LHipAngles": {"region": "hip", "side": "left", "related": "LHJC", "unit": "deg"},
    "RHipAngles": {"region": "hip", "side": "right", "related": "RHJC", "unit": "deg"},
    "LKJC": {"region": "knee", "side": "left", "related": "LKJC", "unit": "mm"},
    "RKJC": {"region": "knee", "side": "right", "related": "RKJC", "unit": "mm"},
    "LKneeAngles": {"region": "knee", "side": "left", "related": "LKJC", "unit": "deg"},
    "RKneeAngles": {"region": "knee", "side": "right", "related": "RKJC", "unit": "deg"},
    "LAJC": {"region": "ankle", "side": "left", "related": "LAJC", "unit": "mm"},
    "RAJC": {"region": "ankle", "side": "right", "related": "RAJC", "unit": "mm"},
    "LAnkleAngles": {"region": "ankle", "side": "left", "related": "LAJC", "unit": "deg"},
    "RAnkleAngles": {"region": "ankle", "side": "right", "related": "RAJC", "unit": "deg"},
    "LAbsAnkleAngle": {"region": "ankle", "side": "left", "related": "LAJC", "unit": "deg"},
    "RAbsAnkleAngle": {"region": "ankle", "side": "right", "related": "RAJC", "unit": "deg"},
    "LHEE": {"region": "foot", "side": "left", "related": "LHEE", "unit": "mm"},
    "RHEE": {"region": "foot", "side": "right", "related": "RHEE", "unit": "mm"},
    "LTOE": {"region": "foot", "side": "left", "related": "LTOE", "unit": "mm"},
    "RTOE": {"region": "foot", "side": "right", "related": "RTOE", "unit": "mm"},
    "LFootProgressAngles": {"region": "foot", "side": "left", "related": "LTOE", "unit": "deg"},
    "RFootProgressAngles": {"region": "foot", "side": "right", "related": "RTOE", "unit": "deg"},
    "CentreOfMass": {"region": "whole_body", "side": "none", "related": "CentreOfMass", "unit": "mm"},
    "CentreOfMassFloor": {"region": "whole_body", "side": "none", "related": "CentreOfMassFloor", "unit": "mm"},
}

ANGLE_SIGNALS = (
    "LHipAngles",
    "RHipAngles",
    "LKneeAngles",
    "RKneeAngles",
    "LAnkleAngles",
    "RAnkleAngles",
    "LAbsAnkleAngle",
    "RAbsAnkleAngle",
    "LFootProgressAngles",
    "RFootProgressAngles",
)

SPATIAL_SIGNALS = (
    "LASI",
    "RASI",
    "LPSI",
    "RPSI",
    "LHJC",
    "RHJC",
    "LKJC",
    "RKJC",
    "LAJC",
    "RAJC",
    "LHEE",
    "RHEE",
    "LTOE",
    "RTOE",
    "CentreOfMass",
    "CentreOfMassFloor",
)

BILATERAL_PAIRS = (
    ("LHipAngles", "RHipAngles", "hip"),
    ("LKneeAngles", "RKneeAngles", "knee"),
    ("LAnkleAngles", "RAnkleAngles", "ankle"),
    ("LAbsAnkleAngle", "RAbsAnkleAngle", "ankle"),
    ("LFootProgressAngles", "RFootProgressAngles", "foot"),
    ("LHJC", "RHJC", "hip"),
    ("LKJC", "RKJC", "knee"),
    ("LAJC", "RAJC", "ankle"),
    ("LHEE", "RHEE", "foot"),
    ("LTOE", "RTOE", "foot"),
    ("LASI", "RASI", "pelvis"),
    ("LPSI", "RPSI", "pelvis"),
)

PHASE_ANGLE_SIGNALS = (
    "LHipAngles",
    "RHipAngles",
    "LKneeAngles",
    "RKneeAngles",
    "LAnkleAngles",
    "RAnkleAngles",
)

COORD_PAIRS = (
    ("LHipAngles", "LKneeAngles", "left_hip_knee"),
    ("LKneeAngles", "LAnkleAngles", "left_knee_ankle"),
    ("RHipAngles", "RKneeAngles", "right_hip_knee"),
    ("RKneeAngles", "RAnkleAngles", "right_knee_ankle"),
)


def meta(signal: str) -> dict[str, str]:
    return SIGNAL_ANATOMY.get(
        signal,
        {"region": "unknown", "side": "none", "related": signal, "unit": "unknown"},
    )
