"""
Camera controller for the Visualization Engine.

Owns **all** camera mathematics:

* Presets - Front / Back / Side / Reset
* Bounding-box framing
* Interruptible ~400 ms transitions
* Constrained orbit / pan / zoom

``viewer.py`` only forwards UI events.
``renderer.py`` only applies a :class:`CameraState` snapshot.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Sequence

import numpy as np
from numpy.typing import NDArray

Vec3 = tuple[float, float, float]
FloatArray = NDArray[np.floating]

DEFAULT_FOV_DEG: float = 16.1
"""Vertical FOV for an 85 mm lens on a full-frame sensor (24 mm tall)."""

LENS_FOCAL_MM: float = 85.0
LOOK_AT_HEIGHT_RATIO: float = 0.48
"""Framing anchor — lower on the body so the horizon sits in the lower third."""

EYE_HEIGHT_RATIO: float = 0.66
"""Camera height above the floor plane."""

CAMERA_YAW_BIAS_DEG: float = 12.0
"""Default 12° orbit offset — subtle asymmetry, not dead-center."""

FIT_MARGIN: float = 0.74
"""Tighter framing — subject fills ~65% of the viewport height."""

BREATH_SPEED: float = 0.32
BREATH_AMPLITUDE_FACTOR: float = 0.0022
DEFAULT_ANIMATION_SECONDS: float = 0.42
MIN_ANIMATION_SECONDS: float = 0.32
MAX_ANIMATION_SECONDS: float = 0.55
FIT_DISTANCE_FACTOR: float = 2.65
SIDE_DISTANCE_FACTOR: float = 2.75
MIN_DISTANCE_RADIUS_FACTOR: float = 0.45
MAX_DISTANCE_RADIUS_FACTOR: float = 35.0
ORBIT_SENSITIVITY: float = 0.0042
PAN_SENSITIVITY: float = 0.00085
ZOOM_SENSITIVITY: float = 0.0014
# Clinical orbit: never roll, never go under the floor, never flip upside-down.
MAX_POLAR_ANGLE: float = math.radians(82.0)
MIN_POLAR_ANGLE: float = math.radians(8.0)
FLOOR_CLEARANCE_FACTOR: float = 0.04
WORLD_UP: Vec3 = (0.0, 0.0, 1.0)
ORBIT_VIEW_COUNT: int = 4
ORBIT_AZIMUTH_STEP: float = 2.0 * math.pi / ORBIT_VIEW_COUNT
ORBIT_ELEVATION_FACTOR: float = 0.055
ORBIT_VIEW_NAMES: tuple[str, ...] = ("Front", "Right", "Back", "Left")


class CameraProjection(str, Enum):
    """Camera projection mode."""

    PERSPECTIVE = "perspective"
    ORTHOGRAPHIC = "orthographic"


class CameraPreset(str, Enum):
    """Four orbital views (90° apart) plus reset."""

    ORBIT_0 = "orbit_0"
    ORBIT_1 = "orbit_1"
    ORBIT_2 = "orbit_2"
    ORBIT_3 = "orbit_3"
    RESET = "reset"


@dataclass(slots=True)
class BoundingBox:
    """Axis-aligned model bounds used for framing."""

    min_corner: Vec3 = (0.0, 0.0, 0.0)
    max_corner: Vec3 = (1.0, 1.0, 1.0)

    @classmethod
    def from_points(cls, points: Sequence[Sequence[float]]) -> BoundingBox:
        """Build a bounding box from XYZ samples."""
        arr = np.asarray(points, dtype=float)
        if arr.size == 0:
            return cls()
        if arr.ndim == 1:
            arr = arr.reshape(1, 3)
        mins = arr.min(axis=0)
        maxs = arr.max(axis=0)
        return cls(
            min_corner=(float(mins[0]), float(mins[1]), float(mins[2])),
            max_corner=(float(maxs[0]), float(maxs[1]), float(maxs[2])),
        )

    @property
    def center(self) -> Vec3:
        c = 0.5 * (
            np.asarray(self.min_corner, dtype=float)
            + np.asarray(self.max_corner, dtype=float)
        )
        return (float(c[0]), float(c[1]), float(c[2]))

    @property
    def extents(self) -> Vec3:
        e = np.asarray(self.max_corner, dtype=float) - np.asarray(
            self.min_corner, dtype=float
        )
        return (float(e[0]), float(e[1]), float(e[2]))

    @property
    def radius(self) -> float:
        e = np.asarray(self.extents, dtype=float)
        return float(max(0.5 * np.linalg.norm(e), 1.0))


@dataclass(slots=True)
class CameraState:
    """Renderer-neutral camera pose snapshot."""

    eye: Vec3 = (1500.0, -1800.0, 1100.0)
    look_at: Vec3 = (0.0, 0.0, 900.0)
    up: Vec3 = WORLD_UP
    fov_deg: float = DEFAULT_FOV_DEG
    near: float = 1.0
    far: float = 1.0e6
    projection: CameraProjection = CameraProjection.PERSPECTIVE
    view_name: str = "Front"
    orbit_enabled: bool = True
    pan_enabled: bool = True
    zoom_enabled: bool = True

    def copy(self) -> CameraState:
        return replace(self)

    @property
    def distance(self) -> float:
        return float(
            np.linalg.norm(
                np.asarray(self.eye, dtype=float) - np.asarray(self.look_at, dtype=float)
            )
        )

    @property
    def forward(self) -> Vec3:
        eye = np.asarray(self.eye, dtype=float)
        look = np.asarray(self.look_at, dtype=float)
        delta = look - eye
        norm = float(np.linalg.norm(delta))
        if norm < 1e-12:
            return (0.0, 1.0, 0.0)
        delta = delta / norm
        return (float(delta[0]), float(delta[1]), float(delta[2]))


@dataclass(slots=True)
class _CameraAnimation:
    start: CameraState
    end: CameraState
    duration: float
    t0: float
    active: bool = True

    def sample(self, now: float) -> tuple[CameraState, bool]:
        if not self.active or self.duration <= 0.0:
            return self.end.copy(), True
        u = (now - self.t0) / self.duration
        if u >= 1.0:
            return self.end.copy(), True
        u = max(0.0, min(u, 1.0))
        s = u * u * (3.0 - 2.0 * u)
        return _lerp_state(self.start, self.end, s), False


def _as_vec3(value: Sequence[float]) -> Vec3:
    return (float(value[0]), float(value[1]), float(value[2]))


def _normalize(v: Sequence[float]) -> Vec3:
    arr = np.asarray(v, dtype=float)
    n = float(np.linalg.norm(arr))
    if n < 1e-12:
        return (0.0, 0.0, 1.0)
    arr = arr / n
    return (float(arr[0]), float(arr[1]), float(arr[2]))


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _lerp_vec(a: Sequence[float], b: Sequence[float], t: float) -> Vec3:
    return (
        _lerp(float(a[0]), float(b[0]), t),
        _lerp(float(a[1]), float(b[1]), t),
        _lerp(float(a[2]), float(b[2]), t),
    )


def _slerp_dir(a: Sequence[float], b: Sequence[float], t: float) -> Vec3:
    aa = np.asarray(_normalize(a), dtype=float)
    bb = np.asarray(_normalize(b), dtype=float)
    dot = float(np.clip(np.dot(aa, bb), -1.0, 1.0))
    if dot > 0.9995:
        return _normalize(_lerp_vec(aa, bb, t))
    omega = math.acos(dot)
    so = math.sin(omega)
    out = (math.sin((1.0 - t) * omega) / so) * aa + (math.sin(t * omega) / so) * bb
    return _normalize(out)


def _orthogonalize_up(forward: Sequence[float], up: Sequence[float]) -> Vec3:
    f = np.asarray(_normalize(forward), dtype=float)
    u = np.asarray(_normalize(up), dtype=float)
    if abs(float(np.dot(f, u))) > 0.98:
        u = np.asarray(WORLD_UP if abs(f[2]) < 0.9 else (0.0, 1.0, 0.0), dtype=float)
    right = np.cross(f, u)
    rn = float(np.linalg.norm(right))
    if rn < 1e-12:
        right = np.array([1.0, 0.0, 0.0], dtype=float)
    else:
        right = right / rn
    return _normalize(np.cross(right, f))


def _lerp_state(a: CameraState, b: CameraState, t: float) -> CameraState:
    look = _lerp_vec(a.look_at, b.look_at, t)
    a_off = np.asarray(a.eye, dtype=float) - np.asarray(a.look_at, dtype=float)
    b_off = np.asarray(b.eye, dtype=float) - np.asarray(b.look_at, dtype=float)
    a_dist = float(max(np.linalg.norm(a_off), 1e-6))
    b_dist = float(max(np.linalg.norm(b_off), 1e-6))
    direction = _slerp_dir(a_off / a_dist, b_off / b_dist, t)
    dist = _lerp(a_dist, b_dist, t)
    eye = (
        look[0] + direction[0] * dist,
        look[1] + direction[1] * dist,
        look[2] + direction[2] * dist,
    )
    up = _normalize(a.up if t < 0.5 else b.up)
    return CameraState(
        eye=eye,
        look_at=look,
        up=up,
        fov_deg=_lerp(a.fov_deg, b.fov_deg, t),
        near=_lerp(a.near, b.near, t),
        far=_lerp(a.far, b.far, t),
        projection=b.projection if t >= 0.5 else a.projection,
        view_name=b.view_name if t >= 0.5 else a.view_name,
    )


@dataclass
class CameraController:
    """Professional camera controller for scientific visualization."""

    state: CameraState = field(default_factory=CameraState)
    bounds: BoundingBox = field(default_factory=BoundingBox)
    animation_seconds: float = DEFAULT_ANIMATION_SECONDS
    _animation: _CameraAnimation | None = field(default=None, init=False, repr=False)
    _dirty: bool = field(default=True, init=False, repr=False)
    _min_distance: float = field(default=50.0, init=False, repr=False)
    _max_distance: float = field(default=50000.0, init=False, repr=False)
    _orbit_index: int = field(default=0, init=False, repr=False)
    _breath_phase: float = field(default=0.0, init=False, repr=False)

    def __post_init__(self) -> None:
        self.animation_seconds = float(
            np.clip(
                self.animation_seconds, MIN_ANIMATION_SECONDS, MAX_ANIMATION_SECONDS
            )
        )
        self._refresh_distance_limits()

    def set_model_bounds(self, bounds: BoundingBox) -> None:
        self.bounds = bounds
        self._refresh_distance_limits()

    def set_model_points(self, points: Sequence[Sequence[float]]) -> None:
        self.set_model_bounds(BoundingBox.from_points(points))

    def get_state(self) -> CameraState:
        return self._apply_breathing(self.state.copy())

    def set_state(self, state: CameraState, *, animate: bool = False) -> None:
        target = self._clamp_state_distance(state.copy())
        target.up = _orthogonalize_up(target.forward, target.up)
        if animate:
            self.animate_to(target)
        else:
            self._cancel_animation()
            self.state = target
            self._dirty = True

    def is_dirty(self) -> bool:
        return self._dirty or self.is_animating()

    def clear_dirty(self) -> None:
        if not self.is_animating():
            self._dirty = False

    def is_animating(self) -> bool:
        return self._animation is not None and self._animation.active

    def update(self, dt: float | None = None) -> CameraState:
        if dt is not None and dt > 0.0 and not self.is_animating():
            self._breath_phase += dt * BREATH_SPEED
        if self._animation is None or not self._animation.active:
            return self.state
        sample, finished = self._animation.sample(time.perf_counter())
        self.state = sample
        self._dirty = True
        if finished:
            self.state = self._clamp_state_distance(self._animation.end.copy())
            self._animation = None
        return self.state

    def animate_to(
        self, target: CameraState, *, duration: float | None = None
    ) -> None:
        duration = float(
            np.clip(
                duration if duration is not None else self.animation_seconds,
                MIN_ANIMATION_SECONDS,
                MAX_ANIMATION_SECONDS,
            )
        )
        end = self._clamp_state_distance(target.copy())
        end.up = _orthogonalize_up(end.forward, end.up)
        self._animation = _CameraAnimation(
            start=self.state.copy(),
            end=end,
            duration=duration,
            t0=time.perf_counter(),
            active=True,
        )
        self._dirty = True

    def front(self, *, animate: bool = True) -> None:
        """Snap to the front orbital view (orbit index 0)."""
        self._orbit_index = 0
        self._go_to_orbit_index(animate=animate)

    def back(self, *, animate: bool = True) -> None:
        """Snap to the back orbital view (orbit index 2)."""
        self._orbit_index = 2
        self._go_to_orbit_index(animate=animate)

    def side(self, *, animate: bool = True) -> None:
        """Snap to the right-side orbital view (orbit index 1)."""
        self._orbit_index = 1
        self._go_to_orbit_index(animate=animate)

    def left(self, *, animate: bool = True) -> None:
        """Snap to the left-side orbital view (orbit index 3)."""
        self._orbit_index = 3
        self._go_to_orbit_index(animate=animate)

    def right(self, *, animate: bool = True) -> None:
        """Snap to the right-side orbital view (orbit index 1)."""
        self.side(animate=animate)

    def rotate_left(self, *, animate: bool = True) -> None:
        """Step counter-clockwise to the next 90° orbital view."""
        self._orbit_index = (self._orbit_index + 1) % ORBIT_VIEW_COUNT
        self._go_to_orbit_index(animate=animate)

    def rotate_right(self, *, animate: bool = True) -> None:
        """Step clockwise to the previous 90° orbital view."""
        self._orbit_index = (self._orbit_index - 1) % ORBIT_VIEW_COUNT
        self._go_to_orbit_index(animate=animate)

    def reset(self, *, animate: bool = True) -> None:
        """Default production framing: front view, full-body fit."""
        self._orbit_index = 0
        self._go_to_orbit_index(animate=animate)

    def focus_subject(self, *, animate: bool = True) -> None:
        """Recenter on the subject and fit the current view direction."""
        self.fit(animate=animate)

    @property
    def orbit_index(self) -> int:
        """Current orbital view index in ``[0, ORBIT_VIEW_COUNT)``."""
        return self._orbit_index

    def fit(self, *, animate: bool = True) -> None:
        """Re-frame the full subject using the current view direction."""
        direction = _normalize(
            np.asarray(self.state.eye) - np.asarray(self.state.look_at)
        )
        target = self._framed_pose(
            direction=direction,
            view_name=self.state.view_name,
        )
        if animate:
            self.animate_to(target)
        else:
            self.set_state(target, animate=False)

    def set_preset(
        self,
        preset: CameraPreset | str,
        *,
        animate: bool = True,
    ) -> None:
        if isinstance(preset, str):
            preset = CameraPreset(preset)
        if preset == CameraPreset.RESET:
            self.reset(animate=animate)
            return
        if preset in {
            CameraPreset.ORBIT_0,
            CameraPreset.ORBIT_1,
            CameraPreset.ORBIT_2,
            CameraPreset.ORBIT_3,
        }:
            self._orbit_index = int(preset.value.rsplit("_", maxsplit=1)[-1])
            self._go_to_orbit_index(animate=animate)
            return
        raise ValueError(f"Unknown camera preset: {preset!r}")

    def orbit(self, dx_pixels: float, dy_pixels: float) -> None:
        if not self.state.orbit_enabled:
            return
        self._cancel_animation()
        # Always orbit around the subject center - keeps the figure centered.
        look = np.asarray(self.bounds.center, dtype=float)
        eye = np.asarray(self.state.eye, dtype=float)
        offset = eye - look
        radius = float(np.linalg.norm(offset))
        if radius < 1e-9:
            return
        x, y, z = offset
        theta = math.atan2(y, x)
        phi = math.acos(float(np.clip(z / radius, -1.0, 1.0)))
        theta -= dx_pixels * ORBIT_SENSITIVITY
        phi = float(
            np.clip(
                phi - dy_pixels * ORBIT_SENSITIVITY, MIN_POLAR_ANGLE, MAX_POLAR_ANGLE
            )
        )
        new_offset = np.array(
            [
                radius * math.sin(phi) * math.cos(theta),
                radius * math.sin(phi) * math.sin(theta),
                radius * math.cos(phi),
            ],
            dtype=float,
        )
        eye_new = look + new_offset
        self.state.look_at = _as_vec3(look)
        self.state.eye = _as_vec3(eye_new)
        self.state.up = WORLD_UP  # lock roll
        self.state = self._clamp_state_distance(self.state)
        self.state.view_name = "Free"
        self._dirty = True

    def pan(self, dx_pixels: float, dy_pixels: float) -> None:
        if not self.state.pan_enabled:
            return
        self._cancel_animation()
        eye = np.asarray(self.state.eye, dtype=float)
        look = np.asarray(self.state.look_at, dtype=float)
        forward = look - eye
        fn = float(np.linalg.norm(forward))
        if fn < 1e-9:
            return
        forward = forward / fn
        up = np.asarray(WORLD_UP, dtype=float)
        right = np.cross(forward, up)
        rn = float(np.linalg.norm(right))
        if rn < 1e-12:
            return
        right = right / rn
        # Screen-space pan: keep world-up locked (no roll).
        screen_up = np.cross(right, forward)
        sn = float(np.linalg.norm(screen_up))
        if sn > 1e-12:
            screen_up = screen_up / sn
        scale = self.state.distance * PAN_SENSITIVITY
        delta = (-dx_pixels * right + dy_pixels * screen_up) * scale
        # Soft leash - never lose the subject.
        center = np.asarray(self.bounds.center, dtype=float)
        new_look = look + delta
        leash = self.bounds.radius * 1.35
        to_center = new_look - center
        dist_c = float(np.linalg.norm(to_center))
        if dist_c > leash:
            new_look = center + to_center * (leash / dist_c)
            delta = new_look - look
        self.state.eye = _as_vec3(eye + delta)
        self.state.look_at = _as_vec3(new_look)
        self.state.up = WORLD_UP
        self.state = self._clamp_state_distance(self.state)
        self.state.view_name = "Free"
        self._dirty = True

    def zoom(self, delta: float) -> None:
        if not self.state.zoom_enabled:
            return
        self._cancel_animation()
        eye = np.asarray(self.state.eye, dtype=float)
        look = np.asarray(self.state.look_at, dtype=float)
        offset = eye - look
        dist = float(np.linalg.norm(offset))
        if dist < 1e-9:
            return
        direction = offset / dist
        new_dist = dist * math.exp(-delta * ZOOM_SENSITIVITY * 100.0)
        new_dist = float(np.clip(new_dist, self._min_distance, self._max_distance))
        self.state.eye = _as_vec3(look + direction * new_dist)
        self.state.up = WORLD_UP
        self.state = self._clamp_state_distance(self.state)
        self.state.view_name = "Free"
        self._dirty = True

    def track_to(self, target: Sequence[float]) -> None:
        look = np.asarray(self.state.look_at, dtype=float)
        eye = np.asarray(self.state.eye, dtype=float)
        offset = eye - look
        new_look = _as_vec3(target)
        self.state.look_at = new_look
        self.state.eye = (
            new_look[0] + float(offset[0]),
            new_look[1] + float(offset[1]),
            new_look[2] + float(offset[2]),
        )
        self._dirty = True

    def _subject_chest(self) -> Vec3:
        """Framing anchor on the upper body (horizon in lower third)."""
        floor_z = float(self.bounds.min_corner[2])
        height = max(float(self.bounds.extents[2]), 1.0)
        cx, cy, _ = self.bounds.center
        anchor_z = floor_z + height * LOOK_AT_HEIGHT_RATIO
        return (cx, cy, anchor_z)

    def _camera_eye_height(self) -> float:
        floor_z = float(self.bounds.min_corner[2])
        height = max(float(self.bounds.extents[2]), 1.0)
        return floor_z + height * EYE_HEIGHT_RATIO

    def _apply_breathing(self, state: CameraState) -> CameraState:
        """Imperceptible handheld drift — like an operator breathing."""
        if self.is_animating():
            return state
        amp = max(self.bounds.radius * BREATH_AMPLITUDE_FACTOR, 0.35)
        breath = math.sin(self._breath_phase) * amp
        breath_y = math.cos(self._breath_phase * 0.73) * amp * 0.4
        eye = np.asarray(state.eye, dtype=float) + np.array(
            [breath * 0.25, breath_y, breath * 0.12], dtype=float
        )
        look = np.asarray(state.look_at, dtype=float) + np.array(
            [breath * 0.08, breath_y * 0.18, 0.0], dtype=float
        )
        return replace(state, eye=_as_vec3(eye), look_at=_as_vec3(look))

    def _go_to_orbit_index(self, *, animate: bool = True) -> None:
        target = self._pose_for_orbit_index(self._orbit_index)
        if animate:
            self.animate_to(target)
        else:
            self.set_state(target, animate=False)

    def _pose_for_orbit_index(self, index: int) -> CameraState:
        """Return a full-body framed pose for one of four 90° views."""
        slot = int(index) % ORBIT_VIEW_COUNT
        azimuth = slot * ORBIT_AZIMUTH_STEP - (math.pi / 2.0)
        azimuth += math.radians(CAMERA_YAW_BIAS_DEG)
        elevation = ORBIT_ELEVATION_FACTOR
        # Horizontal orbit with slight elevation - never under the floor.
        direction = _normalize(
            (
                math.cos(azimuth),
                math.sin(azimuth),
                elevation,
            )
        )
        return self._framed_pose(
            direction=direction,
            view_name=ORBIT_VIEW_NAMES[slot],
        )

    def _framed_pose(
        self,
        *,
        direction: Sequence[float],
        view_name: str,
    ) -> CameraState:
        """Center subject at chest height and compute distance so head/feet never clip."""
        look = self._subject_chest()
        extents = self.bounds.extents
        height = max(float(extents[2]), 1.0)
        width = max(float(extents[0]), float(extents[1]), 1.0)
        fov = math.radians(DEFAULT_FOV_DEG)
        # Vertical FOV framing with margin - primary clinical constraint.
        dist_h = (0.5 * height * FIT_MARGIN) / max(math.tan(0.5 * fov), 1e-6)
        # Horizontal FOV (assume ~16:10 viewport → slightly wider than tall).
        aspect = 1.45
        hfov = 2.0 * math.atan(math.tan(0.5 * fov) * aspect)
        dist_w = (0.5 * width * FIT_MARGIN) / max(math.tan(0.5 * hfov), 1e-6)
        dist = max(dist_h, dist_w, self.bounds.radius * FIT_DISTANCE_FACTOR * 0.85)
        dist = float(np.clip(dist, self._min_distance, self._max_distance))
        direction_n = _normalize(direction)
        eye_z = self._camera_eye_height()
        eye = (
            look[0] + direction_n[0] * dist,
            look[1] + direction_n[1] * dist,
            eye_z,
        )
        near, far = self._clip_planes_for_distance(dist)
        state = CameraState(
            eye=_as_vec3(eye),
            look_at=look,
            up=WORLD_UP,
            fov_deg=DEFAULT_FOV_DEG,
            near=near,
            far=far,
            view_name=view_name,
        )
        return self._clamp_state_distance(state)

    def _pose_for_preset(self, preset: CameraPreset) -> CameraState:
        if preset == CameraPreset.RESET:
            return self._pose_for_orbit_index(0)
        if preset in {
            CameraPreset.ORBIT_0,
            CameraPreset.ORBIT_1,
            CameraPreset.ORBIT_2,
            CameraPreset.ORBIT_3,
        }:
            slot = int(preset.value.rsplit("_", maxsplit=1)[-1])
            return self._pose_for_orbit_index(slot)
        raise ValueError(f"Unknown camera preset: {preset!r}")

    def _refresh_distance_limits(self) -> None:
        radius = self.bounds.radius
        self._min_distance = max(radius * MIN_DISTANCE_RADIUS_FACTOR, 1.0)
        self._max_distance = max(
            radius * MAX_DISTANCE_RADIUS_FACTOR, self._min_distance * 2.0
        )

    def _clip_planes_for_distance(self, distance: float) -> tuple[float, float]:
        radius = self.bounds.radius
        near = max(distance * 0.001, radius * 0.001, 0.1)
        far = max(distance + radius * 25.0, radius * 60.0, near * 100.0)
        return float(near), float(far)

    def _clamp_state_distance(self, state: CameraState) -> CameraState:
        eye = np.asarray(state.eye, dtype=float)
        look = np.asarray(state.look_at, dtype=float)
        offset = eye - look
        dist = float(np.linalg.norm(offset))
        if dist < 1e-9:
            offset = np.array([-1.0, 0.0, 0.15], dtype=float)
            dist = float(np.linalg.norm(offset))
        direction = offset / dist
        dist = float(np.clip(dist, self._min_distance, self._max_distance))
        eye = look + direction * dist
        # Keep the eye above the subject floor plane (no underground views).
        floor_z = float(self.bounds.min_corner[2])
        clearance = max(self.bounds.radius * FLOOR_CLEARANCE_FACTOR, 20.0)
        min_eye_z = floor_z + clearance
        if eye[2] < min_eye_z:
            eye[2] = min_eye_z
            # Recompute distance after floor clamp while keeping look target.
            offset = eye - look
            dist = float(np.linalg.norm(offset))
            if dist < 1e-9:
                eye = look + np.array([-1.0, 0.0, clearance], dtype=float)
                dist = float(np.linalg.norm(eye - look))
            dist = float(np.clip(dist, self._min_distance, self._max_distance))
            direction = (eye - look) / max(dist, 1e-9)
            # Preserve polar clamp after floor push.
            phi = math.acos(float(np.clip(direction[2], -1.0, 1.0)))
            if phi > MAX_POLAR_ANGLE or phi < MIN_POLAR_ANGLE:
                phi = float(np.clip(phi, MIN_POLAR_ANGLE, MAX_POLAR_ANGLE))
                theta = math.atan2(direction[1], direction[0])
                direction = np.array(
                    [
                        math.sin(phi) * math.cos(theta),
                        math.sin(phi) * math.sin(theta),
                        math.cos(phi),
                    ],
                    dtype=float,
                )
                eye = look + direction * dist
                if eye[2] < min_eye_z:
                    eye[2] = min_eye_z
        near, far = self._clip_planes_for_distance(dist)
        return replace(
            state,
            eye=_as_vec3(eye),
            up=WORLD_UP,
            near=near,
            far=far,
        )

    def _cancel_animation(self) -> None:
        if self._animation is not None:
            self._animation.active = False
            self._animation = None


DEFAULT_CAMERA_DISTANCE: float = 1800.0
