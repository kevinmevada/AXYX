"""Built-in mapping profiles + factory."""

from __future__ import annotations

from pathlib import Path

from motion_engine.rendering.avatar.retarget.constants import (
    PROFILE_IDENTITY,
    PROFILE_MATLAB_ARMY,
    PROFILE_MATLAB_METAHUMAN,
    PROFILE_MIXAMO,
    PROFILE_TEST_TWO_BONE,
)
from motion_engine.rendering.avatar.retarget.mapping import load_mapping, mapping_from_dict
from motion_engine.rendering.avatar.retarget.types import (
    AXYX_COORDS,
    BoneMapEntry,
    MappingKind,
    MappingProfile,
    Y_UP_RIGHT,
)

# Clinical Plug-in Gait → Unreal / MetaHuman-style names
_CLINICAL_TO_UNREAL: list[tuple[str, str]] = [
    ("Pelvis", "pelvis"),
    ("LHip", "thigh_l"),
    ("LKnee", "calf_l"),
    ("LAnkle", "foot_l"),
    ("LFoot", "ball_l"),
    ("RHip", "thigh_r"),
    ("RKnee", "calf_r"),
    ("RAnkle", "foot_r"),
    ("RFoot", "ball_r"),
    ("Thorax", "spine_01"),
    ("Neck", "neck_01"),
    ("Head", "head"),
    ("LShoulder", "upperarm_l"),
    ("LElbow", "lowerarm_l"),
    ("LWrist", "hand_l"),
    ("LHand", "hand_l"),
    ("RShoulder", "upperarm_r"),
    ("RElbow", "lowerarm_r"),
    ("RWrist", "hand_r"),
    ("RHand", "hand_r"),
]


def _pairs_to_profile(
    name: str,
    source: str,
    target: str,
    pairs: list[tuple[str, str]],
    *,
    optional_targets: set[str] | None = None,
) -> MappingProfile:
    optional_targets = optional_targets or set()
    bones: list[BoneMapEntry] = []
    for src, dst in pairs:
        bones.append(
            BoneMapEntry(
                source=src,
                targets=(dst,),
                kind=MappingKind.ONE_TO_ONE,
                optional=dst in optional_targets or src in {"LFoot", "RFoot", "LHand", "RHand"},
                copy_translation=(src == "Pelvis"),
            )
        )
    # One-to-many example: Thorax can also drive spine_02 if present
    bones.append(
        BoneMapEntry(
            source="Thorax",
            targets=("spine_01", "spine_02"),
            kind=MappingKind.ONE_TO_MANY,
            optional=True,
            weight=1.0,
        )
    )
    # Deduplicate: keep first Pelvis/Thorax one-to-one, replace Thorax with one-to-many only
    filtered: list[BoneMapEntry] = []
    seen_src: set[str] = set()
    for e in bones:
        if e.source == "Thorax" and e.kind == MappingKind.ONE_TO_ONE:
            continue
        if e.source in seen_src and e.kind != MappingKind.ONE_TO_MANY:
            continue
        if e.source in seen_src and e.kind == MappingKind.ONE_TO_MANY:
            # replace prior
            filtered = [x for x in filtered if x.source != e.source]
        seen_src.add(e.source)
        filtered.append(e)

    return MappingProfile(
        name=name,
        source_skeleton=source,
        target_skeleton=target,
        bones=tuple(filtered),
        root_source="Pelvis",
        root_target="pelvis",
        source_coords=AXYX_COORDS,
        target_coords=Y_UP_RIGHT,
        ignore_target=("ik_foot_root", "ik_hand_root", "root"),
        chains={
            "left_leg": ["Pelvis", "LHip", "LKnee", "LAnkle"],
            "right_leg": ["Pelvis", "RHip", "RKnee", "RAnkle"],
            "left_arm": ["Thorax", "LShoulder", "LElbow", "LWrist"],
            "right_arm": ["Thorax", "RShoulder", "RElbow", "RWrist"],
            "torso": ["Pelvis", "Thorax", "Neck", "Head"],
        },
        metadata={"builtin": True},
    )


