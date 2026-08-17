"""Canonical Plug-in Gait signal catalogs for AXYS Phase 0.

Counts are part of the audit contract:
37 markers + 26 joint angles + 6 joint centers + 2 whole-body COM + 15 segment COM = 86.
"""

from __future__ import annotations

MARKERS: tuple[str, ...] = (
    "LFHD",
    "RFHD",
    "LBHD",
    "RBHD",
    "C7",
    "T10",
    "CLAV",
    "STRN",
    "RBAK",
    "LSHO",
    "LUPA",
    "LELB",
    "LFRM",
    "LWRA",
    "LWRB",
    "LFIN",
    "RSHO",
    "RUPA",
    "RELB",
    "RFRM",
    "RWRA",
    "RWRB",
    "RFIN",
    "LASI",
    "RASI",
    "LPSI",
    "RPSI",
    "LTHI",
    "LKNE",
    "LANK",
    "LHEE",
    "LTOE",
    "RTHI",
    "RKNE",
    "RANK",
    "RHEE",
    "RTOE",
)

JOINT_ANGLES: tuple[str, ...] = (
    "LHipAngles",
    "LKneeAngles",
    "LAbsAnkleAngle",
    "LAnkleAngles",
    "RHipAngles",
    "RKneeAngles",
    "RAnkleAngles",
    "RAbsAnkleAngle",
    "LPelvisAngles",
    "RPelvisAngles",
    "LFootProgressAngles",
    "RFootProgressAngles",
    "RNeckAngles",
    "LNeckAngles",
    "RSpineAngles",
    "LSpineAngles",
    "LShoulderAngles",
    "LElbowAngles",
    "LWristAngles",
    "RShoulderAngles",
    "RElbowAngles",
    "RWristAngles",
    "RThoraxAngles",
    "LThoraxAngles",
    "RHeadAngles",
    "LHeadAngles",
)

JOINT_CENTERS: tuple[str, ...] = (
    "LHJC",
    "RHJC",
    "LKJC",
    "RKJC",
    "LAJC",
    "RAJC",
)

WHOLE_BODY_COM: tuple[str, ...] = (
    "CentreOfMass",
    "CentreOfMassFloor",
)

SEGMENT_COM: tuple[str, ...] = (
    "PelvisCOM",
    "LeftFemurCOM",
    "LeftTibiaCOM",
    "LeftFootCOM",
    "RightFemurCOM",
    "RightTibiaCOM",
    "RightFootCOM",
    "ThoraxCOM",
    "HeadCOM",
    "LeftHumerusCOM",
    "LeftRadiusCOM",
    "LeftHandCOM",
    "RightHumerusCOM",
    "RightRadiusCOM",
    "RightHandCOM",
)

WALKING_KINEMATICS: tuple[str, ...] = (
    *MARKERS,
    *JOINT_ANGLES,
    *JOINT_CENTERS,
    *WHOLE_BODY_COM,
    *SEGMENT_COM,
)

STATIC_KINEMATICS: tuple[str, ...] = (
    *MARKERS,
    *JOINT_ANGLES,
)

EVENT_FIELDS: tuple[str, ...] = ("KinFC", "KinFO", "Midsvnt")
ANTHROPOMETRIC_FIELDS: tuple[str, ...] = ("Mass", "Height", "LLegLength", "RLegLength")

EXPECTED_SUBJECTS = 31
EXPECTED_VICTIMIZED = 17
EXPECTED_NON_VICTIMIZED = 14
EXPECTED_WALKING_TRIALS = 260
EXPECTED_SAMPLING_HZ = 100
EXPECTED_WALKING_SIGNAL_COUNT = 86
EXPECTED_MARKER_COUNT = 37
EXPECTED_JOINT_ANGLE_COUNT = 26
EXPECTED_JOINT_CENTER_COUNT = 6
EXPECTED_WHOLE_BODY_COM_COUNT = 2
EXPECTED_SEGMENT_COM_COUNT = 15

