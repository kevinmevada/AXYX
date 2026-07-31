"""Tests for the clinical CaptureVolume camera system."""

from __future__ import annotations

import time

import numpy as np
import pytest

from motion_engine.camera import (
    ORBIT_VIEW_COUNT,
    ORBIT_VIEW_NAMES,
    BoundingBox,
    CameraController,
    CameraManager,
    CameraPreset,
)
from motion_engine.capture_volume import CaptureVolume


@pytest.fixture
def controller() -> CameraController:
    # Motion drifts +Y → −Y so walk AB→DC aligns with −Y (DC near −Y).
    pts = []
    for t in np.linspace(0.0, 1.0, 40):
        y = 800.0 - 1600.0 * t
        pts.append([0.0, y, 0.0])
        pts.append([200.0, y, 1800.0])
        pts.append([-50.0, y + 80.0, 900.0])
    volume = CaptureVolume.from_motion(pts, floor_z=0.0, subject_height=1800.0)
    cam = CameraController()
    cam.set_model_points(pts)
    cam.set_capture_volume(volume)
    return cam


def test_camera_manager_alias() -> None:
    assert CameraManager is CameraController


def test_bounding_box_metrics() -> None:
    box = BoundingBox.from_points([[0, 0, 0], [2, 4, 6]])
    assert box.center == (1.0, 2.0, 3.0)
    assert box.extents == (2.0, 4.0, 6.0)
    assert box.radius == pytest.approx(0.5 * np.linalg.norm([2, 4, 6]))


def test_capture_volume_midpoints() -> None:
    vol = CaptureVolume(
        A=(-1.0, 1.0, 0.0),
        B=(1.0, 1.0, 0.0),
        C=(1.0, -1.0, 0.0),
        D=(-1.0, -1.0, 0.0),
        floor_z=0.0,
        subject_height=1800.0,
    )
    assert vol.mid_ab == pytest.approx((0.0, 1.0, 0.0))
    assert vol.mid_dc == pytest.approx((0.0, -1.0, 0.0))
    assert vol.mid_bc == pytest.approx((1.0, 0.0, 0.0))
    assert vol.mid_da == pytest.approx((-1.0, 0.0, 0.0))
    assert vol.walk_direction[1] < 0.0


def test_default_is_back_dc(controller: CameraController) -> None:
    controller.reset(animate=False)
    assert controller.orbit_index == 2
    assert controller.state.view_name == "Back"
    look = np.asarray(controller.state.look_at)
    eye = np.asarray(controller.state.eye)
    # DC is on the near/walk-end side; eye sits on outward DC ray.
    assert eye[1] < look[1]


def test_orbital_presets_from_volume_edges(controller: CameraController) -> None:
    controller.front(animate=False)
    assert controller.state.view_name == "Front"
    look = np.asarray(controller.state.look_at)
    eye = np.asarray(controller.state.eye)
    assert eye[1] > look[1]

    controller.right(animate=False)
    assert controller.state.view_name == "Right"
    eye = np.asarray(controller.state.eye)
    assert eye[0] > look[0]

    controller.back(animate=False)
    assert controller.state.view_name == "Back"
    assert controller.state.eye[1] < look[1]

    controller.left(animate=False)
    assert controller.state.view_name == "Left"
    assert controller.state.eye[0] < look[0]


def test_rotate_cycles_names(controller: CameraController) -> None:
    controller.front(animate=False)
    names = []
    for _ in range(ORBIT_VIEW_COUNT):
        names.append(controller.state.view_name)
        controller.rotate_left(animate=False)
    assert names == list(ORBIT_VIEW_NAMES)


def test_fit_and_reset(controller: CameraController) -> None:
    controller.fit(animate=False)
    dist_fit = controller.state.distance
    assert dist_fit >= controller._min_distance
    assert dist_fit <= controller._max_distance

    controller.reset(animate=False)
    assert controller.orbit_index == 2
    assert controller.state.view_name == "Back"


def test_animation_is_interruptible(controller: CameraController) -> None:
    controller.rotate_left(animate=True)
    assert controller.is_animating()
    controller.rotate_right(animate=True)
    assert controller.is_animating()
    start = time.perf_counter()
    while controller.is_animating() and time.perf_counter() - start < 1.0:
        controller.update(0.016)
        time.sleep(0.01)
    assert controller.state.view_name in ORBIT_VIEW_NAMES


def test_orbit_pan_zoom_constraints(controller: CameraController) -> None:
    controller.right(animate=False)
    before = controller.state.distance
    controller.zoom(5.0)
    assert controller.state.distance < before
    controller.zoom(-50.0)
    assert controller.state.distance <= controller._max_distance
    controller.orbit(40.0, 10.0)
    assert controller.state.view_name == "Free"
    controller.pan(20.0, -10.0)
    assert controller.is_dirty()


def test_set_preset_clinical_names(controller: CameraController) -> None:
    controller.set_camera("front", animate=False)
    assert controller.state.view_name == "Front"
    controller.set_preset(CameraPreset.DEFAULT, animate=False)
    assert controller.state.view_name == "Back"
    controller.set_preset(CameraPreset.ORBIT_1, animate=False)
    assert controller.state.view_name == "Right"


def test_look_at_is_volume_center(controller: CameraController) -> None:
    assert controller.volume is not None
    controller.front(animate=False)
    look = np.asarray(controller.state.look_at)
    center = np.asarray(controller.volume.center)
    assert look[0] == pytest.approx(center[0], abs=1e-6)
    assert look[1] == pytest.approx(center[1], abs=1e-6)


def test_no_hardcoded_eye_when_volume_scales() -> None:
    small = CaptureVolume.from_motion(
        [[0, 0, 0], [100, 0, 1600], [0, -200, 800]],
        floor_z=0.0,
        subject_height=1600.0,
    )
    large = CaptureVolume.from_motion(
        [[0, 0, 0], [1000, 0, 1800], [0, -2000, 900]],
        floor_z=0.0,
        subject_height=1800.0,
    )
    a = CameraController()
    a.set_capture_volume(small)
    a.set_model_points([[0, 0, 0], [100, 0, 1600]])
    a.back(animate=False)
    b = CameraController()
    b.set_capture_volume(large)
    b.set_model_points([[0, 0, 0], [1000, 0, 1800]])
    b.back(animate=False)
    assert b.state.distance > a.state.distance
