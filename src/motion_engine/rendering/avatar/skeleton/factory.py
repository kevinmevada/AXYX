"""Factory: imported M1 skeleton → validated M2 runtime AvatarSkeleton."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from motion_engine.rendering.avatar.skeleton.avatar_skeleton import AvatarSkeleton
from motion_engine.rendering.avatar.skeleton.bone import Bone
from motion_engine.rendering.avatar.skeleton.constants import RUNTIME_VERSION
from motion_engine.rendering.avatar.skeleton.exceptions import SkeletonFactoryError
from motion_engine.rendering.avatar.skeleton.metadata import SkeletonMetadata
from motion_engine.rendering.avatar.skeleton.transforms import (
    Transform,
    identity_matrix,
    invert_affine,
)
from motion_engine.rendering.avatar.skeleton.types import (
    BoneFlag,
    CoordinateSystem,
    LengthUnit,
)

if TYPE_CHECKING:
    from motion_engine.rendering.avatar.models.avatar import LoadedAvatar
    from motion_engine.rendering.avatar.models.skeleton import (
        AvatarSkeleton as ImportedAvatarSkeleton,
    )
    from motion_engine.rendering.avatar.models.skeleton import BoneData


def _parse_coordinate_system(raw: str | None) -> CoordinateSystem:
    if not raw:
        return CoordinateSystem.UNKNOWN
    key = raw.strip().lower().replace("-", "_").replace(" ", "_")
    mapping = {
        "z_up": CoordinateSystem.Z_UP_RIGHT,
        "z_up_right": CoordinateSystem.Z_UP_RIGHT,
        "y_up": CoordinateSystem.Y_UP_RIGHT,
        "y_up_right": CoordinateSystem.Y_UP_RIGHT,
        "z_up_left": CoordinateSystem.Z_UP_LEFT,
        "y_up_left": CoordinateSystem.Y_UP_LEFT,
    }
    return mapping.get(key, CoordinateSystem.UNKNOWN)


def _parse_units(raw: str | None) -> LengthUnit:
    if not raw:
        return LengthUnit.UNKNOWN
    key = raw.strip().lower()
    mapping = {
        "m": LengthUnit.METERS,
        "meter": LengthUnit.METERS,
        "meters": LengthUnit.METERS,
        "cm": LengthUnit.CENTIMETERS,
        "centimeter": LengthUnit.CENTIMETERS,
        "centimeters": LengthUnit.CENTIMETERS,
        "mm": LengthUnit.MILLIMETERS,
        "millimeter": LengthUnit.MILLIMETERS,
        "millimeters": LengthUnit.MILLIMETERS,
    }
    return mapping.get(key, LengthUnit.UNKNOWN)


def _bone_from_imported(data: BoneData) -> Bone:
    """Convert a single M1 :class:`BoneData` into a runtime :class:`Bone`."""
    local = Transform.from_translation(data.local_translation)
    if data.bind_world is not None:
        world = np.asarray(data.bind_world, dtype=np.float64).reshape(4, 4).copy()
    else:
        # Fallback: local only (root-like); hierarchy FK fills later if needed.
        world = local.to_matrix()

    ibm = None
    flags = BoneFlag.NONE
    if data.inverse_bind is not None:
        ibm = np.asarray(data.inverse_bind, dtype=np.float64).reshape(4, 4).copy()
        flags |= BoneFlag.HAS_INVERSE_BIND
    else:
        try:
            ibm = invert_affine(world)
            flags |= BoneFlag.HAS_INVERSE_BIND
        except np.linalg.LinAlgError:
            ibm = identity_matrix()

    if data.parent_index is None:
        flags |= BoneFlag.ROOT

    if local.has_non_uniform_scale:
        flags |= BoneFlag.NON_UNIFORM_SCALE

    return Bone(
        index=int(data.index),
        name=str(data.name),
        parent_index=data.parent_index,
        children=(),
        local_transform=local,
        world_transform=world,
        rest_transform=local,
        inverse_bind=ibm,
        flags=flags,
        metadata={"source": "m1_bone_data"},
    )


class AvatarSkeletonFactory:
    """Convert imported (M1) skeletons into validated runtime skeletons.

    The M1 :class:`~motion_engine.rendering.avatar.models.skeleton.AvatarSkeleton`
    remains the immutable **import DTO**. This factory is the sole bridge to the
    M2 canonical runtime object. Asset pipeline loaders are not modified.
    """

    def __init__(
        self,
        *,
        validate: bool = True,
        require_inverse_bind: bool = False,
        allow_multiple_roots: bool = True,
        rebuild_world_from_local: bool = False,
    ) -> None:
        self.validate = validate
        self.require_inverse_bind = require_inverse_bind
        self.allow_multiple_roots = allow_multiple_roots
        self.rebuild_world_from_local = rebuild_world_from_local

    def from_imported(
        self,
        imported: ImportedAvatarSkeleton,
        *,
        coordinate_system: str | None = None,
        units: str | None = None,
        source_format: str = "m1_imported",
        source_asset_id: str = "",
        extra: dict[str, object] | None = None,
    ) -> AvatarSkeleton:
        """Build runtime skeleton from an M1 imported skeleton.

        Raises:
            SkeletonFactoryError: If the imported skeleton is empty or conversion fails.
        """
        if imported is None:  # type: ignore[redundant-expr]
            raise SkeletonFactoryError("Imported skeleton is None", code="SKEL_FACTORY_NULL")
        if not imported.bones:
            raise SkeletonFactoryError(
                "Imported skeleton has no bones",
                code="SKEL_FACTORY_EMPTY",
            )

        try:
            from motion_engine.rendering.avatar.skeleton.hierarchy import attach_children

            raw = [_bone_from_imported(b) for b in imported.bones]
            with_kids = attach_children(raw)
            bones: list[Bone] = []
            for b in with_kids:
                flags = b.flags
                if b.is_leaf:
                    flags |= BoneFlag.LEAF
                if b.is_root:
                    flags |= BoneFlag.ROOT
                if flags != b.flags:
                    bones.append(
                        Bone(
                            index=b.index,
                            name=b.name,
                            parent_index=b.parent_index,
                            children=b.children,
                            local_transform=b.local_transform,
                            world_transform=b.world_matrix,
                            rest_transform=b.rest_transform,
                            inverse_bind=b.inverse_bind,
                            bone_id=b.bone_id,
                            flags=flags,
                            metadata=b.metadata,
                            user_data=b.user_data,
                        )
                    )
                else:
                    bones.append(b)

            meta = SkeletonMetadata(
                coordinate_system=_parse_coordinate_system(coordinate_system),
                units=_parse_units(units),
                source_format=source_format,
                importer_version="m1",
                bone_count=len(bones),
                runtime_version=RUNTIME_VERSION,
                skeleton_name=imported.name,
                source_asset_id=source_asset_id,
                extra=extra or {},
            )
            skel = AvatarSkeleton.from_bones(
                bones,
                name=imported.name or "AvatarSkeleton",
                metadata=meta,
                validate=self.validate,
                require_inverse_bind=self.require_inverse_bind,
                allow_multiple_roots=self.allow_multiple_roots,
            )
            if self.rebuild_world_from_local:
                skel = skel.rebuild_world_rest()
            return skel
        except SkeletonFactoryError:
            raise
        except Exception as exc:  # noqa: BLE001 - wrap for domain clarity
            raise SkeletonFactoryError(
                f"Failed to convert imported skeleton: {exc}",
                code="SKEL_FACTORY_CONVERT",
                details={"error": str(exc)},
            ) from exc

    def from_loaded(self, loaded: LoadedAvatar) -> AvatarSkeleton:
        """Build runtime skeleton from a :class:`LoadedAvatar`.

        Raises:
            SkeletonFactoryError: If the avatar has no skeleton (e.g. procedural).
        """
        if loaded.skeleton is None:
            raise SkeletonFactoryError(
                f"LoadedAvatar {loaded.id!r} has no skeleton",
                code="SKEL_FACTORY_NO_SKELETON",
            )
        coord = None
        units = None
        manifest = loaded.manifest
        if hasattr(manifest, "coordinate_system"):
            coord = getattr(manifest, "coordinate_system", None)
        if hasattr(manifest, "units"):
            units = getattr(manifest, "units", None)
        # Manifest may store nested metadata
        meta_map = getattr(manifest, "metadata", None)
        if isinstance(meta_map, dict):
            coord = coord or meta_map.get("coordinate_system")
            units = units or meta_map.get("units")
        return self.from_imported(
            loaded.skeleton,
            coordinate_system=str(coord) if coord else None,
            units=str(units) if units else None,
            source_format="loaded_avatar",
            source_asset_id=str(loaded.id),
        )

    def from_bone_tables(
        self,
        *,
        names: list[str],
        parents: list[int | None],
        local_translations: list[tuple[float, float, float]] | None = None,
        bind_world: list[np.ndarray] | None = None,
        inverse_bind: list[np.ndarray | None] | None = None,
        name: str = "AvatarSkeleton",
    ) -> AvatarSkeleton:
        """Build a runtime skeleton from raw tables (tests / procedural bridges)."""
        n = len(names)
        if len(parents) != n:
            raise SkeletonFactoryError("parents length mismatch", code="SKEL_FACTORY_TABLE")
        locals_t = local_translations or [(0.0, 0.0, 0.0)] * n
        bones: list[Bone] = []
        for i in range(n):
            local = Transform.from_translation(locals_t[i])
            world = (
                np.asarray(bind_world[i], dtype=np.float64).reshape(4, 4)
                if bind_world is not None
                else local.to_matrix()
            )
            ibm = None
            if inverse_bind is not None:
                ibm = (
                    None
                    if inverse_bind[i] is None
                    else np.asarray(inverse_bind[i], dtype=np.float64).reshape(4, 4)
                )
            bones.append(
                Bone(
                    index=i,
                    name=names[i],
                    parent_index=parents[i],
                    local_transform=local,
                    world_transform=world,
                    rest_transform=local,
                    inverse_bind=ibm,
                    flags=BoneFlag.ROOT if parents[i] is None else BoneFlag.NONE,
                )
            )
        return AvatarSkeleton.from_bones(
            bones,
            name=name,
            metadata=SkeletonMetadata(
                source_format="bone_tables",
                skeleton_name=name,
                bone_count=n,
            ),
            validate=self.validate,
            require_inverse_bind=self.require_inverse_bind,
            allow_multiple_roots=self.allow_multiple_roots,
        )


__all__ = ["AvatarSkeletonFactory"]
