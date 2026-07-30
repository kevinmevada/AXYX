"""Internal glTF / GLB animation loader."""

from __future__ import annotations

import json
import struct
from pathlib import Path

import numpy as np

from motion_engine.rendering.avatar.animation.animation_clip import AnimationClip
from motion_engine.rendering.avatar.animation.animation_track import AnimationTrack
from motion_engine.rendering.avatar.animation.exceptions import AnimationFactoryError
from motion_engine.rendering.avatar.animation.keyframe import Keyframe
from motion_engine.rendering.avatar.animation.types import InterpolationMode, TrackChannel


def _load_gltf_document(path: Path) -> tuple[dict, bytes | None]:
    if path.suffix.lower() == ".glb":
        raw = path.read_bytes()
        magic, version, length = struct.unpack_from("<III", raw, 0)
        if magic != 0x46546C67:
            raise AnimationFactoryError("Not a GLB file", code="ANIM_GLB_MAGIC")
        offset = 12
        json_chunk = None
        bin_chunk = None
        while offset + 8 <= length:
            chunk_len, chunk_type = struct.unpack_from("<II", raw, offset)
            offset += 8
            data = raw[offset : offset + chunk_len]
            offset += chunk_len
            if chunk_type == 0x4E4F534A:
                json_chunk = data
            elif chunk_type == 0x004E4942:
                bin_chunk = data
        if json_chunk is None:
            raise AnimationFactoryError("GLB missing JSON", code="ANIM_GLB_JSON")
        return json.loads(json_chunk.decode("utf-8")), bin_chunk
    doc = json.loads(path.read_text(encoding="utf-8"))
    bin_blob = None
    for buf in doc.get("buffers", []):
        uri = buf.get("uri")
        if uri and not uri.startswith("data:"):
            bin_blob = (path.parent / uri).read_bytes()
            break
    return doc, bin_blob


def _accessor_numpy(doc: dict, blob: bytes | None, index: int) -> np.ndarray:
    acc = doc["accessors"][index]
    bv = doc["bufferViews"][acc["bufferView"]]
    if blob is None:
        raise AnimationFactoryError("Missing BIN buffer", code="ANIM_GLTF_BIN")
    offset = int(bv.get("byteOffset", 0)) + int(acc.get("byteOffset", 0))
    count = int(acc["count"])
    typ = acc["type"]
    comp = int(acc["componentType"])
    fmt = {5126: "f", 5123: "H", 5121: "B", 5125: "I", 5120: "b", 5122: "h"}[comp]
    ncomp = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}[typ]
    size = struct.calcsize("<" + fmt) * ncomp * count
    data = np.frombuffer(blob, dtype="<" + fmt, count=ncomp * count, offset=offset)
    return data.reshape(count, ncomp).astype(np.float64)


def load_gltf_animation(path: Path, *, animation_index: int = 0) -> AnimationClip:
    doc, blob = _load_gltf_document(path)
    anims = doc.get("animations") or []
    if not anims:
        raise AnimationFactoryError(f"No animations in {path}", code="ANIM_GLTF_EMPTY")
    if animation_index < 0 or animation_index >= len(anims):
        raise AnimationFactoryError("animation_index out of range", code="ANIM_GLTF_INDEX")
    anim = anims[animation_index]
    nodes = doc.get("nodes") or []
    tracks: list[AnimationTrack] = []
    duration = 0.0
    for ch in anim.get("channels", []):
        path_str = ch.get("target", {}).get("path")
        node_i = ch.get("target", {}).get("node")
        samp_i = ch.get("sampler")
        if path_str is None or node_i is None or samp_i is None:
            continue
        node = nodes[int(node_i)]
        bone = str(node.get("name") or f"node_{node_i}")
        samp = anim["samplers"][int(samp_i)]
        times = _accessor_numpy(doc, blob, int(samp["input"])).reshape(-1)
        values = _accessor_numpy(doc, blob, int(samp["output"]))
        duration = max(duration, float(times[-1]) if len(times) else 0.0)
        interp = str(samp.get("interpolation", "LINEAR")).upper()
        mode = {
            "STEP": InterpolationMode.STEP,
            "LINEAR": InterpolationMode.LINEAR,
            "CUBICSPLINE": InterpolationMode.CUBIC,
        }.get(interp, InterpolationMode.LINEAR)
        keys: list[Keyframe] = []
        if path_str == "translation":
            channel = TrackChannel.TRANSLATION
            for i, t in enumerate(times):
                v = values[i]
                keys.append(
                    Keyframe(time=float(t), translation=(float(v[0]), float(v[1]), float(v[2])))
                )
        elif path_str == "rotation":
            channel = TrackChannel.ROTATION
            for i, t in enumerate(times):
                v = values[i]
                # glTF is xyzw
                keys.append(
                    Keyframe(
                        time=float(t),
                        rotation_xyzw=(float(v[0]), float(v[1]), float(v[2]), float(v[3])),
                    )
                )
        elif path_str == "scale":
            channel = TrackChannel.SCALE
            for i, t in enumerate(times):
                v = values[i]
                keys.append(Keyframe(time=float(t), scale=(float(v[0]), float(v[1]), float(v[2]))))
        else:
            continue
        if keys:
            tracks.append(
                AnimationTrack(
                    bone_name=bone,
                    channel=channel,
                    keyframes=tuple(keys),
                    interpolation=mode,
                )
            )
    if not tracks:
        raise AnimationFactoryError(f"No TRS tracks in {path}", code="ANIM_GLTF_TRACKS")
    name = str(anim.get("name") or path.stem)
    clip = AnimationClip(name=name, duration=duration, tracks=tuple(tracks), metadata={"source": "gltf"})
    clip.validate()
    return clip
