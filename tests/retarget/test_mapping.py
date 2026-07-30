from __future__ import annotations

from motion_engine.rendering.avatar.retarget.bone_mapping import BoneMapping
from motion_engine.rendering.avatar.retarget.mapping import mapping_from_dict, mapping_to_dict
from motion_engine.rendering.avatar.retarget.mapping_factory import MappingFactory


def test_builtin_profiles():
    f = MappingFactory()
    for name in f.list_builtins():
        p = f.builtin(name)
        assert p.name
        assert p.bones


def test_mapping_roundtrip_dict():
    p = MappingFactory().builtin("matlab_clinical_to_army_girl")
    d = mapping_to_dict(p)
    p2 = mapping_from_dict(d)
    assert p2.name == p.name
    assert len(p2.bones) == len(p.bones)
    assert p2.root_source == p.root_source


def test_bone_mapping_resolve():
    p = MappingFactory().builtin("test_two_bone")
    bm = BoneMapping(p)
    active, miss_s, miss_t = bm.resolve({"root", "forearm"}, {"root", "forearm"})
    assert len(active) == 2
    assert not miss_s
    assert not miss_t