def matlab_to_metahuman() -> MappingProfile:
    return _pairs_to_profile(
        PROFILE_MATLAB_METAHUMAN,
        "matlab_clinical",
        "metahuman",
        _CLINICAL_TO_UNREAL,
        optional_targets={"ball_l", "ball_r", "spine_02"},
    )


def matlab_to_army_girl() -> MappingProfile:
    return _pairs_to_profile(
        PROFILE_MATLAB_ARMY,
        "matlab_clinical",
        "army_girl",
        _CLINICAL_TO_UNREAL,
        optional_targets={"ball_l", "ball_r", "spine_02"},
    )


def mixamo_to_metahuman() -> MappingProfile:
    pairs = [
        ("Hips", "pelvis"),
        ("LeftUpLeg", "thigh_l"),
        ("LeftLeg", "calf_l"),
        ("LeftFoot", "foot_l"),
        ("RightUpLeg", "thigh_r"),
        ("RightLeg", "calf_r"),
        ("RightFoot", "foot_r"),
        ("Spine", "spine_01"),
        ("Spine1", "spine_02"),
        ("Spine2", "spine_03"),
        ("Neck", "neck_01"),
        ("Head", "head"),
        ("LeftArm", "upperarm_l"),
        ("LeftForeArm", "lowerarm_l"),
        ("LeftHand", "hand_l"),
        ("RightArm", "upperarm_r"),
        ("RightForeArm", "lowerarm_r"),
        ("RightHand", "hand_r"),
    ]
    bones = [
        BoneMapEntry(
            source=s,
            targets=(t,),
            optional=t in {"spine_02", "spine_03"},
            copy_translation=(s == "Hips"),
        )
        for s, t in pairs
    ]
    return MappingProfile(
        name=PROFILE_MIXAMO,
        source_skeleton="mixamo",
        target_skeleton="metahuman",
        bones=tuple(bones),
        root_source="Hips",
        root_target="pelvis",
        source_coords=Y_UP_RIGHT,
        target_coords=Y_UP_RIGHT,
        metadata={"builtin": True},
    )


def identity_profile(joint_names: list[str] | None = None) -> MappingProfile:
    names = joint_names or ["root", "forearm"]
    bones = [
        BoneMapEntry(source=n, targets=(n,), copy_translation=(i == 0))
        for i, n in enumerate(names)
    ]
    return MappingProfile(
        name=PROFILE_IDENTITY,
        source_skeleton="identity",
        target_skeleton="identity",
        bones=tuple(bones),
        root_source=names[0],
        root_target=names[0],
        source_coords=AXYX_COORDS,
        target_coords=AXYX_COORDS,
        metadata={"builtin": True},
    )


def test_two_bone_profile() -> MappingProfile:
    return MappingProfile(
        name=PROFILE_TEST_TWO_BONE,
        source_skeleton="motion_arm",
        target_skeleton="avatar_arm",
        bones=(
            BoneMapEntry(source="root", targets=("root",), copy_translation=True),
            BoneMapEntry(source="forearm", targets=("forearm",)),
        ),
        root_source="root",
        root_target="root",
        source_coords=AXYX_COORDS,
        target_coords=AXYX_COORDS,
        metadata={"builtin": True},
    )


class MappingFactory:
    """Construct mapping profiles from builtins, JSON, or dict."""

    BUILTINS = {
        PROFILE_MATLAB_METAHUMAN: matlab_to_metahuman,
        PROFILE_MATLAB_ARMY: matlab_to_army_girl,
        PROFILE_MIXAMO: mixamo_to_metahuman,
        PROFILE_IDENTITY: identity_profile,
        PROFILE_TEST_TWO_BONE: test_two_bone_profile,
    }

    def builtin(self, name: str) -> MappingProfile:
        if name not in self.BUILTINS:
            raise KeyError(f"Unknown builtin mapping: {name}")
        return self.BUILTINS[name]()

    def from_json(self, path: str | Path) -> MappingProfile:
        return load_mapping(path)

    def from_dict(self, data: dict) -> MappingProfile:
        return mapping_from_dict(data)

    def list_builtins(self) -> list[str]:
        return sorted(self.BUILTINS)


__all__ = [
    "MappingFactory",
    "matlab_to_metahuman",
    "matlab_to_army_girl",
    "mixamo_to_metahuman",
    "identity_profile",
    "test_two_bone_profile",
]
