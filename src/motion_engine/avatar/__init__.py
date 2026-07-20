"""Avatar-independent rendering layer for AXYX.

Motion engine poses feed an :class:`AvatarBackend`. Backends never leak into
loader / skeleton / AI code. Metallic stick-figure remains the fallback.
"""

from __future__ import annotations

from motion_engine.avatar.base import AvatarBackend, AvatarInfo, NullAvatar
from motion_engine.avatar.registry import AvatarRegistry, create_default_avatar

__all__ = [
    "AvatarBackend",
    "AvatarInfo",
    "AvatarRegistry",
    "NullAvatar",
    "create_default_avatar",
]
