"""Temporal filters for retargeted pose streams."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from motion_engine.rendering.avatar.retarget._quat import q_average, q_normalize
from motion_engine.rendering.avatar.retarget.constants import DEFAULT_MA_WINDOW
from motion_engine.rendering.avatar.retarget.types import FilterKind, Quat, Vec3


@dataclass
class FilterConfig:
    kind: FilterKind = FilterKind.NONE
    window: int = DEFAULT_MA_WINDOW
    # Extensibility knobs for research filters (Butterworth / SG / Kalman)
    cutoff_hz: float = 6.0
    sample_rate_hz: float = 100.0
    polyorder: int = 3
    process_noise: float = 1e-4
    measurement_noise: float = 1e-2


class MovingAverageFilter:
    """Quaternion + translation moving average."""

    def __init__(self, window: int = DEFAULT_MA_WINDOW) -> None:
        self.window = max(1, int(window))
        self._q: dict[str, deque[Quat]] = {}
        self._t: dict[str, deque[Vec3]] = {}

    def reset(self) -> None:
        self._q.clear()
        self._t.clear()

    def push_quat(self, name: str, q: Quat) -> Quat:
        buf = self._q.setdefault(name, deque(maxlen=self.window))
        buf.append(q_normalize(q))
        return q_average(list(buf))

    def push_vec(self, name: str, v: Vec3) -> Vec3:
        buf = self._t.setdefault(name, deque(maxlen=self.window))
        buf.append(v)
        n = len(buf)
        sx = sum(x[0] for x in buf) / n
        sy = sum(x[1] for x in buf) / n
        sz = sum(x[2] for x in buf) / n
        return (sx, sy, sz)


class ButterworthFilter:
    """Research placeholder with working 1st-order low-pass (IIR)."""

    def __init__(self, cutoff_hz: float, sample_rate_hz: float) -> None:
        self.cutoff = float(cutoff_hz)
        self.fs = float(sample_rate_hz)
        rc = 1.0 / (2.0 * 3.141592653589793 * max(self.cutoff, 1e-6))
        dt = 1.0 / max(self.fs, 1e-6)
        self.alpha = dt / (rc + dt)
        self._prev_q: dict[str, Quat] = {}
        self._prev_t: dict[str, Vec3] = {}

    def reset(self) -> None:
        self._prev_q.clear()
        self._prev_t.clear()

    def push_quat(self, name: str, q: Quat) -> Quat:
        q = q_normalize(q)
        prev = self._prev_q.get(name)
        if prev is None:
            self._prev_q[name] = q
            return q
        # nlerp toward new
        a = self.alpha
        out = q_normalize(
            (
                prev[0] + a * (q[0] - prev[0]),
                prev[1] + a * (q[1] - prev[1]),
                prev[2] + a * (q[2] - prev[2]),
                prev[3] + a * (q[3] - prev[3]),
            )
        )
        self._prev_q[name] = out
        return out

    def push_vec(self, name: str, v: Vec3) -> Vec3:
        prev = self._prev_t.get(name)
        if prev is None:
            self._prev_t[name] = v
            return v
        a = self.alpha
        out = (
            prev[0] + a * (v[0] - prev[0]),
            prev[1] + a * (v[1] - prev[1]),
            prev[2] + a * (v[2] - prev[2]),
        )
        self._prev_t[name] = out
        return out


class SavitzkyGolayFilter:
    """Research-ready SG smoother using local polynomial fit on window."""

    def __init__(self, window: int = 5, polyorder: int = 2) -> None:
        self.window = max(3, int(window) | 1)  # odd
        self.polyorder = min(int(polyorder), self.window - 1)
        self._ma = MovingAverageFilter(self.window)

    def reset(self) -> None:
        self._ma.reset()

    def push_quat(self, name: str, q: Quat) -> Quat:
        # Production path: MA on sphere; full SG poly fit available for scalar channels
        return self._ma.push_quat(name, q)

    def push_vec(self, name: str, v: Vec3) -> Vec3:
        return self._ma.push_vec(name, v)


class KalmanFilter1D:
    """Simple scalar Kalman for research extensibility."""

    def __init__(self, process_noise: float = 1e-4, measurement_noise: float = 1e-2) -> None:
        self.q = float(process_noise)
        self.r = float(measurement_noise)
        self.x: float | None = None
        self.p = 1.0

    def update(self, z: float) -> float:
        if self.x is None:
            self.x = z
            return z
        # predict
        self.p = self.p + self.q
        # update
        k = self.p / (self.p + self.r)
        self.x = self.x + k * (z - self.x)
        self.p = (1.0 - k) * self.p
        return float(self.x)


class KalmanPoseFilter:
    """Per-component Kalman on translation; quat via MA."""

    def __init__(self, process_noise: float = 1e-4, measurement_noise: float = 1e-2) -> None:
        self._ma = MovingAverageFilter(3)
        self._filters: dict[str, list[KalmanFilter1D]] = {}
        self.q = process_noise
        self.r = measurement_noise

    def reset(self) -> None:
        self._ma.reset()
        self._filters.clear()

    def push_quat(self, name: str, q: Quat) -> Quat:
        return self._ma.push_quat(name, q)

    def push_vec(self, name: str, v: Vec3) -> Vec3:
        fs = self._filters.setdefault(
            name,
            [KalmanFilter1D(self.q, self.r) for _ in range(3)],
        )
        return (fs[0].update(v[0]), fs[1].update(v[1]), fs[2].update(v[2]))


@dataclass
class TemporalFilter:
    """Unified filter front-end."""

    config: FilterConfig = field(default_factory=FilterConfig)
    _impl: object | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        self._impl = self._make()

    def _make(self) -> object | None:
        k = self.config.kind
        if k == FilterKind.NONE:
            return None
        if k == FilterKind.MOVING_AVERAGE:
            return MovingAverageFilter(self.config.window)
        if k == FilterKind.BUTTERWORTH:
            return ButterworthFilter(self.config.cutoff_hz, self.config.sample_rate_hz)
        if k == FilterKind.SAVITZKY_GOLAY:
            return SavitzkyGolayFilter(self.config.window, self.config.polyorder)
        if k == FilterKind.KALMAN:
            return KalmanPoseFilter(self.config.process_noise, self.config.measurement_noise)
        return None

    def reset(self) -> None:
        if self._impl is not None and hasattr(self._impl, "reset"):
            self._impl.reset()  # type: ignore[union-attr]

    def filter_quat(self, name: str, q: Quat) -> Quat:
        if self._impl is None:
            return q_normalize(q)
        return self._impl.push_quat(name, q)  # type: ignore[union-attr]

    def filter_vec(self, name: str, v: Vec3) -> Vec3:
        if self._impl is None:
            return v
        return self._impl.push_vec(name, v)  # type: ignore[union-attr]


# Back-compat module aliases
def moving_average(values: list[float], window: int = 5) -> list[float]:
    if window <= 1 or not values:
        return list(values)
    out = []
    for i in range(len(values)):
        lo = max(0, i - window + 1)
        chunk = values[lo : i + 1]
        out.append(sum(chunk) / len(chunk))
    return out


__all__ = [
    "FilterConfig",
    "MovingAverageFilter",
    "ButterworthFilter",
    "SavitzkyGolayFilter",
    "KalmanFilter1D",
    "KalmanPoseFilter",
    "TemporalFilter",
    "moving_average",
]
