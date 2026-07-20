"""Export KILI bone hierarchy JSON only."""
from __future__ import annotations

import json
import os
from pathlib import Path

import ufbx

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "KILI" / "cache"
DRIVE = [
    "root",
    "pelvis",
    "spine_01",
    "spine_02",
    "spine_03",
    "spine_04",
    "spine_05",
    "neck_01",
    "neck_02",
    "head",
    "clavicle_l",
    "upperarm_l",
    "lowerarm_l",
    "hand_l",
    "clavicle_r",
    "upperarm_r",
    "lowerarm_r",
    "hand_r",
    "thigh_l",
    "calf_l",
    "foot_l",
    "ball_l",
    "thigh_r",
    "calf_r",
    "foot_r",
    "ball_r",
]


def main() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    scene = ufbx.load_file(str(ROOT / "KILI" / "SKM_Kili_BodyMesh.FBX"))
    nodes = {}
    for node in scene.nodes:
        parent = node.parent.name if node.parent is not None else None
        t = node.local_transform.translation
        nodes[node.name] = {
            "parent": parent,
            "translation": [float(t.x), float(t.y), float(t.z)],
            "is_bone": node.bone is not None,
        }
    # Also capture bind world for drive bones from first mesh skin
    mesh = scene.meshes[3]
    skin = mesh.skin_deformers[0]
    bind = {}
    for cluster in skin.clusters:
        if cluster.bone_node is None:
            continue
        name = cluster.bone_node.name
        if name not in DRIVE:
            continue
        m = cluster.bone_node.geometry_to_world
        c0, c1, c2, c3 = m.c0, m.c1, m.c2, m.c3
        bind[name] = [
            [c0.x, c1.x, c2.x, c3.x],
            [c0.y, c1.y, c2.y, c3.y],
            [c0.z, c1.z, c2.z, c3.z],
            [0.0, 0.0, 0.0, 1.0],
        ]
    payload = {
        "nodes": nodes,
        "drive_bones": {n: nodes[n] for n in DRIVE if n in nodes},
        "drive_order": DRIVE,
        "drive_bind_world": bind,
    }
    path = CACHE / "skeleton.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {path} nodes={len(nodes)} drive={len(payload['drive_bones'])}", flush=True)
    os._exit(0)


if __name__ == "__main__":
    main()
