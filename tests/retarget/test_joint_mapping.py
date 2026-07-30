from __future__ import annotations

from motion_engine.rendering.avatar.retarget.joint_mapping import JointMapping
from motion_engine.rendering.avatar.retarget.mapping_factory import MappingFactory
from motion_engine.rendering.avatar.retarget.types import MappingKind


def test_joint_mapping_primary():
    p = MappingFactory().builtin("matlab_clinical_to_army_girl")
    jm = JointMapping(p)
    assert jm.primary("Pelvis") == "pelvis"
    assert jm.primary("LHip") == "thigh_l"
    assert "spine_01" in jm.map_name("Thorax")


def test_one_to_many_expand():
    p = MappingFactory().builtin("matlab_clinical_to_army_girl")
    jm = JointMapping(p)
    entry = jm.bones.get("Thorax")
    assert entry is not None
    assert entry.kind == MappingKind.ONE_TO_MANY
    expanded = jm.expand_one_to_many("Thorax")
    assert len(expanded) >= 1
