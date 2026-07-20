"""
Unreal Engine 5 integration layer.

Motion Engine never depends on Unreal. This package prepares Unreal-ready
animation packages from :class:`~motion_engine.animation_clip.AnimationClip`.
"""

from __future__ import annotations

from motion_engine.unreal.pipeline import UnrealPipeline
from motion_engine.unreal.unreal_exporter import UnrealExporter, UnrealExportPackage

__all__ = ["UnrealExporter", "UnrealExportPackage", "UnrealPipeline"]
