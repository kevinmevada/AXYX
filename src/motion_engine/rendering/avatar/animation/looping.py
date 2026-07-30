"""Loop / wrap helpers for timeline sampling."""

from __future__ import annotations

from motion_engine.rendering.avatar.animation.types import LoopMode


def wrap_time(time: float, duration: float, mode: LoopMode) -> tuple[float, bool]:
    """Map ``time`` into ``[0, duration]`` according to ``mode``.

    Returns ``(wrapped_time, finished)`` where ``finished`` is True when
    ``ONCE`` mode has passed the end (clamped).
    """
    duration = float(duration)
    time = float(time)
    if duration <= 1e-15:
        return 0.0, True
    if mode is LoopMode.ONCE:
        if time < 0.0:
            return 0.0, False
        if time >= duration:
            return duration, True
        return time, False
    if mode is LoopMode.LOOP:
        # Python modulo for negatives.
        return time % duration, False
    # PING_PONG
    cycle = duration * 2.0
    u = time % cycle
    if u < 0.0:
        u += cycle
    if u <= duration:
        return u, False
    return cycle - u, False


__all__ = ["wrap_time"]
