"""Load a skinned FBX into M1 mesh + skeleton DTOs via ``ufbx``.

Note: some ``ufbx`` builds crash when reading ``Node.parent`` after other cluster
accesses. Parent links are therefore inferred from Unreal/MetaHuman-style names
(and optional explicit overrides), while bind/IBM/weights come from the FBX.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from motion_engine.rendering.avatar.models.mesh import (
    MeshData,
    SubMesh,
    compute_bounds,
)
from motion_engine.rendering.avatar.models.skeleton import AvatarSkeleton, BoneData

# Explicit parents for common UE5 / MetaHuman drive bones.
_UE_PARENT: dict[str, str | None] = {
    "root": None,
    "pelvis": "root",
    "spine_01": "pelvis",
    "spine_02": "spine_01",
    "spine_03": "spine_02",
    "spine_04": "spine_03",
    "spine_05": "spine_04",
    "neck_01": "spine_05",
    "neck_02": "neck_01",
    "head": "neck_02",
    "clavicle_l": "spine_05",
    "upperarm_l": "clavicle_l",
    "lowerarm_l": "upperarm_l",
    "hand_l": "lowerarm_l",
    "clavicle_r": "spine_05",
    "upperarm_r": "clavicle_r",
    "lowerarm_r": "upperarm_r",
    "hand_r": "lowerarm_r",
    "thigh_l": "pelvis",
    "calf_l": "thigh_l",
    "foot_l": "calf_l",
    "ball_l": "foot_l",
    "thigh_r": "pelvis",
    "calf_r": "thigh_r",
    "foot_r": "calf_r",
    "ball_r": "foot_r",
    "jaw": "head",
    "eye_l": "head",
    "eye_r": "head",
}


def _mat4(m) -> np.ndarray:
    """Convert ufbx ``Matrix`` (c0..c3 Vec3 columns) to a 4×4 affine."""
    out = np.eye(4, dtype=np.float64)
    for col, vec in enumerate((m.c0, m.c1, m.c2, m.c3)):
        out[0, col] = float(vec.x)
        out[1, col] = float(vec.y)
        out[2, col] = float(vec.z)
    return out


def _generate_normals(positions: np.ndarray, indices: np.ndarray) -> np.ndarray:
    normals = np.zeros_like(positions, dtype=np.float32)
    tris = indices.reshape(-1, 3)
    for i0, i1, i2 in tris:
        p0, p1, p2 = positions[i0], positions[i1], positions[i2]
        n = np.cross(p1 - p0, p2 - p0)
        normals[i0] += n
        normals[i1] += n
        normals[i2] += n
    lens = np.linalg.norm(normals, axis=1, keepdims=True)
    lens = np.maximum(lens, 1e-8)
    return (normals / lens).astype(np.float32)


def _infer_parent(name: str, known: set[str]) -> str | None:
    """Infer parent bone name for Unreal-style skeletal names."""
    if name in _UE_PARENT:
        p = _UE_PARENT[name]
        # Fall back through missing intermediate spines (some assets stop at spine_03).
        while p is not None and p not in known and p in _UE_PARENT:
            p = _UE_PARENT[p]
        if p is None or p in known:
            return p
        # spine_05 missing → try spine_03 / spine_04 etc.
        if name in {"clavicle_l", "clavicle_r", "neck_01"}:
            for cand in ("spine_05", "spine_04", "spine_03", "spine_02", "spine_01"):
                if cand in known:
                    return cand
        return None

    # twist / corrective: upperarm_twist_01_l → upperarm_l
    if "_twist_" in name:
        base = name.split("_twist_")[0]
        # upperarm_twist_01_l → need side suffix
        parts = name.split("_")
        side = parts[-1] if parts[-1] in {"l", "r"} else None
        if side and f"{base}_{side}" in known:
            return f"{base}_{side}"
        if base in known:
            return base

    # finger chain: index_03_l → index_02_l → index_01_l → hand_l
    for digit in ("thumb", "index", "middle", "ring", "pinky"):
        for side in ("l", "r"):
            for stage in (3, 2, 1):
                if name == f"{digit}_{stage:02d}_{side}":
                    if stage > 1:
                        prev = f"{digit}_{stage - 1:02d}_{side}"
                        if prev in known:
                            return prev
                    hand = f"hand_{side}"
                    return hand if hand in known else None
            if name == f"{digit}_01_{side}":
                hand = f"hand_{side}"
                return hand if hand in known else None

    # facial helpers → head
    for prefix in ("lip_", "eyebrow_", "eyelashes_"):
        if name.startswith(prefix):
            return "head" if "head" in known else None

    return None


def load_skinned_fbx(
    path: str | Path,
    *,
    max_influences: int = 4,
) -> tuple[MeshData, AvatarSkeleton]:
    """Load the first skinned mesh from an FBX file.

    Returns:
        ``(MeshData, AvatarSkeleton)`` ready for ``SkinningDebugSession.from_loaded``.

    Raises:
        ImportError: If ``ufbx`` is not installed.
        RuntimeError: If the file has no skinned mesh.
    """
    try:
        import ufbx
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "FBX import requires the 'ufbx' package. Install with: pip install ufbx"
        ) from exc

    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)

    scene = ufbx.load_file(str(path))
    mesh = None
    skin = None
    for i in range(len(scene.meshes)):
        candidate = scene.meshes[i]
        if len(candidate.skin_deformers) > 0:
            mesh = candidate
            skin = candidate.skin_deformers[0]
            break
    if mesh is None or skin is None:
        raise RuntimeError(f"No skinned mesh in FBX: {path}")

    n_verts = int(mesh.num_vertices)
    positions = np.zeros((n_verts, 3), dtype=np.float32)
    for i in range(n_verts):
        v = mesh.vertices[i]
        positions[i, 0] = float(v.x)
        positions[i, 1] = float(v.y)
        positions[i, 2] = float(v.z)

    faces = np.zeros((int(mesh.num_faces), 3), dtype=np.int32)
    for fi in range(mesh.num_faces):
        face = mesh.faces[fi]
        if int(face.num_indices) != 3:
            raise RuntimeError(
                f"Non-triangle face in {path.name} (num_indices={face.num_indices})"
            )
        base = int(face.index_begin)
        faces[fi, 0] = int(mesh.vertex_indices[base])
        faces[fi, 1] = int(mesh.vertex_indices[base + 1])
        faces[fi, 2] = int(mesh.vertex_indices[base + 2])
    indices = faces.reshape(-1)

    # Do NOT touch Node.parent — ufbx can access-violate after cluster reads.
    n_bones = int(len(skin.clusters))
    bone_names: list[str] = []
    bind_worlds: list[np.ndarray] = []
    ibms: list[np.ndarray] = []
    cluster_verts: list[np.ndarray] = []
    cluster_weights: list[np.ndarray] = []

    for ci in range(n_bones):
        cluster = skin.clusters[ci]
        node = cluster.bone_node
        bone_names.append(str(node.name) if node is not None else f"bone_{ci}")
        bind_worlds.append(_mat4(cluster.bind_to_world))
        ibms.append(_mat4(cluster.geometry_to_bone))
        nw = int(cluster.num_weights)
        verts = np.zeros(nw, dtype=np.int32)
        weights = np.zeros(nw, dtype=np.float32)
        for wi in range(nw):
            verts[wi] = int(cluster.vertices[wi])
            weights[wi] = float(cluster.weights[wi])
        cluster_verts.append(verts)
        cluster_weights.append(weights)

    known = set(bone_names)
    # If asset has no explicit root bone, treat pelvis (or first bone) as root.
    name_to_index = {n: i for i, n in enumerate(bone_names)}
    bones: list[BoneData] = []
    for i, name in enumerate(bone_names):
        parent_name = _infer_parent(name, known)
        if parent_name == "root" and "root" not in known:
            parent_name = None
        # neck may parent to spine_03 when spine_05 absent
        if name == "head" and parent_name is None:
            for cand in ("neck_02", "neck_01", "spine_03", "spine_02"):
                if cand in known:
                    parent_name = cand
                    break
        if name == "neck_01" and (parent_name is None or parent_name not in known):
            for cand in ("spine_05", "spine_04", "spine_03", "spine_02"):
                if cand in known:
                    parent_name = cand
                    break
        if name.startswith("clavicle_") and (parent_name is None or parent_name not in known):
            for cand in ("spine_05", "spine_04", "spine_03", "spine_02"):
                if cand in known:
                    parent_name = cand
                    break

        parent_index = name_to_index.get(parent_name) if parent_name else None
        # Avoid self-parent
        if parent_index == i:
            parent_index = None

        t = bind_worlds[i][:3, 3]
        bones.append(
            BoneData(
                index=i,
                name=name,
                parent_index=parent_index,
                local_translation=(float(t[0]), float(t[1]), float(t[2])),
                bind_world=bind_worlds[i],
                inverse_bind=ibms[i],
            )
        )

    # Pack per-vertex influences (top-K by weight).
    k = int(max_influences)
    accum: list[list[tuple[int, float]]] = [[] for _ in range(n_verts)]
    for bi, (verts, weights) in enumerate(zip(cluster_verts, cluster_weights, strict=True)):
        for vi, w in zip(verts.tolist(), weights.tolist(), strict=True):
            if w <= 0.0:
                continue
            accum[int(vi)].append((bi, float(w)))

    joint_indices = np.zeros((n_verts, k), dtype=np.int32)
    joint_weights = np.zeros((n_verts, k), dtype=np.float32)
    for vi, infl in enumerate(accum):
        infl.sort(key=lambda t: t[1], reverse=True)
        infl = infl[:k]
        total = sum(w for _, w in infl) or 1.0
        for j, (bi, w) in enumerate(infl):
            joint_indices[vi, j] = bi
            joint_weights[vi, j] = w / total

    normals = _generate_normals(positions, indices)
    uvs = np.zeros((n_verts, 2), dtype=np.float32)
    mesh_name = path.stem
    mesh_data = MeshData(
        name=mesh_name,
        positions=positions,
        normals=normals,
        uvs=uvs,
        indices=indices,
        submeshes=(
            SubMesh(name=mesh_name, index_offset=0, index_count=int(indices.size)),
        ),
        bounds=compute_bounds(positions),
        joint_indices=joint_indices,
        joint_weights=joint_weights,
        source_path=path.resolve(),
        format="fbx",
    )
    skeleton = AvatarSkeleton(name=mesh_name, bones=tuple(bones))
    return mesh_data, skeleton


__all__ = ["load_skinned_fbx"]
