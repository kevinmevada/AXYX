"""Serialize animation clips / tracks / markers / events / statistics."""

from __future__ import annotations

from typing import Any

import numpy as np

from motion_engine.rendering.avatar.animation.animation_clip import AnimationClip
from motion_engine.rendering.avatar.animation.animation_track import AnimationTrack
from motion_engine.rendering.avatar.animation.events import AnimationEvent
from motion_engine.rendering.avatar.animation.keyframe import Keyframe
from motion_engine.rendering.avatar.animation.markers import AnimationMarker
from motion_engine.rendering.avatar.animation.statistics import (
    AnimationStatistics,
    compute_clip_statistics,
)
from motion_engine.rendering.avatar.animation.types import InterpolationMode, TrackChannel


def _keyframe_to_dict(k: Keyframe) -> dict[str, Any]:
    d: dict[str, Any] = {"time": k.time, "metadata": dict(k.metadata)}
    if k.translation is not None:
        d["translation"] = list(k.translation)
    if k.rotation_xyzw is not None:
        d["rotation_xyzw"] = list(k.rotation_xyzw)
    if k.scale is not None:
        d["scale"] = list(k.scale)
    return d


def export_track(track: AnimationTrack) -> dict[str, Any]:
    return {
        "bone_name": track.bone_name,
        "channel": track.channel.name,
        "interpolation": track.interpolation.name,
        "keyframes": [_keyframe_to_dict(k) for k in track.keyframes],
        "metadata": dict(track.metadata),
    }


def export_clip(clip: AnimationClip) -> dict[str, Any]:
    return {
        "name": clip.name,
        "duration": clip.duration,
        "fps": clip.fps,
        "tracks": [export_track(t) for t in clip.tracks],
        "markers": [
            {"name": m.name, "time": m.time, "metadata": dict(m.metadata)} for m in clip.markers
        ],
        "events": [
            {"name": e.name, "time": e.time, "payload": dict(e.payload)} for e in clip.events
        ],
        "metadata": dict(clip.metadata),
        "statistics": compute_clip_statistics(clip).to_dict(),
    }


def export_statistics(stats: AnimationStatistics) -> dict[str, Any]:
    return stats.to_dict()


def export_markers(clip: AnimationClip) -> list[dict[str, Any]]:
    return [{"name": m.name, "time": m.time, "metadata": dict(m.metadata)} for m in clip.markers]


def export_events(clip: AnimationClip) -> list[dict[str, Any]]:
    return [{"name": e.name, "time": e.time, "payload": dict(e.payload)} for e in clip.events]


def import_clip(data: dict[str, Any]) -> AnimationClip:
    tracks = []
    for td in data.get("tracks", []):
        keys = []
        for kd in td.get("keyframes", []):
            keys.append(
                Keyframe(
                    time=float(kd["time"]),
                    translation=tuple(kd["translation"]) if "translation" in kd else None,
                    rotation_xyzw=tuple(kd["rotation_xyzw"]) if "rotation_xyzw" in kd else None,
                    scale=tuple(kd["scale"]) if "scale" in kd else None,
                    metadata=kd.get("metadata") or {},
                )
            )
        tracks.append(
            AnimationTrack(
                bone_name=str(td["bone_name"]),
                channel=TrackChannel[str(td.get("channel", "TRANSFORM"))],
                keyframes=tuple(keys),
                interpolation=InterpolationMode[str(td.get("interpolation", "LINEAR"))],
                metadata=td.get("metadata") or {},
            )
        )
    markers = tuple(
        AnimationMarker(name=m["name"], time=float(m["time"]), metadata=m.get("metadata") or {})
        for m in data.get("markers", [])
    )
    events = tuple(
        AnimationEvent(name=e["name"], time=float(e["time"]), payload=e.get("payload") or {})
        for e in data.get("events", [])
    )
    return AnimationClip(
        name=str(data.get("name", "clip")),
        duration=float(data.get("duration", 0.0)),
        tracks=tuple(tracks),
        markers=markers,
        events=events,
        fps=float(data.get("fps", 30.0)),
        metadata=data.get("metadata") or {},
    )


__all__ = [
    "export_clip",
    "export_track",
    "export_statistics",
    "export_markers",
    "export_events",
    "import_clip",
]
