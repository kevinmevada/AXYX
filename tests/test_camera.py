"""Tests for the professional CameraController."""

from __future__ import annotations

import math
import time

import numpy as np
import pytest

from motion_engine.camera import (
    ORBIT_VIEW_COUNT,
    ORBIT_VIEW_NAMES,
    BoundingBox,
    CameraController,
    CameraPreset,
)


@pytest.fixture
def controller() -> CameraController:
    pts = [
        [0.0, 0.0, 0.0],
        [200.0, 100.0, 1800.0],
        [-50.0, 80.0, 900.0],
    ]
    cam = CameraController()
    cam.set_model_points(pts)
    return cam


def test_bounding_box_metrics() -> None:
    box = BoundingBox.from_points([[0, 0, 0], [2, 4, 6]])
    assert box.center == (1.0, 2.0, 3.0)
    assert box.extents == (2.0, 4.0, 6.0)
    assert box.radius == pytest.approx(0.5 * np.linalg.norm([2, 4, 6]))


def test_orbital_presets_are_quadrants(controller: CameraController) -> None:
    assert len(CameraPreset) == ORBIT_VIEW_COUNT + 1
    assert CameraPreset.RESET in CameraPreset

    controller.reset(animate=False)
    assert controller.orbit_index == 0
    assert controller.state.view_name == "Front"
    look = np.asarray(controller.state.look_at)
    eye = np.asarray(controller.state.eye)
    assert eye[1] < look[1]

    controller.rotate_left(animate=False)
    assert controller.orbit_index == 1
    assert controller.state.view_name == "Right"
    eye = np.asarray(controller.state.eye)
    assert eye[0] > look[0]

    controller.rotate_left(animate=False)
    assert controller.state.view_name == "Back"
    assert controller.state.eye[1] > look[1]

    controller.rotate_left(animate=False)
    assert controller.state.view_name == "Left"
    assert controller.state.eye[0] < look[0]

    controller.rotate_left(animate=False)
    assert controller.orbit_index == 0
    assert controller.state.view_name == "Front"


def test_rotate_right_cycles_backward(controller: CameraController) -> None:
    controller.reset(animate=False)
    controller.rotate_right(animate=False)
    assert controller.orbit_index == ORBIT_VIEW_COUNT - 1
    assert controller.state.view_name == "Left"


def test_fit_and_reset(controller: CameraController) -> None:
    controller.fit(animate=False)
    dist_fit = controller.state.distance
    assert dist_fit >= controller._min_distance
    assert dist_fit <= controller._max_distance

    controller.reset(animate=False)
    assert controller.orbit_index == 0
    assert controller.state.view_name == ORBIT_VIEW_NAMES[0]


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
    controller.rotate_left(animate=False)
    before = controller.state.distance
    controller.zoom(5.0)
    assert controller.state.distance < before
    controller.zoom(-50.0)
    assert controller.state.distance <= controller._max_distance
    controller.orbit(40.0, 10.0)
    assert controller.state.view_name == "Free"
    controller.pan(20.0, -10.0)
    assert controller.is_dirty()


def test_get_set_state(controller: CameraController) -> None:
    controller.rotate_left(animate=False)
    snap = controller.get_state()
    controller.rotate_left(animate=False)
    controller.set_state(snap, animate=False)
    assert controller.state.view_name == "Right"


def test_set_preset_orbit_slots(controller: CameraController) -> None:
    controller.set_preset(CameraPreset.ORBIT_2, animate=False)
    assert controller.orbit_index == 2
    assert controller.state.view_name == "Back"


def test_unknown_preset_raises(controller: CameraController) -> None:
    with pytest.raises(ValueError):
        controller.set_preset("isometric", animate=False)