assert len(MARKERS) == EXPECTED_MARKER_COUNT
assert len(JOINT_ANGLES) == EXPECTED_JOINT_ANGLE_COUNT
assert len(JOINT_CENTERS) == EXPECTED_JOINT_CENTER_COUNT
assert len(WHOLE_BODY_COM) == EXPECTED_WHOLE_BODY_COM_COUNT
assert len(SEGMENT_COM) == EXPECTED_SEGMENT_COM_COUNT
assert len(WALKING_KINEMATICS) == EXPECTED_WALKING_SIGNAL_COUNT
assert len(STATIC_KINEMATICS) == EXPECTED_MARKER_COUNT + EXPECTED_JOINT_ANGLE_COUNT


# Empirically validated on all 260 walking trials (heel-Z at KinFC):
# code 1 = right contact, code 2 = left contact. Not assumed a priori.
SIDE_CODE_TO_FOOT: dict[int, str] = {1: "R", 2: "L"}

CORE_PELVIS: tuple[str, ...] = ("LASI", "RASI", "LPSI", "RPSI")
CORE_HIP: tuple[str, ...] = ("LHJC", "RHJC", "LHipAngles", "RHipAngles")
CORE_KNEE: tuple[str, ...] = ("LKJC", "RKJC", "LKneeAngles", "RKneeAngles")
CORE_ANKLE: tuple[str, ...] = (
    "LAJC",
    "RAJC",
    "LAnkleAngles",
    "RAnkleAngles",
    "LAbsAnkleAngle",
    "RAbsAnkleAngle",
)
CORE_FOOT: tuple[str, ...] = (
    "LHEE",
    "RHEE",
    "LTOE",
    "RTOE",
    "LFootProgressAngles",
    "RFootProgressAngles",
)
CORE_WHOLE_BODY: tuple[str, ...] = ("CentreOfMass", "CentreOfMassFloor")

CORE_GAIT_SIGNALS: tuple[str, ...] = (
    *CORE_PELVIS,
    *CORE_HIP,
    *CORE_KNEE,
    *CORE_ANKLE,
    *CORE_FOOT,
    *CORE_WHOLE_BODY,
)

DOMAIN_SIGNALS: dict[str, tuple[str, ...]] = {
    "pelvis": CORE_PELVIS,
    "hip": CORE_HIP,
    "knee": CORE_KNEE,
    "ankle": CORE_ANKLE,
    "foot": CORE_FOOT,
    "whole_body": CORE_WHOLE_BODY,
    "trunk": (
        "C7",
        "T10",
        "CLAV",
        "STRN",
        "RBAK",
        "LSpineAngles",
        "RSpineAngles",
        "LThoraxAngles",
        "RThoraxAngles",
    ),
    "head": (
        "LFHD",
        "RFHD",
        "LBHD",
        "RBHD",
        "LHeadAngles",
        "RHeadAngles",
        "LNeckAngles",
        "RNeckAngles",
    ),
    "arms": (
        "LSHO",
        "LUPA",
        "LELB",
        "LFRM",
        "LWRA",
        "LWRB",
        "LFIN",
        "RSHO",
        "RUPA",
        "RELB",
        "RFRM",
        "RWRA",
        "RWRB",
        "RFIN",
        "LShoulderAngles",
        "LElbowAngles",
        "LWristAngles",
        "RShoulderAngles",
        "RElbowAngles",
        "RWristAngles",
    ),
}

LOWER_BODY_DOMAINS: tuple[str, ...] = ("pelvis", "hip", "knee", "ankle", "foot", "whole_body")
UPPER_BODY_DOMAINS: tuple[str, ...] = ("trunk", "head", "arms")

NORMALIZED_POINTS = 101

DURATION_FAIL_MIN_S = 0.50
DURATION_FAIL_MAX_S = 2.20
DURATION_WARN_MIN_S = 0.70
DURATION_WARN_MAX_S = 1.60
LOWER_BODY_FINITE_FAIL = 0.90
LOWER_BODY_FINITE_WARN = 0.99


def classify_signal(name: str) -> str:
    if name in MARKERS:
        return "marker"
    if name in JOINT_ANGLES:
        return "joint_angle"
    if name in JOINT_CENTERS:
        return "joint_center"
    if name in WHOLE_BODY_COM:
        return "com"
    if name in SEGMENT_COM:
        return "segment_com"
    return "other"
