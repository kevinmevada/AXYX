"""
Renderer abstraction - VTK / PyVista studio backend.

``viewer.py`` talks only to :class:`Renderer`. Concrete backends:

* :class:`PyVistaRenderer` - production studio renderer (default)
* :class:`NullRenderer` - headless unit tests

Legacy Open3D / Matplotlib paths are not used by the new studio viewer.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Sequence

import numpy as np
from numpy.typing import NDArray

from motion_engine.camera import CameraState
from motion_engine.colors import ColorRGB, DEFAULT_THEME, Theme
from motion_engine.exceptions import MotionEngineError
from motion_engine.scene import Scene

logger = logging.getLogger(__name__)

FloatArray = NDArray[np.floating[Any]]

TARGET_RENDER_FPS: int = 120
JOINT_SPHERE_RESOLUTION: int = 24
BONE_TUBE_SIDES: int = 20
FLOOR_RESOLUTION: int = 48
GRID_MAJOR_STEP_RATIO: float = 0.10
# Black metallic bones / golden metallic joints / matte white floor.
BONE_METALLIC: float = 0.88
BONE_ROUGHNESS: float = 0.32
JOINT_METALLIC: float = 0.92
JOINT_ROUGHNESS: float = 0.26
FLOOR_METALLIC: float = 0.02
FLOOR_ROUGHNESS: float = 0.78
CONTACT_SHADOW_OPACITY: float = 0.16
GRID_MAJOR_OPACITY: float = 0.28
GRID_MINOR_OPACITY: float = 0.12


class RendererError(MotionEngineError):
    """Raised when a rendering backend fails."""


class Renderer(ABC):
    """Abstract 3D renderer."""

    def __init__(self, theme: Theme | None = None) -> None:
        self.theme = theme or DEFAULT_THEME
        self.scene = Scene(background=self.theme.background)

    @abstractmethod
    def initialize(self, title: str = "Motion Engine Viewer") -> None:
        """Create the window / GPU context."""

    @abstractmethod
    def clear(self) -> None:
        """Clear per-frame skeleton buffers."""

    @abstractmethod
    def draw_sphere(
        self,
        center: Sequence[float],
        radius: float,
        color: ColorRGB,
        *,
        name: str = "",
    ) -> None:
        """Queue a joint sphere."""

    @abstractmethod
    def draw_line(
        self,
        start: Sequence[float],
        end: Sequence[float],
        color: ColorRGB,
        *,
        width: float = 2.0,
        name: str = "",
    ) -> None:
        """Queue a bone segment."""

    @abstractmethod
    def draw_ground(
        self,
        size: float,
        color: ColorRGB,
        *,
        origin: Sequence[float] = (0.0, 0.0, 0.0),
    ) -> None:
        """Draw studio floor."""

    @abstractmethod
    def draw_axes(self, origin: Sequence[float], length: float) -> None:
        """Draw coordinate triad."""

    @abstractmethod
    def draw_grid(
        self,
        size: float,
        divisions: int,
        color: ColorRGB,
        *,
        origin: Sequence[float] = (0.0, 0.0, 0.0),
    ) -> None:
        """Draw scientific floor grid."""

    @abstractmethod
    def set_camera(self, camera: CameraState) -> None:
        """Apply camera state."""

    @abstractmethod
    def set_background(self, color: ColorRGB) -> None:
        """Set clear / gradient background."""

    @abstractmethod
    def render(self) -> None:
        """Flush draw calls."""

    @abstractmethod
    def poll_events(self) -> bool:
        """Process UI events. False if closed."""

    @abstractmethod
    def screenshot(self, path: Path, *, transparent: bool = False, scale: int = 1) -> Path:
        """Capture framebuffer."""

    @abstractmethod
    def close(self) -> None:
        """Destroy the window / context."""

    def draw_text(self, text: str, x: float, y: float, color: ColorRGB) -> None:
        """Optional HUD text."""
        return

    def draw_label_3d(
        self,
        text: str,
        position: Sequence[float],
        color: ColorRGB,
    ) -> None:
        """Optional world-space label."""
        return

    def bind_key(self, key: str, callback: Any) -> None:
        """Optional keyboard binding."""
        return

    def set_lighting_enabled(self, enabled: bool) -> None:
        """Toggle cinematic lights."""
        return


class NullRenderer(Renderer):
    """Headless renderer for unit tests."""

    def __init__(self, theme: Theme | None = None) -> None:
        super().__init__(theme=theme)
        self.initialized = False
        self.closed = False
        self.draw_calls: list[str] = []
        self.camera: CameraState | None = None
        self.last_screenshot: Path | None = None

    def initialize(self, title: str = "Motion Engine Viewer") -> None:
        self.initialized = True
        self.draw_calls.append(f"initialize:{title}")

    def clear(self) -> None:
        self.draw_calls.append("clear")

    def draw_sphere(
        self,
        center: Sequence[float],
        radius: float,
        color: ColorRGB,
        *,
        name: str = "",
    ) -> None:
        self.draw_calls.append(f"sphere:{name}")

    def draw_line(
        self,
        start: Sequence[float],
        end: Sequence[float],
        color: ColorRGB,
        *,
        width: float = 2.0,
        name: str = "",
    ) -> None:
        self.draw_calls.append(f"line:{name}")

    def draw_ground(
        self,
        size: float,
        color: ColorRGB,
        *,
        origin: Sequence[float] = (0.0, 0.0, 0.0),
    ) -> None:
        self.draw_calls.append("ground")

    def draw_axes(self, origin: Sequence[float], length: float) -> None:
        self.draw_calls.append("axes")

    def draw_grid(
        self,
        size: float,
        divisions: int,
        color: ColorRGB,
        *,
        origin: Sequence[float] = (0.0, 0.0, 0.0),
    ) -> None:
        self.draw_calls.append("grid")

    def set_camera(self, camera: CameraState) -> None:
        self.camera = camera
        self.draw_calls.append("camera")

    def set_background(self, color: ColorRGB) -> None:
        self.draw_calls.append("background")

    def render(self) -> None:
        self.draw_calls.append("render")

    def poll_events(self) -> bool:
        return not self.closed

    def screenshot(
        self, path: Path, *, transparent: bool = False, scale: int = 1
    ) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"")
        self.last_screenshot = path
        return path

    def close(self) -> None:
        self.closed = True
        self.draw_calls.append("close")


class PyVistaRenderer(Renderer):
    """VTK / PyVista studio renderer with cinematic lighting and PBR materials."""

    def __init__(
        self,
        theme: Theme | None = None,
        *,
        plotter: Any | None = None,
        off_screen: bool = False,
    ) -> None:
        super().__init__(theme=theme)
        try:
            import pyvista as pv
        except ImportError as exc:
            raise RendererError(
                "PyVista is required for the studio Visualization Engine. "
                "Install with: pip install pyvista pyvistaqt"
            ) from exc
        self._pv = pv
        self._plotter: Any = plotter
        self._owns_plotter = plotter is None
        self._off_screen = off_screen
        self._joint_pts: list[np.ndarray] = []
        self._joint_colors: list[ColorRGB] = []
        self._joint_radius = 25.0
        self._bone_segs: list[tuple[np.ndarray, np.ndarray]] = []
        self._bone_colors: list[ColorRGB] = []
        self._ground_args: tuple[float, ColorRGB, np.ndarray] | None = None
        self._grid_args: tuple[float, int, ColorRGB, np.ndarray] | None = None
        self._axes_args: tuple[np.ndarray, float] | None = None
        self._pending_camera: CameraState | None = None
        self._env_built = False
        self._lighting_enabled = True
        self._closed = False
        self._actors: dict[str, Any] = {}
        self._env_sigs: dict[str, Any] = {}
        self._labels: list[tuple[str, Sequence[float], ColorRGB]] = []
        self._bone_radius_scale = 0.42
        self._skeleton_sig: tuple[Any, ...] | None = None
        self._joint_mesh: Any | None = None
        self._bone_mesh: Any | None = None
        self._bone_line_mesh: Any | None = None
        self._bone_tube_mesh: Any | None = None
        self._bone_tube_radius: float = 14.0
        self._joint_template_pts: np.ndarray | None = None
        self._joint_template_faces: np.ndarray | None = None
        self._joint_points_per_sphere: int = 0
        self._bone_segment_count: int = 0

    @property
    def plotter(self) -> Any:
        if self._plotter is None:
            raise RendererError("Renderer is not initialized")
        return self._plotter

    def initialize(self, title: str = "Motion Engine Viewer") -> None:
        if self._plotter is None:
            self._plotter = self._pv.Plotter(
                window_size=(1600, 960),
                off_screen=self._off_screen,
                title=title,
                lighting="none",
            )
            self._owns_plotter = True
        self._configure_render_window()
        self._setup_lighting()
        self._setup_environment()
        self._closed = False

    def attach_plotter(self, plotter: Any) -> None:
        """Attach an externally owned Qt/PyVista plotter."""
        self._plotter = plotter
        self._owns_plotter = False
        self._configure_render_window()
        self._setup_lighting()
        self._setup_environment()

    def clear(self) -> None:
        """Clear per-frame draw queues (does not destroy GPU skeleton cache)."""
        self._joint_pts.clear()
        self._joint_colors.clear()
        self._bone_segs.clear()
        self._bone_colors.clear()
        self._labels.clear()

    def draw_sphere(
        self,
        center: Sequence[float],
        radius: float,
        color: ColorRGB,
        *,
        name: str = "",
    ) -> None:
        self._joint_pts.append(np.asarray(center, dtype=float))
        self._joint_colors.append(color)
        self._joint_radius = radius

    def draw_line(
        self,
        start: Sequence[float],
        end: Sequence[float],
        color: ColorRGB,
        *,
        width: float = 2.0,
        name: str = "",
    ) -> None:
        self._bone_segs.append(
            (np.asarray(start, dtype=float), np.asarray(end, dtype=float))
        )
        self._bone_colors.append(color)

    def draw_ground(
        self,
        size: float,
        color: ColorRGB,
        *,
        origin: Sequence[float] = (0.0, 0.0, 0.0),
    ) -> None:
        self._ground_args = (size, color, np.asarray(origin, dtype=float))

    def draw_axes(self, origin: Sequence[float], length: float) -> None:
        self._axes_args = (np.asarray(origin, dtype=float), float(length))

    def draw_grid(
        self,
        size: float,
        divisions: int,
        color: ColorRGB,
        *,
        origin: Sequence[float] = (0.0, 0.0, 0.0),
    ) -> None:
        self._grid_args = (
            size,
            divisions,
            color,
            np.asarray(origin, dtype=float),
        )

    def set_camera(self, camera: CameraState) -> None:
        self._pending_camera = camera

    def set_background(self, color: ColorRGB) -> None:
        """Apply a subtle vertical studio gradient (top → bottom)."""
        if self._plotter is None:
            return
        # Prefer theme top/bottom; ``color`` is the bottom stop when provided.
        top = tuple(int(c * 255) for c in self.theme.background_top)
        bottom = tuple(int(c * 255) for c in color)
        self._plotter.set_background(bottom, top=top)

    def set_lighting_enabled(self, enabled: bool) -> None:
        self._lighting_enabled = enabled
        if self._plotter is None:
            return
        if enabled:
            self._setup_lighting()
        else:
            self._plotter.remove_all_lights()

    def render(self) -> None:
        if self._plotter is None:
            return
        self._flush_environment()
        self._flush_skeleton()
        if self._pending_camera is not None:
            self._apply_camera(self._pending_camera)
            self._pending_camera = None
        self._plotter.render()

    def poll_events(self) -> bool:
        if self._closed or self._plotter is None:
            return False
        if getattr(self._plotter, "ren_win", None) is None:
            return False
        return True

    def screenshot(
        self, path: Path, *, transparent: bool = False, scale: int = 1
    ) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if self._plotter is not None:
            self._plotter.screenshot(
                str(path),
                transparent_background=transparent,
                scale=max(1, int(scale)),
            )
        return path

    def close(self) -> None:
        self._closed = True
        self._skeleton_sig = None
        self._joint_mesh = None
        self._bone_mesh = None
        self._bone_line_mesh = None
        self._bone_tube_mesh = None
        self._bone_tube_radius = 14.0
        self._joint_template_pts = None
        self._joint_template_faces = None
        self._joint_points_per_sphere = 0
        self._bone_segment_count = 0
        if self._plotter is not None and self._owns_plotter:
            try:
                self._plotter.close()
            except Exception:
                logger.debug("Plotter close failed", exc_info=True)
        if self._owns_plotter:
            self._plotter = None
        self._actors.clear()
        self._env_sigs.clear()
        self._labels.clear()
        self._env_built = False

    def _invalidate_skeleton_cache(self) -> None:
        self._skeleton_sig = None
        self._joint_mesh = None
        self._bone_mesh = None
        self._bone_line_mesh = None
        self._bone_tube_mesh = None
        self._bone_tube_radius = 14.0
        self._joint_template_pts = None
        self._joint_template_faces = None
        self._joint_points_per_sphere = 0
        self._bone_segment_count = 0
        if self._plotter is None:
            return
        self._remove_actor("bones")
        self._remove_actor("joints")
        self._remove_actor("labels")

    # ---- setup -----------------------------------------------------------

    def _configure_render_window(self) -> None:
        assert self._plotter is not None
        ren_win = self._plotter.ren_win
        if ren_win is not None:
            try:
                ren_win.SetMultiSamples(8)
            except Exception:
                try:
                    ren_win.SetMultiSamples(4)
                except Exception:
                    pass
        try:
            self._plotter.enable_anti_aliasing("msaa", multi_samples=8)
        except Exception:
            try:
                self._plotter.enable_anti_aliasing("fxaa")
            except Exception:
                try:
                    self._plotter.enable_anti_aliasing()
                except Exception:
                    pass
        self.set_background(self.theme.background)
        # Depth cueing is handled by lighting/silhouette - VTK fog uses camera
        # distance units; tiny start/end values wash the entire scene to fog color.
        try:
            renderer = self._plotter.renderer
            if hasattr(renderer, "SetUseFog"):
                renderer.SetUseFog(False)
            elif hasattr(renderer, "UseFogOff"):
                renderer.UseFogOff()
        except Exception:
            logger.debug("Fog toggle unsupported on this VTK build", exc_info=True)

    def _setup_lighting(self) -> None:
        """Professional three-point studio lighting (key / fill / rim + ambient)."""
        assert self._plotter is not None
        self._plotter.remove_all_lights()
        key = self._pv.Light(
            position=(-1.6, -1.1, 2.4),
            focal_point=(0.0, 0.0, 0.55),
            color=(1.0, 0.98, 0.94),
            intensity=1.35,
            positional=False,
        )
        fill = self._pv.Light(
            position=(1.4, 0.9, 1.5),
            focal_point=(0.0, 0.0, 0.5),
            color=(0.88, 0.92, 1.0),
            intensity=0.50,
            positional=False,
        )
        rim = self._pv.Light(
            position=(0.15, 1.8, 1.2),
            focal_point=(0.0, 0.0, 0.65),
            color=(1.0, 0.97, 0.92),
            intensity=0.48,
            positional=False,
        )
        ambient = self._pv.Light(light_type="headlight", intensity=0.40)
        for light in (key, fill, rim, ambient):
            self._plotter.add_light(light)
        try:
            self._plotter.disable_shadows()
        except Exception:
            pass

    def _setup_environment(self) -> None:
        # Environment is rebuilt when ground/grid args arrive.
        self._env_built = False

    def _apply_pbr(
        self,
        actor: Any,
        *,
        metallic: float,
        roughness: float,
        specular: float = 0.18,
        specular_power: float = 22.0,
    ) -> None:
        try:
            prop = actor.GetProperty()
            prop.SetInterpolationToPBR()
            prop.SetMetallic(float(metallic))
            prop.SetRoughness(float(roughness))
            prop.SetSpecular(float(specular))
            prop.SetSpecularPower(float(specular_power))
        except Exception:
            prop = actor.GetProperty()
            prop.SetInterpolationToPhong()
            prop.SetSpecular(float(specular))
            prop.SetSpecularPower(float(specular_power))

    # ---- flush -----------------------------------------------------------

    def _remove_actor(self, key: str) -> None:
        assert self._plotter is not None
        actor = self._actors.pop(key, None)
        if actor is None:
            return
        actors = actor if isinstance(actor, (list, tuple)) else (actor,)
        for item in actors:
            try:
                self._plotter.remove_actor(item, render=False)
            except Exception:
                pass

    def _flush_environment(self) -> None:
        assert self._plotter is not None
        show_ground = self.scene.show_ground and self._ground_args is not None
        show_grid = self.scene.show_grid and self._grid_args is not None
        show_axes = self.scene.show_axes and self._axes_args is not None

        if not show_ground:
            self._remove_actor("ground")
            self._remove_actor("floor_reflect")
            self._remove_actor("contact_shadow")
            self._env_sigs.pop("ground", None)
        if not show_grid:
            self._remove_actor("grid")
            self._remove_actor("grid_minor")
            self._env_sigs.pop("grid", None)
        if not show_axes:
            self._remove_actor("axes")
            self._env_sigs.pop("axes", None)

        if show_ground and self._ground_args is not None:
            size, color, origin = self._ground_args
            signature = (
                round(size, 3),
                round(float(origin[0]), 3),
                round(float(origin[1]), 3),
                round(float(origin[2]), 3),
                color,
            )
            if self._env_sigs.get("ground") != signature:
                self._remove_actor("ground")
                self._remove_actor("floor_reflect")
                self._remove_actor("contact_shadow")
                plane = self._pv.Plane(
                    center=(float(origin[0]), float(origin[1]), float(origin[2])),
                    direction=(0, 0, 1),
                    i_size=size,
                    j_size=size,
                    i_resolution=FLOOR_RESOLUTION,
                    j_resolution=FLOOR_RESOLUTION,
                )
                actor = self._plotter.add_mesh(
                    plane,
                    color=color,
                    smooth_shading=True,
                    ambient=0.22,
                    diffuse=0.78,
                    specular=0.04,
                    name="studio_floor",
                    render=False,
                )
                self._apply_pbr(
                    actor,
                    metallic=FLOOR_METALLIC,
                    roughness=FLOOR_ROUGHNESS,
                    specular=0.05,
                    specular_power=8.0,
                )
                self._actors["ground"] = actor

                # Soft Gaussian-like contact shadow under the subject.
                shadow = self._pv.Disc(
                    center=(
                        float(origin[0]),
                        float(origin[1]),
                        float(origin[2]) + 0.35,
                    ),
                    inner=0.0,
                    outer=size * 0.22,
                    normal=(0, 0, 1),
                    r_res=2,
                    c_res=64,
                )
                contact = self._plotter.add_mesh(
                    shadow,
                    color=(0.12, 0.13, 0.15),
                    opacity=CONTACT_SHADOW_OPACITY,
                    smooth_shading=True,
                    name="contact_shadow",
                    render=False,
                )
                try:
                    contact.GetProperty().SetOpacity(CONTACT_SHADOW_OPACITY)
                    contact.GetProperty().SetLighting(False)
                except Exception:
                    pass
                self._actors["contact_shadow"] = contact

                # Soft distance fade rings - ground dissolves into the void.
                fade_actors = []
                for ring_i, (inner_r, outer_r, opacity) in enumerate(
                    (
                        (0.42, 0.55, 0.10),
                        (0.55, 0.70, 0.16),
                        (0.70, 0.92, 0.22),
                    )
                ):
                    ring = self._pv.Disc(
                        center=(
                            float(origin[0]),
                            float(origin[1]),
                            float(origin[2]) + 0.45 + ring_i * 0.05,
                        ),
                        inner=size * inner_r,
                        outer=size * outer_r,
                        normal=(0, 0, 1),
                        r_res=1,
                        c_res=64,
                    )
                    fade = self._plotter.add_mesh(
                        ring,
                        color=self.theme.background,
                        opacity=opacity,
                        smooth_shading=True,
                        name=f"floor_fade_{ring_i}",
                        render=False,
                    )
                    try:
                        fade.GetProperty().SetLighting(False)
                    except Exception:
                        pass
                    fade_actors.append(fade)
                self._actors["floor_reflect"] = fade_actors
                self._env_sigs["ground"] = signature

        if show_grid and self._grid_args is not None:
            size, divisions, color, origin = self._grid_args
            signature = (
                round(size, 3),
                int(divisions),
                round(float(origin[0]), 3),
                round(float(origin[1]), 3),
                round(float(origin[2]), 3),
                color,
                self.theme.grid_minor,
            )
            if self._env_sigs.get("grid") != signature:
                self._remove_actor("grid")
                self._remove_actor("grid_minor")
                major_mesh, minor_mesh = self._build_grid_meshes(
                    size, divisions, origin
                )
                major = self._plotter.add_mesh(
                    major_mesh,
                    color=color,
                    line_width=1.15,
                    opacity=GRID_MAJOR_OPACITY,
                    name="studio_grid_major",
                    render=False,
                )
                minor = self._plotter.add_mesh(
                    minor_mesh,
                    color=self.theme.grid_minor,
                    line_width=0.8,
                    opacity=GRID_MINOR_OPACITY,
                    name="studio_grid_minor",
                    render=False,
                )
                self._actors["grid"] = major
                self._actors["grid_minor"] = minor
                self._env_sigs["grid"] = signature

        if show_axes and self._axes_args is not None:
            origin, length = self._axes_args
            signature = (
                round(float(origin[0]), 3),
                round(float(origin[1]), 3),
                round(float(origin[2]), 3),
                round(float(length), 3),
            )
            if self._env_sigs.get("axes") != signature:
                self._remove_actor("axes")
                o = origin
                axis_length = length
                tubes = [
                    self._pv.Line(o, (o[0] + axis_length, o[1], o[2])).tube(
                        radius=axis_length * 0.018, n_sides=16
                    ),
                    self._pv.Line(o, (o[0], o[1] + axis_length, o[2])).tube(
                        radius=axis_length * 0.018, n_sides=16
                    ),
                    self._pv.Line(o, (o[0], o[1], o[2] + axis_length)).tube(
                        radius=axis_length * 0.018, n_sides=16
                    ),
                ]
                actors = []
                for idx, (block, col) in enumerate(
                    zip(
                        tubes,
                        (self.theme.axis_x, self.theme.axis_y, self.theme.axis_z),
                        strict=True,
                    )
                ):
                    act = self._plotter.add_mesh(
                        block,
                        color=col,
                        smooth_shading=True,
                        name=f"axis_{idx}",
                        render=False,
                    )
                    self._apply_pbr(act, metallic=0.25, roughness=0.40)
                    actors.append(act)
                self._actors["axes"] = actors
                self._env_sigs["axes"] = signature

        self._env_built = True

    def _build_grid_meshes(
        self, size: float, divisions: int, origin: np.ndarray
    ) -> tuple[Any, Any]:
        """Return (major, minor) floor grid line meshes."""
        half = size * 0.5
        step = size / max(divisions, 1)
        ox, oy, oz = float(origin[0]), float(origin[1]), float(origin[2]) + 0.8
        major_lines: list[Any] = []
        minor_lines: list[Any] = []
        for i in range(divisions + 1):
            t = -half + i * step
            is_major = i % 5 == 0 or i == 0 or i == divisions
            x_line = self._pv.Line(
                (ox + t, oy - half, oz), (ox + t, oy + half, oz)
            )
            y_line = self._pv.Line(
                (ox - half, oy + t, oz), (ox + half, oy + t, oz)
            )
            bucket = major_lines if is_major else minor_lines
            bucket.extend((x_line, y_line))
        return self._merge_lines(major_lines), self._merge_lines(minor_lines)

    def _merge_lines(self, lines: list[Any]) -> Any:
        if not lines:
            return self._pv.PolyData()
        try:
            return self._pv.merge(lines)
        except Exception:
            mesh = lines[0]
            for line in lines[1:]:
                mesh = mesh.merge(line)
            return mesh

    def _build_grid_mesh(
        self, size: float, divisions: int, origin: np.ndarray
    ) -> Any:
        major, _minor = self._build_grid_meshes(size, divisions, origin)
        return major

    def draw_text(self, text: str, x: float, y: float, color: ColorRGB) -> None:
        """Optional 2D HUD text (no-op in studio viewport; status bar owns HUD)."""
        return

    def draw_label_3d(
        self,
        text: str,
        position: Sequence[float],
        color: ColorRGB,
    ) -> None:
        """Queue a 3D world-space label."""
        self._labels.append((text, position, color))

    def _flush_skeleton(self) -> None:
        assert self._plotter is not None
        has_labels = bool(self._labels)
        sig = self._skeleton_signature(has_labels)
        if self._skeleton_sig == sig:
            if not self._bone_segs and not self._joint_pts:
                self._invalidate_skeleton_cache()
                return
            if "joints" in self._actors or "bones" in self._actors:
                self._update_skeleton_positions()
                return

        self._invalidate_skeleton_cache()
        self._skeleton_sig = sig
        self._build_skeleton_actors(has_labels)

    def _skeleton_signature(self, has_labels: bool) -> tuple[Any, ...]:
        joint_colors = tuple(self._joint_colors)
        bone_colors = tuple(self._bone_colors)
        return (
            len(self._joint_pts),
            len(self._bone_segs),
            round(self._joint_radius, 3),
            round(max(self._joint_radius * self._bone_radius_scale, 14.0), 3),
            joint_colors,
            bone_colors,
            has_labels,
        )

    def _build_skeleton_actors(self, has_labels: bool) -> None:
        assert self._plotter is not None
        if self._bone_segs:
            self._bone_line_mesh, self._bone_segment_count = self._make_bone_line_mesh(
                self._bone_segs
            )
            self._bone_tube_radius = max(
                self._joint_radius * self._bone_radius_scale, 14.0
            )
            self._bone_tube_mesh = self._bone_line_mesh.tube(
                radius=self._bone_tube_radius,
                n_sides=BONE_TUBE_SIDES,
                capping=True,
            )
            self._bone_mesh = self._bone_tube_mesh
            bone_color = (
                self._bone_colors[0]
                if len(set(self._bone_colors)) == 1
                else self.theme.bone
            )
            actor = self._plotter.add_mesh(
                self._bone_tube_mesh,
                color=bone_color,
                smooth_shading=True,
                name="bones",
                render=False,
            )
            self._apply_pbr(
                actor,
                metallic=BONE_METALLIC,
                roughness=BONE_ROUGHNESS,
                specular=0.42,
                specular_power=48.0,
            )
            self._actors["bones"] = actor

        if self._joint_pts:
            (
                self._joint_mesh,
                self._joint_template_pts,
                self._joint_template_faces,
                self._joint_points_per_sphere,
            ) = self._make_joint_mesh(self._joint_pts, self._joint_radius)
            unique = set(self._joint_colors)
            use_rgb = len(unique) > 1
            if use_rgb:
                n = self._joint_points_per_sphere
                rgb = np.zeros((self._joint_mesh.n_points, 3), dtype=np.uint8)
                for index, color in enumerate(self._joint_colors):
                    byte = (
                        int(np.clip(color[0] * 255, 0, 255)),
                        int(np.clip(color[1] * 255, 0, 255)),
                        int(np.clip(color[2] * 255, 0, 255)),
                    )
                    rgb[index * n : (index + 1) * n] = byte
                self._joint_mesh["RGB"] = rgb
                actor = self._plotter.add_mesh(
                    self._joint_mesh,
                    scalars="RGB",
                    rgb=True,
                    smooth_shading=True,
                    name="joints",
                    render=False,
                )
            else:
                actor = self._plotter.add_mesh(
                    self._joint_mesh,
                    color=self._joint_colors[0],
                    smooth_shading=True,
                    name="joints",
                    render=False,
                )
            # Polished gold joint nodes.
            self._apply_pbr(
                actor,
                metallic=JOINT_METALLIC,
                roughness=JOINT_ROUGHNESS,
                specular=0.55,
                specular_power=64.0,
            )
            # Soft selection glow when Apple-blue joints are present.
            if any(c == self.theme.selected for c in self._joint_colors):
                try:
                    prop = actor.GetProperty()
                    prop.SetAmbient(0.22)
                    prop.SetDiffuse(0.78)
                except Exception:
                    pass
            self._actors["joints"] = actor

        if has_labels:
            points = np.asarray([pos for _, pos, _ in self._labels], dtype=float)
            names = [text for text, _, _ in self._labels]
            cloud = self._pv.PolyData(points)
            actor = self._plotter.add_point_labels(
                cloud,
                names,
                font_size=11,
                text_color=self.theme.label,
                shape=None,
                show_points=False,
                always_visible=True,
                name="labels",
                render=False,
            )
            self._actors["labels"] = actor
            self._labels.clear()

    def _update_skeleton_positions(self) -> None:
        assert self._plotter is not None
        if self._joint_mesh is not None and self._joint_template_pts is not None:
            n = self._joint_points_per_sphere
            radius = self._joint_radius
            template = self._joint_template_pts * radius
            centers = np.asarray(self._joint_pts, dtype=float)
            if centers.ndim == 1:
                centers = centers.reshape(1, 3)
            expected = len(centers) * self._joint_points_per_sphere
            if self._joint_mesh.n_points != expected:
                self._invalidate_skeleton_cache()
                self._skeleton_sig = None
                return
            points = (template[None, :, :] + centers[:, None, :]).reshape(-1, 3)
            self._joint_mesh.points = points
            self._joint_mesh.Modified()

        if (
            self._bone_line_mesh is not None
            and self._bone_tube_mesh is not None
            and self._bone_segment_count > 0
        ):
            points = self._bone_line_mesh.points
            for index, (start, end) in enumerate(self._bone_segs):
                offset = index * 2
                points[offset] = start
                points[offset + 1] = end
            self._bone_line_mesh.points = points
            self._bone_line_mesh.Modified()
            new_tube = self._bone_line_mesh.tube(
                radius=self._bone_tube_radius,
                n_sides=BONE_TUBE_SIDES,
                capping=True,
            )
            if new_tube.n_points == self._bone_tube_mesh.n_points:
                self._bone_tube_mesh.points = new_tube.points
                self._bone_tube_mesh.Modified()
            else:
                self._bone_tube_mesh.copy_from(new_tube)
                self._bone_tube_mesh.Modified()

        if self._labels:
            self._remove_actor("labels")
            points = np.asarray([pos for _, pos, _ in self._labels], dtype=float)
            names = [text for text, _, _ in self._labels]
            cloud = self._pv.PolyData(points)
            actor = self._plotter.add_point_labels(
                cloud,
                names,
                font_size=11,
                text_color=self.theme.label,
                shape=None,
                show_points=False,
                always_visible=True,
                name="labels",
                render=False,
            )
            self._actors["labels"] = actor
            self._labels.clear()

    def _make_joint_mesh(
        self,
        centers: Sequence[np.ndarray],
        radius: float,
    ) -> tuple[Any, np.ndarray, np.ndarray | None, int]:
        template = self._pv.Sphere(
            radius=radius,
            center=(0.0, 0.0, 0.0),
            theta_resolution=JOINT_SPHERE_RESOLUTION,
            phi_resolution=JOINT_SPHERE_RESOLUTION,
        )
        base_pts = np.asarray(template.points, dtype=float)
        n = int(template.n_points)
        spheres = [
            self._pv.Sphere(
                radius=radius,
                center=center,
                theta_resolution=JOINT_SPHERE_RESOLUTION,
                phi_resolution=JOINT_SPHERE_RESOLUTION,
            )
            for center in centers
        ]
        try:
            mesh = self._pv.merge(spheres)
        except Exception:
            mesh = spheres[0]
            for sphere in spheres[1:]:
                mesh = mesh.merge(sphere)
        return mesh, base_pts / max(radius, 1e-9), None, n

    def _make_bone_line_mesh(
        self,
        segments: Sequence[tuple[np.ndarray, np.ndarray]],
    ) -> tuple[Any, int]:
        points = np.zeros((len(segments) * 2, 3), dtype=float)
        lines: list[int] = []
        for index, (start, end) in enumerate(segments):
            offset = index * 2
            points[offset] = start
            points[offset + 1] = end
            lines.extend([2, offset, offset + 1])
        mesh = self._pv.PolyData(points, lines=np.asarray(lines, dtype=np.int64))
        return mesh, len(segments)

    def _apply_camera(self, camera: CameraState) -> None:
        assert self._plotter is not None
        self._plotter.camera.position = camera.eye
        self._plotter.camera.focal_point = camera.look_at
        self._plotter.camera.up = camera.up
        self._plotter.camera.view_angle = camera.fov_deg
        self._plotter.camera.clipping_range = (camera.near, camera.far)


def create_default_renderer(
    prefer: str = "auto",
    theme: Theme | None = None,
    *,
    off_screen: bool = False,
) -> Renderer:
    """Factory: prefer PyVista studio renderer."""
    prefer = prefer.lower()
    if prefer == "null":
        return NullRenderer(theme=theme)
    if prefer in {"pyvista", "vtk", "auto", "open3d", "matplotlib"}:
        try:
            return PyVistaRenderer(theme=theme, off_screen=off_screen)
        except RendererError:
            if prefer == "auto":
                logger.warning("PyVista unavailable; using NullRenderer")
                return NullRenderer(theme=theme)
            raise
    return NullRenderer(theme=theme)
