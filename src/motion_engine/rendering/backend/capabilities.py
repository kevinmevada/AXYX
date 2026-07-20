"""Backend capability flags."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BackendCapabilities:
    """Capability flags reported by a render backend."""

    supports_pbr: bool = True
    supports_shadows: bool = True
    supports_msaa: bool = True
    supports_hdri: bool = True
    supports_skinning: bool = False
    supports_compute: bool = False
    max_lights: int = 8
    name: str = "unknown"


PYVISTA_CAPABILITIES = BackendCapabilities(
    supports_pbr=True,
    supports_shadows=True,
    supports_msaa=True,
    supports_hdri=True,
    supports_skinning=False,
    supports_compute=False,
    max_lights=8,
    name="pyvista",
)

NULL_CAPABILITIES = BackendCapabilities(
    supports_pbr=False,
    supports_shadows=False,
    supports_msaa=False,
    supports_hdri=False,
    supports_skinning=False,
    supports_compute=False,
    max_lights=0,
    name="null",
)


__all__ = ["BackendCapabilities", "PYVISTA_CAPABILITIES", "NULL_CAPABILITIES"]
