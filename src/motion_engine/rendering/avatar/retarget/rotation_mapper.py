"""Rotation mapping — quaternion local/world, pre/post, bind offsets."""

from __future__ import annotations

from motion_engine.rendering.avatar.retarget._quat import q_mul, q_normalize
from motion_engine.rendering.avatar.retarget.constants import QUAT_IDENTITY
from motion_engine.rendering.avatar.retarget.coordinate_mapper import CoordinateMapper
from motion_engine.rendering.avatar.retarget.types import Quat


class RotationMapper:
    """Map source rotations into target skeleton space (quaternions only)."""

    def __init__(
        self,
        coords: CoordinateMapper | None = None,
        *,
        pre: Quat = QUAT_IDENTITY,
        post: Quat = QUAT_IDENTITY,
    ) -> None:
        self.coords = coords
        self.pre = q_normalize(pre)
        self.post = q_normalize(post)

    def map_local(
        self,
        source_local: Quat,
        *,
        pre: Quat | None = None,
        post: Quat | None = None,
        bind_offset: Quat = QUAT_IDENTITY,
    ) -> Quat:
        """Apply coordinate change + pre/post + bind offset to a local quat."""
        q = q_normalize(source_local)
        if self.coords is not None:
            q = self.coords.map_quat(q)
        pre_q = q_normalize(pre) if pre is not None else self.pre
        post_q = q_normalize(post) if post is not None else self.post
        # out = post * bind_offset * pre * q
        q = q_mul(pre_q, q)
        q = q_mul(bind_offset, q)
        q = q_mul(post_q, q)
        return q_normalize(q)

    def world_to_local(self, world: Quat, parent_world: Quat) -> Quat:
        from motion_engine.rendering.avatar.retarget._quat import q_conjugate

        return q_normalize(q_mul(q_conjugate(parent_world), world))

    def local_to_world(self, local: Quat, parent_world: Quat) -> Quat:
        return q_normalize(q_mul(parent_world, local))

    def relative_to_bind(self, animated: Quat, bind_local: Quat) -> Quat:
        """Delta rotation: bind^{-1} * animated (applied as bind * delta)."""
        from motion_engine.rendering.avatar.retarget._quat import q_conjugate

        return q_normalize(q_mul(q_conjugate(bind_local), animated))

    def apply_delta(self, bind_local: Quat, delta: Quat) -> Quat:
        return q_normalize(q_mul(bind_local, delta))


__all__ = ["RotationMapper"]
