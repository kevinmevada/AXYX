"""Factory: procedural / JSON / GLTF / FBX → AnimationClip."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

import numpy as np

from motion_engine.rendering.avatar.animation.animation_clip import AnimationClip
from motion_engine.rendering.avatar.animation.animation_track import AnimationTrack
from motion_engine.rendering.avatar.animation.constants import DEFAULT_FPS
from motion_engine.rendering.avatar.animation.events import AnimationEvent
from motion_engine.rendering.avatar.animation.exceptions import AnimationFactoryError
from motion_engine.rendering.avatar.animation.keyframe import Keyframe
from motion_engine.rendering.avatar.animation.markers import AnimationMarker
from motion_engine.rendering.avatar.animation.quaternion import axis_angle_quat
from motion_engine.rendering.avatar.animation.serialization import import_clip
from motion_engine.rendering.avatar.animation.types import InterpolationMode, TrackChannel
from motion_engine.rendering.avatar.pose.bind_pose import BindPose
from motion_engine.rendering.avatar.pose.matrix_utils import decompose_trs


class AnimationFactory:
    """Construct validated animation clips from multiple sources."""

    def from_json(self, path: str | Path) -> AnimationClip:
        path = Path(path)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            raise AnimationFactoryError(
                f"Failed to read clip JSON: {path}: {exc}",
                code="ANIM_JSON",
            ) from exc
        clip = import_clip(data)
        clip.validate()
        return clip

    def from_dict(self, data: dict) -> AnimationClip:
        clip = import_clip(data)
        clip.validate()
        return clip

    def hold_pose(
        self,
        bind: BindPose,
        *,
        name: str = "idle",
        duration: float = 1.0,
        bones: Sequence[str] | None = None,
        fps: float = DEFAULT_FPS,
    ) -> AnimationClip:
        """Static hold of bind locals (Idle)."""
        names = list(bones) if bones is not None else [b.name for b in bind.bones]
        tracks: list[AnimationTrack] = []
        for nm in names:
            if not bind.exists(nm):
                continue
            t, q, s = decompose_trs(bind.find(nm).local_matrix)
            keys = (
                Keyframe(
                    time=0.0,
                    translation=(float(t[0]), float(t[1]), float(t[2])),
                    rotation_xyzw=(float(q[0]), float(q[1]), float(q[2]), float(q[3])),
                    scale=(float(s[0]), float(s[1]), float(s[2])),
                ),
                Keyframe(
                    time=float(duration),
                    translation=(float(t[0]), float(t[1]), float(t[2])),
                    rotation_xyzw=(float(q[0]), float(q[1]), float(q[2]), float(q[3])),
                    scale=(float(s[0]), float(s[1]), float(s[2])),
                ),
            )
            tracks.append(
                AnimationTrack(
                    bone_name=nm,
                    channel=TrackChannel.TRANSFORM,
                    keyframes=keys,
                    interpolation=InterpolationMode.LINEAR,
                )
            )
        if not tracks:
            raise AnimationFactoryError("hold_pose: no bones", code="ANIM_HOLD_EMPTY")
        return AnimationClip(
            name=name,
            duration=float(duration),
            tracks=tuple(tracks),
            markers=(AnimationMarker("LoopStart", 0.0), AnimationMarker("LoopEnd", float(duration))),
            events=(AnimationEvent("IdleTick", 0.0),),
            fps=fps,
            metadata={"source": "procedural_hold"},
        )

    def wave_clip(
        self,
        bind: BindPose,
        bone: str,
        *,
        name: str = "wave",
        duration: float = 2.0,
        axis: str = "z",
        amplitude_deg: float = 45.0,
        fps: float = DEFAULT_FPS,
        phase: float = 0.0,
    ) -> AnimationClip:
        """Procedural rotation wave on one bone."""
        track = self._wave_track(
            bind,
            bone,
            duration=duration,
            axis=axis,
            amplitude_deg=amplitude_deg,
            fps=fps,
            phase=phase,
        )
        return AnimationClip(
            name=name,
            duration=float(duration),
            tracks=(track,),
            markers=(
                AnimationMarker("LoopStart", 0.0),
                AnimationMarker("LoopEnd", float(duration)),
                AnimationMarker("FootContact", float(duration) * 0.5),
            ),
            events=(
                AnimationEvent("Footstep", float(duration) * 0.25, {"foot": "L"}),
                AnimationEvent("Footstep", float(duration) * 0.75, {"foot": "R"}),
            ),
            fps=fps,
            metadata={"source": "procedural_wave", "bone": bone, "axis": axis},
        )

    def _wave_track(
        self,
        bind: BindPose,
        bone: str,
        *,
        duration: float,
        axis: str,
        amplitude_deg: float,
        fps: float,
        phase: float = 0.0,
    ) -> AnimationTrack:
        if not bind.exists(bone):
            raise AnimationFactoryError(
                f"Bone {bone!r} missing from bind",
                code="ANIM_WAVE_BONE",
            )
        from motion_engine.rendering.avatar.pose.matrix_utils import matrix_to_quat, quat_to_matrix

        t0, q0, s0 = decompose_trs(bind.find(bone).local_matrix)
        ax = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}[axis.lower()]
        amp = np.deg2rad(float(amplitude_deg))
        keys: list[Keyframe] = []
        steps = max(4, int(duration * fps))
        for i in range(steps + 1):
            u = i / steps
            time = u * duration
            angle = amp * np.sin(2.0 * np.pi * u + float(phase))
            dq = axis_angle_quat(ax, angle)
            r0 = quat_to_matrix(q0)
            rd = quat_to_matrix(dq)
            q = matrix_to_quat(r0 @ rd)
            keys.append(
                Keyframe(
                    time=float(time),
                    translation=(float(t0[0]), float(t0[1]), float(t0[2])),
                    rotation_xyzw=(float(q[0]), float(q[1]), float(q[2]), float(q[3])),
                    scale=(float(s0[0]), float(s0[1]), float(s0[2])),
                )
            )
        return AnimationTrack(
            bone_name=bone,
            channel=TrackChannel.TRANSFORM,
            keyframes=tuple(keys),
            interpolation=InterpolationMode.LINEAR,
        )

    def body_locomotion_clip(
        self,
        bind: BindPose,
        *,
        name: str = "walk",
        duration: float = 1.2,
        intensity: float = 1.0,
        fps: float = DEFAULT_FPS,
    ) -> AnimationClip:
        """Whole-body procedural gait using **every** bone in the bind pose.

        Primary limbs get a strong walk cycle; twists / feet / hands / fingers /
        spine / neck follow with matched phase so skinning is fully driven.
        """
        primary: dict[str, tuple[str, float, float]] = {
            # bone -> (axis, amplitude_deg, phase)
            "pelvis": ("y", 5.0, 0.0),
            "spine_01": ("y", 6.0, 0.15),
            "spine_02": ("y", 5.0, 0.5 * np.pi),
            "spine_03": ("y", 4.0, np.pi),
            "neck_01": ("x", 4.0, np.pi),
            "head": ("y", 3.0, np.pi * 0.5),
            "clavicle_l": ("z", 6.0, np.pi),
            "clavicle_r": ("z", 6.0, 0.0),
            "upperarm_l": ("x", 24.0, np.pi),
            "upperarm_r": ("x", 24.0, 0.0),
            "lowerarm_l": ("x", 14.0, np.pi + 0.25),
            "lowerarm_r": ("x", 14.0, 0.25),
            "hand_l": ("x", 8.0, np.pi + 0.4),
            "hand_r": ("x", 8.0, 0.4),
            "thigh_l": ("x", 30.0, 0.0),
            "thigh_r": ("x", 30.0, np.pi),
            "calf_l": ("x", 20.0, 0.35),
            "calf_r": ("x", 20.0, np.pi + 0.35),
            "foot_l": ("x", 12.0, 0.55),
            "foot_r": ("x", 12.0, np.pi + 0.55),
            "ball_l": ("x", 8.0, 0.7),
            "ball_r": ("x", 8.0, np.pi + 0.7),
            "forearm": ("z", 30.0, 0.0),  # 2-bone fixture
        }

        def _side_phase(bone: str) -> float:
            if bone.endswith("_r") or "_r_" in bone:
                return np.pi
            return 0.0

        def _params_for(bone: str) -> tuple[str, float, float] | None:
            if bone in primary:
                axis, amp, phase = primary[bone]
                return axis, amp * intensity, phase
            # Twists follow their limb.
            if "thigh_twist" in bone:
                return "x", 10.0 * intensity, _side_phase(bone)
            if "calf_twist" in bone:
                return "x", 8.0 * intensity, _side_phase(bone) + 0.35
            if "upperarm_twist" in bone:
                return "x", 10.0 * intensity, _side_phase(bone) + np.pi
            if "lowerarm_twist" in bone:
                return "x", 8.0 * intensity, _side_phase(bone) + np.pi + 0.25
            # Fingers — light curl opposing that side's arm swing.
            for digit in ("thumb", "index", "middle", "ring", "pinky"):
                if bone.startswith(f"{digit}_"):
                    stage = 1
                    for part in bone.split("_"):
                        if part.isdigit():
                            stage = int(part)
                            break
                    return (
                        "x",
                        (6.0 + 2.0 * stage) * intensity * 0.45,
                        _side_phase(bone) + np.pi + 0.15 * stage,
                    )
            # Face — tiny idle bob so every bone is keyed (keeps skin weights alive).
            if bone.startswith(
                ("jaw", "lip_", "eye_", "eyebrow_", "eyelashes_")
            ) or bone in {"jaw"}:
                return "x", 1.5 * intensity, 0.0
            # Any leftover (neck extras, helpers, unnamed): gentle Y sway.
            if bone in {"root"} or bone.lower().startswith("root"):
                return None
            return "y", 2.5 * intensity, _side_phase(bone)

        tracks: list[AnimationTrack] = []
        covered: set[str] = set()
        for bone in bind.bones:
            params = _params_for(bone.name)
            if params is None:
                continue
            axis, amp, phase = params
            if abs(amp) < 1e-6:
                continue
            tracks.append(
                self._wave_track(
                    bind,
                    bone.name,
                    duration=duration,
                    axis=axis,
                    amplitude_deg=amp,
                    fps=fps,
                    phase=phase,
                )
            )
            covered.add(bone.name)

        if not tracks:
            raise AnimationFactoryError(
                "body_locomotion_clip: no animatable bones",
                code="ANIM_BODY_EMPTY",
            )
        return AnimationClip(
            name=name,
            duration=float(duration),
            tracks=tuple(tracks),
            markers=(
                AnimationMarker("LoopStart", 0.0),
                AnimationMarker("LoopEnd", float(duration)),
                AnimationMarker("FootContact", float(duration) * 0.5),
            ),
            events=(
                AnimationEvent("Footstep", float(duration) * 0.25, {"foot": "L"}),
                AnimationEvent("Footstep", float(duration) * 0.75, {"foot": "R"}),
            ),
            fps=fps,
            metadata={
                "source": "procedural_body_locomotion",
                "bones": [t.bone_name for t in tracks],
                "bone_count": len(tracks),
                "intensity": float(intensity),
            },
        )

    def jump_clip(
        self,
        bind: BindPose,
        *,
        name: str = "jump",
        duration: float = 0.9,
        fps: float = DEFAULT_FPS,
    ) -> AnimationClip:
        """Jump uses the full-body gait recipe at higher intensity + crouch bias."""
        # Reuse full-body coverage so every skinned bone moves.
        base = self.body_locomotion_clip(
            bind, name=name, duration=duration, intensity=1.35, fps=fps
        )
        return AnimationClip(
            name=name,
            duration=base.duration,
            tracks=base.tracks,
            markers=(
                AnimationMarker("LoopStart", 0.0),
                AnimationMarker("JumpApex", float(duration) * 0.5),
                AnimationMarker("LoopEnd", float(duration)),
            ),
            events=(
                AnimationEvent("Jump", 0.1),
                AnimationEvent("Land", float(duration) * 0.85),
            ),
            fps=fps,
            metadata={"source": "procedural_jump", "bones": list(base.bone_names)},
        )

    def locomotion_set(
        self,
        bind: BindPose,
        bone: str | None = None,
    ) -> dict[str, AnimationClip]:
        """Idle / Walk / Run / Jump — whole-body procedural set.

        ``bone`` is kept for API compatibility with older call sites; whole-body
        clips ignore it unless the rig is too small (then ``wave_clip`` is used).
        """
        _ = bone
        return {
            "idle": self.hold_pose(bind, name="idle", duration=1.0),
            "walk": self.body_locomotion_clip(
                bind, name="walk", duration=1.2, intensity=1.0
            ),
            "run": self.body_locomotion_clip(
                bind, name="run", duration=0.7, intensity=1.45
            ),
            "jump": self.jump_clip(bind, name="jump", duration=0.9),
        }

    def from_gltf(self, path: str | Path, *, animation_index: int = 0) -> AnimationClip:
        """Load a glTF / GLB animation (TRS channels → tracks)."""
        path = Path(path)
        try:
            from motion_engine.rendering.avatar.animation._gltf_anim import load_gltf_animation
        except ImportError as exc:  # pragma: no cover
            raise AnimationFactoryError(str(exc), code="ANIM_GLTF_IMPORT") from exc
        return load_gltf_animation(path, animation_index=animation_index)

    def from_fbx(self, path: str | Path, *, stack_index: int = 0) -> AnimationClip:
        """Bake an FBX anim stack into an AnimationClip (requires ``ufbx``)."""
        path = Path(path)
        try:
            from motion_engine.rendering.avatar.animation._fbx_anim import load_fbx_animation
        except ImportError as exc:  # pragma: no cover
            raise AnimationFactoryError(str(exc), code="ANIM_FBX_IMPORT") from exc
        return load_fbx_animation(path, stack_index=stack_index)


__all__ = ["AnimationFactory"]
