"""Internal FBX animation bake via ``ufbx``."""

from __future__ import annotations

from pathlib import Path

from motion_engine.rendering.avatar.animation.animation_clip import AnimationClip
from motion_engine.rendering.avatar.animation.animation_track import AnimationTrack
from motion_engine.rendering.avatar.animation.exceptions import AnimationFactoryError
from motion_engine.rendering.avatar.animation.keyframe import Keyframe
from motion_engine.rendering.avatar.animation.types import InterpolationMode, TrackChannel


def load_fbx_animation(path: Path, *, stack_index: int = 0, fps: float = 30.0) -> AnimationClip:
    """Bake skinned-bone local transforms across an FBX anim stack.

    Only touches cluster ``bone_node`` handles (no full ``scene.nodes`` walk).
    """
    try:
        import ufbx
    except ImportError as exc:
        raise AnimationFactoryError(
            "FBX animation requires ufbx",
            code="ANIM_FBX_UFBX",
        ) from exc

    path = Path(path)
    if not path.is_file():
        raise AnimationFactoryError(f"FBX not found: {path}", code="ANIM_FBX_MISSING")

    scene = ufbx.load_file(str(path))
    if len(scene.anim_stacks) == 0:
        raise AnimationFactoryError(f"No anim stacks in {path}", code="ANIM_FBX_EMPTY")
    if stack_index < 0 or stack_index >= len(scene.anim_stacks):
        raise AnimationFactoryError("stack_index out of range", code="ANIM_FBX_INDEX")

    stack = scene.anim_stacks[stack_index]
    t0 = float(stack.time_begin)
    t1 = float(stack.time_end)
    duration = max(0.0, t1 - t0)
    if duration <= 1e-9:
        raise AnimationFactoryError("Zero-length FBX anim", code="ANIM_FBX_DURATION")

    bone_nodes: list[tuple[str, object]] = []
    for mi in range(len(scene.meshes)):
        mesh = scene.meshes[mi]
        if len(mesh.skin_deformers) == 0:
            continue
        skin = mesh.skin_deformers[0]
        for ci in range(len(skin.clusters)):
            node = skin.clusters[ci].bone_node
            if node is not None:
                bone_nodes.append((str(node.name), node))
        break
    if not bone_nodes:
        raise AnimationFactoryError("No skinned bones in FBX", code="ANIM_FBX_BONES")

    frames = max(2, int(round(duration * fps)) + 1)
    times = [t0 + (t1 - t0) * (i / (frames - 1)) for i in range(frames)]
    anim = stack.anim if hasattr(stack, "anim") else scene.anim

    tracks: list[AnimationTrack] = []
    for bone_name, node in bone_nodes:
        keys: list[Keyframe] = []
        ok = True
        for t in times:
            try:
                xf = ufbx.evaluate_transform(anim, node, float(t))
                tr, rot, sc = xf.translation, xf.rotation, xf.scale
                keys.append(
                    Keyframe(
                        time=float(t - t0),
                        translation=(float(tr.x), float(tr.y), float(tr.z)),
                        rotation_xyzw=(
                            float(rot.x),
                            float(rot.y),
                            float(rot.z),
                            float(rot.w),
                        ),
                        scale=(float(sc.x), float(sc.y), float(sc.z)),
                    )
                )
            except Exception:
                ok = False
                break
        if ok and len(keys) >= 2:
            tracks.append(
                AnimationTrack(
                    bone_name=bone_name,
                    channel=TrackChannel.TRANSFORM,
                    keyframes=tuple(keys),
                    interpolation=InterpolationMode.LINEAR,
                )
            )

    if not tracks:
        raise AnimationFactoryError(
            f"Could not bake FBX animation from {path.name}",
            code="ANIM_FBX_BAKE",
        )

    clip = AnimationClip(
        name=str(stack.name) or path.stem,
        duration=duration,
        tracks=tuple(tracks),
        fps=fps,
        metadata={"source": "fbx", "stack": str(stack.name)},
    )
    clip.validate()
    return clip
