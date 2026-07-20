"""Factory conversion tests."""

from __future__ import annotations

import numpy as np
import pytest

from motion_engine.rendering.avatar.models.skeleton import AvatarSkeleton as ImportedSkeleton
from motion_engine.rendering.avatar.models.skeleton import BoneData
from motion_engine.rendering.avatar.skeleton import AvatarSkeletonFactory, SkeletonFactoryError
from tests.skeleton.helpers import make_chain_imported, make_tree_imported


def test_from_imported_chain(factory) -> None:
    sk = factory.from_imported(make_chain_imported(3))
    assert sk.bone_count == 3
    assert sk.name == "chain"
    assert sk.metadata.source_format == "m1_imported"
    assert sk.find("b2").parent_index == 1


def test_from_imported_preserves_ibm(factory) -> None:
    eye = np.eye(4)
    ibm = np.diag([2.0, 2.0, 2.0, 1.0])
    imp = ImportedSkeleton(
        name="x",
        bones=(BoneData(0, "r", None, (0, 0, 0), eye, ibm),),
    )
    sk = factory.from_imported(imp)
    assert sk.bones[0].inverse_bind is not None
    assert np.allclose(sk.bones[0].inverse_bind, ibm)


def test_from_bone_tables(factory) -> None:
    sk = factory.from_bone_tables(
        names=["root", "child"],
        parents=[None, 0],
        local_translations=[(0, 0, 0), (1, 0, 0)],
    )
    assert sk.path("child") == "root/child"


def test_empty_imported_raises(factory) -> None:
    with pytest.raises(SkeletonFactoryError):
        factory.from_imported(ImportedSkeleton(name="e", bones=()))


def test_rebuild_world_option() -> None:
    fac = AvatarSkeletonFactory(rebuild_world_from_local=True)
    sk = fac.from_imported(make_tree_imported())
    assert sk.bone_count == 4


def test_children_attached(factory) -> None:
    sk = factory.from_imported(make_tree_imported())
    assert sk.find("root").children == (1, 2)
    assert sk.find("right").children == (3,)
