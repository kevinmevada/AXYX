"""Preprocess KILI FBX + TGA assets into a runtime-safe cache.

ufbx can segfault on interpreter teardown after complex scenes, so this script
extracts bind-pose mesh/skin data into NumPy + JSON once, then exits.

Usage:
    venv311\\Scripts\\python.exe scripts\\preprocess_kili_assets.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
KILI = ROOT / "KILI"
CACHE = KILI / "cache"
BODY_FBX = KILI / "SKM_Kili_BodyMesh.FBX"
OUTFIT_FBX = KILI / "Kili_Outfits.FBX"

# Prefer LOD1 for interactive Studio (balance fidelity vs speed).
DEFAULT_LOD = 1

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
    """Convert ufbx 4x3 Matrix (c0..c3 as Vec3) to a 4x4 NumPy array."""
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


def _export_mesh_skin(scene, mesh, lod: int, out_stem: str) -> dict:
    import ufbx

    if not mesh.skin_deformers:
        raise RuntimeError(f"Mesh {mesh.name!r} has no skin deformer")
    skin = mesh.skin_deformers[0]
    clusters = list(skin.clusters)
    bone_names = [
        (c.bone_node.name if c.bone_node is not None else f"bone_{i}")
        for i, c in enumerate(clusters)
    ]

    n_verts = int(mesh.num_vertices)
    max_w = int(max(4, skin.max_weights_per_vertex))
    indices = np.zeros((n_verts, max_w), dtype=np.int32)
    weights = np.zeros((n_verts, max_w), dtype=np.float32)
    inv_bind = np.zeros((len(clusters), 4, 4), dtype=np.float64)
    bind_world = np.zeros((len(clusters), 4, 4), dtype=np.float64)

    for bi, cluster in enumerate(clusters):
        inv_bind[bi] = _mat4(cluster.geometry_to_bone)
        if cluster.bone_node is not None:
            bind_world[bi] = _mat4(cluster.bone_node.geometry_to_world)

    # Packed per-control-point skin weights from the deformer.
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
        p = ufbx.get_vertex_vec3(mesh.vertex_position, i)
        positions[i] = (p.x, p.y, p.z)
        if mesh.vertex_normal.exists:
            n = ufbx.get_vertex_vec3(mesh.vertex_normal, i)
            normals[i] = (n.x, n.y, n.z)
        if mesh.vertex_uv.exists:
            uv = ufbx.get_vertex_vec2(mesh.vertex_uv, i)
            uvs[i] = (uv.x, uv.y)

    faces: list[tuple[int, int, int]] = []
    for fi in range(int(mesh.num_faces)):
        face = mesh.faces[fi]
        idxs = [
            int(mesh.vertex_indices[face.index_begin + k])
            for k in range(int(face.num_indices))
        ]
        if len(idxs) < 3:
            continue
        for k in range(1, len(idxs) - 1):
            faces.append((idxs[0], idxs[k], idxs[k + 1]))
    faces_arr = np.asarray(faces, dtype=np.int32)

    npz_path = CACHE / f"{out_stem}_lod{lod}.npz"
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
    )
    return {
        "name": mesh.name,
        "lod": lod,
        "vertices": n_verts,
        "triangles": int(faces_arr.shape[0]),
        "bones": len(bone_names),
        "max_weights": max_w,
        "cache": str(npz_path.relative_to(ROOT)).replace("\\", "/"),
    }


def _export_hierarchy(scene) -> dict:
    nodes = {}
    for node in scene.nodes:
        parent = node.parent.name if node.parent is not None else None
        t = node.local_transform.translation
        nodes[node.name] = {
            "parent": parent,
            "translation": _vec3(t),
            "is_bone": node.bone is not None,
        }
    drive = {}
    for name in DRIVE_BONES:
        if name in nodes:
            drive[name] = nodes[name]
    return {"nodes": nodes, "drive_bones": drive, "drive_order": DRIVE_BONES}


def _downscale_textures() -> list[dict]:
    from PIL import Image

    tex_dir = CACHE / "textures"
    tex_dir.mkdir(parents=True, exist_ok=True)
    mapping = [
        ("T_Body_BC_VT.TGA", "body_bc.png", 2048),
        ("T_Body_N_VT.TGA", "body_n.png", 2048),
        ("T_Body_SRMF_VT.TGA", "body_srmf.png", 2048),
        ("T_Body_Scatter_VT.TGA", "body_scatter.png", 1024),
    ]
    out = []
    for src_name, dst_name, max_dim in mapping:
        src = KILI / src_name
        if not src.is_file():
            continue
        img = Image.open(src)
        img = img.convert("RGBA" if img.mode in ("RGBA", "LA") else "RGB")
        w, h = img.size
        scale = min(1.0, max_dim / float(max(w, h)))
        if scale < 1.0:
            img = img.resize(
                (max(1, int(w * scale)), max(1, int(h * scale))),
                Image.Resampling.LANCZOS,
            )
        dst = tex_dir / dst_name
        img.save(dst, optimize=True)
        out.append(
            {
                "source": src_name,
                "cache": str(dst.relative_to(ROOT)).replace("\\", "/"),
                "size": list(img.size),
            }
        )
        print(f"  texture {src_name} -> {dst.name} {img.size}")
    return out


def main() -> int:
    import ufbx

    if not BODY_FBX.is_file():
        print(f"Missing body FBX: {BODY_FBX}", file=sys.stderr)
        return 1

    CACHE.mkdir(parents=True, exist_ok=True)
    print("Loading body FBX…")
    body = ufbx.load_file(str(BODY_FBX))

    meshes_meta = []
    for mesh in body.meshes:
        name = mesh.name or ""
        lod = 0
        if "_LOD" in name:
            try:
                lod = int(name.split("_LOD")[-1])
            except ValueError:
                lod = 0
        print(f"Exporting {name} (LOD {lod})…")
        meta = _export_mesh_skin(body, mesh, lod, "body")
        meshes_meta.append(meta)

    hierarchy = _export_hierarchy(body)

    outfit_meta = None
    if OUTFIT_FBX.is_file():
        print("Loading outfit FBX…")
        outfit = ufbx.load_file(str(OUTFIT_FBX))
        outfit_meshes = []
        for i, mesh in enumerate(outfit.meshes):
            print(f"Exporting outfit mesh {mesh.name!r}…")
            try:
                outfit_meshes.append(
                    _export_mesh_skin(outfit, mesh, i, f"outfit_{i}")
                )
            except Exception as exc:  # noqa: BLE001
                print(f"  skip outfit mesh: {exc}")
        outfit_meta = {
            "meshes": outfit_meshes,
            "blend_shapes": int(len(outfit.blend_shapes)),
            "bones": int(len(outfit.bones)),
        }

    print("Downscaling textures…")
    textures = _downscale_textures()

    manifest = {
        "schema_version": "1.0.0",
        "name": "kili",
        "display_name": "Kili Digital Human",
        "source": {
            "body_fbx": "KILI/SKM_Kili_BodyMesh.FBX",
            "outfit_fbx": "KILI/Kili_Outfits.FBX",
            "exporter": "Unreal FBX mesh export",
        },
        "skeleton": {
            "style": "metahuman_ue5",
            "bone_count": int(len(body.bones)),
            "drive_bones": DRIVE_BONES,
            "hierarchy_cache": "KILI/cache/skeleton.json",
        },
        "meshes": {
            "body_lods": meshes_meta,
            "default_lod": DEFAULT_LOD,
            "outfit": outfit_meta,
        },
        "materials": {
            "pbr": {
                "base_color": "T_Body_BC_VT.TGA",
                "normal": "T_Body_N_VT.TGA",
                "srmf": "T_Body_SRMF_VT.TGA",
                "scatter": "T_Body_Scatter_VT.TGA",
                "srmf_packing": "Specular/Roughness/Metallic/AO (Unreal VT packed)",
            },
            "runtime_textures": textures,
        },
        "features": {
            "skinning": True,
            "lods": True,
            "blend_shapes": int(len(body.blend_shapes)) > 0,
            "hair": False,
            "physics_assets": False,
            "clothing_mesh": outfit_meta is not None,
            "cloth_simulation": False,
            "facial_morphs": False,
        },
        "notes": [
            "No morph targets / blend shapes in exported FBX.",
            "No separate hair assets.",
            "No Unreal PhysicsAsset; secondary motion not available from data.",
            "Outfit FBX provides clothing meshes skinned to the same skeleton.",
        ],
    }

    (CACHE / "skeleton.json").write_text(
        json.dumps(hierarchy, indent=2), encoding="utf-8"
    )
    (CACHE / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    (KILI / "ASSET_MANIFEST.yaml").write_text(
        _to_yamlish(manifest), encoding="utf-8"
    )
    print(f"Wrote {CACHE / 'manifest.json'}")
    print("Done. (process may exit with ufbx teardown noise — cache is valid)")
    # Force hard exit to avoid ufbx GC crash masking success.
    sys.stdout.flush()
    os_exit = getattr(__import__("os"), "_exit")
    os_exit(0)
    return 0


def _to_yamlish(obj, indent: int = 0) -> str:
    """Minimal YAML emitter for the human-readable manifest."""
    sp = "  " * indent
    if isinstance(obj, dict):
        lines = []
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                lines.append(f"{sp}{k}:")
                lines.append(_to_yamlish(v, indent + 1))
            else:
                lines.append(f"{sp}{k}: {_yaml_scalar(v)}")
        return "\n".join(lines)
    if isinstance(obj, list):
        lines = []
        for item in obj:
            if isinstance(item, (dict, list)):
                lines.append(f"{sp}-")
                lines.append(_to_yamlish(item, indent + 1))
            else:
                lines.append(f"{sp}- {_yaml_scalar(item)}")
        return "\n".join(lines)
    return f"{sp}{_yaml_scalar(obj)}"


def _yaml_scalar(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if v is None:
        return "null"
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v).replace('"', '\\"')
    return f'"{s}"'


if __name__ == "__main__":
    raise SystemExit(main())
