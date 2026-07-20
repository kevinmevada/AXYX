"""Tests for the Visualization Engine viewer layer."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from motion_engine.camera import CameraPreset
from motion_engine.playback import PlaybackState
from motion_engine.renderer import NullRenderer
from motion_engine.skeleton import Bone, Joint, Pose, Skeleton
from motion_engine.viewer import (
    Open3DViewer,
    PyVistaViewer,
    SkeletonViewer,
    Viewer,
    ViewerError,
)


def _make_skeleton(n_frames: int = 5) -> Skeleton:
    """Build a tiny synthetic skeleton (no MATLAB / database)."""
    joints = {
        "Pelvis": Joint(name="Pelvis", parent=None, children=["Head"]),
        "Head": Joint(name="Head", parent="Pelvis", children=[]),
    }
    bones = {
        "Pelvis_Head": Bone(
            name="Pelvis_Head",
            parent_joint="Pelvis",
            child_joint="Head",
            length=200.0,
        )
    }
    poses: list[Pose] = []
    for i in range(n_frames):
        offset = float(i) * 10.0
        poses.append(
            Pose(
                frame_index=i,
                joint_positions={
                    "Pelvis": np.array([offset, 0.0, 900.0], dtype=float),
                    "Head": np.array([offset, 0.0, 1100.0], dtype=float),
                },
            )
        )
    return Skeleton(
        name="synthetic",
        subject_id="S_TEST",
        session_name="WU00",
        root_joint="Pelvis",
        joints=joints,
        bones=bones,
        poses=poses,
        n_frames=n_frames,
        sampling_rate_hz=100.0,
        coordinate_system="lab",
    )


@pytest.fixture
def skeleton() -> Skeleton:
    return _make_skeleton()


@pytest.fixture
def viewer(skeleton: Skeleton) -> SkeletonViewer:
    v = SkeletonViewer(renderer=NullRenderer(), block=False)
    v.show(skeleton)
    return v


def test_viewer_is_abstract_interface() -> None:
    assert issubclass(SkeletonViewer, Viewer)
    assert issubclass(Open3DViewer, Viewer)
    assert issubclass(PyVistaViewer, Viewer)


def test_show_initializes_and_draws(viewer: SkeletonViewer) -> None:
    assert viewer.skeleton is not None
    assert viewer._initialized is True
    renderer = viewer.renderer
    assert isinstance(renderer, NullRenderer)
    assert renderer.initialized is True
    assert any(c.startswith("sphere:") for c in renderer.draw_calls)
    assert any(c.startswith("line:") for c in renderer.draw_calls)
    assert "ground" in renderer.draw_calls
    assert "grid" in renderer.draw_calls
    # Axes are optional and off by default for a clean studio look.
    assert "axes" not in renderer.draw_calls or viewer.scene.show_axes is False


def test_playback_controls(viewer: SkeletonViewer) -> None:
    viewer.pause()
    assert viewer.playback.state is PlaybackState.PAUSED
    viewer.play()
    assert viewer.playback.state is PlaybackState.PLAYING
    viewer.next_frame()
    assert viewer.timeline.current_frame == 1
    viewer.previous_frame()
    assert viewer.timeline.current_frame == 0
    viewer.seek(3)
    assert viewer.timeline.current_frame == 3
    viewer.set_speed(2.0)
    assert viewer.playback.speed == 2.0
    viewer.stop()
    assert viewer.playback.state is PlaybackState.STOPPED
    assert viewer.timeline.current_frame == 0


def test_toggles(viewer: SkeletonViewer) -> None:
    before_axes = viewer.scene.show_axes
    viewer.toggle_axes()
    assert viewer.scene.show_axes is not before_axes
    viewer.toggle_grid()
    viewer.toggle_ground()
    viewer.toggle_joint_labels()
    viewer.toggle_bone_labels()
    assert viewer.show_joint_labels is True
    assert viewer.show_bone_labels is True


def test_camera_presets(viewer: SkeletonViewer) -> None:
    viewer.camera.reset(animate=False)
    assert viewer.camera.state.view_name == "Front"

    viewer.camera.rotate_left(animate=False)
    assert viewer.camera.state.view_name == "Right"

    viewer.camera.rotate_right(animate=False)
    assert viewer.camera.state.view_name == "Front"

    viewer.set_camera_preset(CameraPreset.ORBIT_2)
    viewer.camera.set_preset(CameraPreset.ORBIT_2, animate=False)
    assert viewer.camera.state.view_name == "Back"

    viewer.reset()
    viewer.camera.reset(animate=False)
    assert viewer.timeline.current_frame == 0
    assert viewer.camera.state.view_name == "Front"


def test_screenshot(tmp_path: Path, viewer: SkeletonViewer) -> None:
    out = tmp_path / "frame.png"
    path = viewer.screenshot(out)
    assert path == out
    assert out.exists()
    path2 = viewer.save_frame(tmp_path / "frame2.png")
    assert path2.exists()


def test_recording_api(tmp_path: Path, viewer: SkeletonViewer) -> None:
    viewer.start_recording()
    assert viewer._is_recording is True
    # Null renderer cannot capture pixels - stopping with no frames should error.
    with pytest.raises(ViewerError):
        viewer.stop_recording(tmp_path / "out.mp4")
    assert viewer._is_recording is False


def test_close(viewer: SkeletonViewer) -> None:
    viewer.close()
    assert viewer._initialized is False
    assert isinstance(viewer.renderer, NullRenderer)
    assert viewer.renderer.closed is True


def test_show_requires_poses() -> None:
    empty = Skeleton(
        name="empty",
        subject_id="S0",
        session_name="X",
        root_joint="Pelvis",
        n_frames=0,
        poses=[],
    )
    v = SkeletonViewer(renderer=NullRenderer(), block=False)
    with pytest.raises(ViewerError):
        v.show(empty)


def test_update_frame_without_show_raises() -> None:
    v = SkeletonViewer(renderer=NullRenderer(), block=False)
    with pytest.raises(ViewerError):
        v.update_frame(0)


def test_viewer_never_imports_open3d() -> None:
    import motion_engine.viewer as viewer_mod

    source = Path(viewer_mod.__file__).read_text(encoding="utf-8")
    assert "import open3d" not in source
    assert "from open3d" not in source
