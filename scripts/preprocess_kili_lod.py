"""Preprocess one KILI body LOD into NumPy cache (crash-safe single-shot).

Usage:
    venv311\\Scripts\\python.exe scripts\\preprocess_kili_lod.py 1
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import ufbx

ROOT = Path(__file__).resolve().parents[1]
KILI = ROOT / "KILI"
CACHE = KILI / "cache"
BODY_FBX = KILI / "SKM_Kili_BodyMesh.FBX"

DRIVE_BONES = [
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


def _mat4(m) -> np.ndarray:
    c0, c1, c2, c3 = m.c0, m.c1, m.c2, m.c3
    return np.array(
        [
            [c0.x, c1.x, c2.x, c3.x],
            [c0.y, c1.y, c2.y, c3.y],
            [c0.z, c1.z, c2.z, c3.z],
            [0.0, 0.0, 0.0, 1.0],
        ],
        dtype=np.float64,
    )


def _vec3(v) -> list[float]:
    return [float(v.x), float(v.y), float(v.z)]


def export_lod(lod: int) -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    print(f"Loading FBX for LOD {lod}…", flush=True)
    scene = ufbx.load_file(str(BODY_FBX))
    target = None
    for mesh in scene.meshes:
        name = mesh.name or ""
        mesh_lod = -1
        if "_LOD" in name:
            try:
                mesh_lod = int(name.split("_LOD")[-1])
            except ValueError:
                mesh_lod = -1
        if mesh_lod == lod:
            target = mesh
            break
    if target is None:
        raise SystemExit(f"LOD {lod} not found. Available: {[m.name for m in scene.meshes]}")

    skin = target.skin_deformers[0]
    clusters = list(skin.clusters)
    bone_names = [
        (c.bone_node.name if c.bone_node is not None else f"bone_{i}")
        for i, c in enumerate(clusters)
    ]
    name_to_index = {n: i for i, n in enumerate(bone_names)}
    bone_parents = np.full(len(clusters), -1, dtype=np.int32)
    for i, cluster in enumerate(clusters):
        node = cluster.bone_node
        if node is not None and node.parent is not None:
            pname = node.parent.name
            if pname in name_to_index:
                bone_parents[i] = name_to_index[pname]
    n_verts = int(target.num_vertices)
    max_w = int(max(4, skin.max_weights_per_vertex))
    indices = np.zeros((n_verts, max_w), dtype=np.int32)
    weights = np.zeros((n_verts, max_w), dtype=np.float32)
    inv_bind = np.zeros((len(clusters), 4, 4), dtype=np.float64)
    bind_world = np.zeros((len(clusters), 4, 4), dtype=np.float64)

    for bi, cluster in enumerate(clusters):
        inv_bind[bi] = _mat4(cluster.geometry_to_bone)
        if cluster.bone_node is not None:
            bind_world[bi] = _mat4(cluster.bone_node.geometry_to_world)

    for vi in range(n_verts):
        sv = skin.vertices[vi]
        begin = int(sv.weight_begin)
        nw = int(sv.num_weights)
        pairs = []
        for k in range(nw):
            sw = skin.weights[begin + k]
            pairs.append((float(sw.weight), int(sw.cluster_index)))
        pairs.sort(reverse=True)
        for slot, (w, bi) in enumerate(pairs[:max_w]):
            indices[vi, slot] = bi
            weights[vi, slot] = w
    wsum = weights.sum(axis=1, keepdims=True)
    wsum[wsum < 1e-8] = 1.0
    weights = (weights / wsum).astype(np.float32)

    positions = np.zeros((n_verts, 3), dtype=np.float32)
    normals = np.zeros((n_verts, 3), dtype=np.float32)
    uvs = np.zeros((n_verts, 2), dtype=np.float32)
    for i in range(n_verts):
        p = ufbx.get_vertex_vec3(target.vertex_position, i)
        positions[i] = (p.x, p.y, p.z)
        if target.vertex_normal.exists:
            n = ufbx.get_vertex_vec3(target.vertex_normal, i)
            normals[i] = (n.x, n.y, n.z)
        if target.vertex_uv.exists:
            uv = ufbx.get_vertex_vec2(target.vertex_uv, i)
            uvs[i] = (uv.x, uv.y)

    faces: list[tuple[int, int, int]] = []
    for fi in range(int(target.num_faces)):
        face = target.faces[fi]
        idxs = [
            int(target.vertex_indices[face.index_begin + k])
            for k in range(int(face.num_indices))
        ]
        if len(idxs) < 3:
            continue
        for k in range(1, len(idxs) - 1):
            faces.append((idxs[0], idxs[k], idxs[k + 1]))
    faces_arr = np.asarray(faces, dtype=np.int32)

    npz_path = CACHE / f"body_lod{lod}.npz"
    np.savez_compressed(
        npz_path,
        positions=positions,
        normals=normals,
        uvs=uvs,
        faces=faces_arr,
        bone_indices=indices,
        bone_weights=weights,
        inv_bind=inv_bind,
        bind_world=bind_world,
        bone_names=np.asarray(bone_names),
        bone_parents=bone_parents,
    )
    print(
        f"Wrote {npz_path.name}: verts={n_verts} tris={faces_arr.shape[0]} bones={len(bone_names)}",
        flush=True,
    )

    # Hierarchy once
    skel_path = CACHE / "skeleton.json"
    if not skel_path.is_file():
        nodes = {}
        for node in scene.nodes:
            parent = node.parent.name if node.parent is not None else None
            nodes[node.name] = {
                "parent": parent,
                "translation": _vec3(node.local_transform.translation),
                "is_bone": node.bone is not None,
            }
        drive = {n: nodes[n] for n in DRIVE_BONES if n in nodes}
        skel_path.write_text(
            json.dumps(
                {"nodes": nodes, "drive_bones": drive, "drive_order": DRIVE_BONES},
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"Wrote {skel_path.name}", flush=True)

    print("OK", flush=True)
    os._exit(0)


if __name__ == "__main__":
    lod = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    export_lod(lod)
