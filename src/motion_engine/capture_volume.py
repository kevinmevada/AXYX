"""
Capture volume — floor plane A-B-C-D for clinical camera framing.

Walking direction is AB → DC (far edge toward near edge). Corners:

        A ---------------- B
       /                  /
      /      (walk)      /
     D ---------------- C
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
from numpy.typing import NDArray

Vec3 = tuple[float, float, float]
FloatArray = NDArray[np.floating]


def _as_xy(v: Sequence[float]) -> np.ndarray:
    return np.asarray(v, dtype=float)[:2].copy()


def _normalize_xy(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    if n < 1e-12:
        return np.array([0.0, 1.0], dtype=float)
    return v / n


@dataclass(frozen=True, slots=True)
class CaptureVolume:
    """Lab floor rectangle used as the camera reference geometry."""

    A: Vec3
    B: Vec3
    C: Vec3
    D: Vec3
    floor_z: float
    subject_height: float

    @classmethod
    def from_motion(
        cls,
        points: Sequence[Sequence[float]],
        *,
        floor_z: float,
        subject_height: float | None = None,
        walk_hint: Sequence[float] | None = None,
        padding: float = 1.35,
        min_half_extent: float = 800.0,
    ) -> CaptureVolume:
        """Build A-B-C-D from motion XYZ. Walk = AB → DC when hint/PCA available."""
        arr = np.asarray(points, dtype=float)
        if arr.size == 0:
            z = float(floor_z)
            h = float(subject_height or 1700.0)
            half = min_half_extent
            return cls(
                A=(-half, half, z),
                B=(half, half, z),
                C=(half, -half, z),
                D=(-half, -half, z),
                floor_z=z,
                subject_height=h,
            )
        if arr.ndim == 1:
            arr = arr.reshape(1, 3)

        xy = arr[:, :2]
        center = 0.5 * (xy.min(axis=0) + xy.max(axis=0))
        span = np.maximum(xy.max(axis=0) - xy.min(axis=0), 1.0)
        half_w = float(max(0.5 * span[0] * padding, min_half_extent * 0.5))
        half_d = float(max(0.5 * span[1] * padding, min_half_extent * 0.5))

        if walk_hint is not None:
            walk = _normalize_xy(_as_xy(walk_hint))
        else:
            walk = _infer_walk_xy(arr)

        # Right when facing walk (Z-up): R = up × walk → (−wy, wx).
        right = np.array([-walk[1], walk[0]], dtype=float)
        right = _normalize_xy(right)

        # Use isotropic half-extent from diagonal so both edges scale together.
        half_diag = 0.5 * float(np.linalg.norm([span[0], span[1]])) * padding
        half_diag = max(half_diag, min_half_extent)
        half_along = max(half_d, half_diag * 0.55)
        half_across = max(half_w, half_diag * 0.55)

        mid_ab = center - walk * half_along
        mid_dc = center + walk * half_along
        z = float(floor_z)
        a = (*((mid_ab - right * half_across).tolist()), z)
        b = (*((mid_ab + right * half_across).tolist()), z)
        c = (*((mid_dc + right * half_across).tolist()), z)
        d = (*((mid_dc - right * half_across).tolist()), z)

        z_pts = arr[:, 2]
        height = float(subject_height) if subject_height is not None else float(
            max(z_pts.max() - z, 1000.0)
        )
        return cls(A=a, B=b, C=c, D=d, floor_z=z, subject_height=max(height, 500.0))

    @property
    def center(self) -> Vec3:
        c = 0.25 * (
            np.asarray(self.A, dtype=float)
            + np.asarray(self.B, dtype=float)
            + np.asarray(self.C, dtype=float)
            + np.asarray(self.D, dtype=float)
        )
        return (float(c[0]), float(c[1]), float(self.floor_z))

    @property
    def mid_ab(self) -> Vec3:
        return _midpoint(self.A, self.B)

    @property
    def mid_bc(self) -> Vec3:
        return _midpoint(self.B, self.C)

    @property
    def mid_dc(self) -> Vec3:
        return _midpoint(self.D, self.C)

    @property
    def mid_da(self) -> Vec3:
        return _midpoint(self.D, self.A)

    @property
    def walk_direction(self) -> Vec3:
        """Unit XY from far (AB) toward near (DC)."""
        ab = np.asarray(self.mid_ab, dtype=float)
        dc = np.asarray(self.mid_dc, dtype=float)
        d = dc - ab
        d[2] = 0.0
        n = float(np.linalg.norm(d))
        if n < 1e-12:
            return (0.0, -1.0, 0.0)
        d = d / n
        return (float(d[0]), float(d[1]), 0.0)

    @property
    def diagonal(self) -> float:
        return float(
            np.linalg.norm(
                np.asarray(self.A, dtype=float) - np.asarray(self.C, dtype=float)
            )
        )

    @property
    def ground_size(self) -> float:
        """Axis-aligned span for drawing a covering floor plane."""
        corners = np.asarray([self.A, self.B, self.C, self.D], dtype=float)
        span = corners[:, :2].max(axis=0) - corners[:, :2].min(axis=0)
        return float(max(float(span[0]), float(span[1]), 1.0))

    def edge_outward(self, edge: str) -> Vec3:
        """Horizontal unit vector from volume center through an edge midpoint."""
        mid = {
            "ab": self.mid_ab,
            "bc": self.mid_bc,
            "dc": self.mid_dc,
            "da": self.mid_da,
        }[edge]
        c = np.asarray(self.center, dtype=float)
        m = np.asarray(mid, dtype=float)
        d = m - c
        d[2] = 0.0
        n = float(np.linalg.norm(d))
        if n < 1e-12:
            return (0.0, 1.0, 0.0)
        d = d / n
        return (float(d[0]), float(d[1]), 0.0)


def _midpoint(a: Vec3, b: Vec3) -> Vec3:
    m = 0.5 * (np.asarray(a, dtype=float) + np.asarray(b, dtype=float))
    return (float(m[0]), float(m[1]), float(m[2]))


def _infer_walk_xy(arr: FloatArray) -> np.ndarray:
    """Prefer first→last centroid drift; fall back to PCA major axis."""
    if arr.shape[0] >= 4:
        n = arr.shape[0]
        early = arr[: max(1, n // 10), :2].mean(axis=0)
        late = arr[-max(1, n // 10) :, :2].mean(axis=0)
        drift = late - early
        if float(np.linalg.norm(drift)) > 50.0:
            return _normalize_xy(drift)
    xy = arr[:, :2]
    centered = xy - xy.mean(axis=0)
    if centered.shape[0] < 2:
        return np.array([0.0, -1.0], dtype=float)
    _, _, vt = np.linalg.svd(centered, full_matrices=False)
    axis = vt[0]
    return _normalize_xy(axis)


__all__ = ["CaptureVolume"]
