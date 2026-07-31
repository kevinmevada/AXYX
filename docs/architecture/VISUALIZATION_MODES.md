# Visualization Modes Architecture

## Overview

AXYX supports three interchangeable visualization backends behind a single
playback pipeline:

```
VisualizationManager
├── StickRenderer      (clinical stick figure — default, fastest)
├── BoneRenderer       (anatomical meshes from assets/bones)
└── AvatarRenderer     (skinned FBX digital twin)
```

Motion originates exclusively from the existing playback engine.
Renderers only visualize pose data. Switching modes never recreates the
viewport, resets the camera, or restarts playback.

## API

```python
viewer_canvas.set_visualization("stick")
viewer_canvas.set_visualization("bones")
viewer_canvas.set_visualization("avatar")
```

Studio UI: **Visualization ▾** on the viewport toolbar.

## Bone assets

- Config: `config/bone_mapping.yaml` (mesh ↔ joints, rest pose, material)
- Assets: `assets/bones/` (auto-installed on first anatomical use)
- Loader: `BoneAssetLoader` (lazy cache, OBJ/STL/PLY/GLTF/VTK via PyVista)
- Manager: `BoneAssetManager` downloads a curated pack when `pack_url` is set,
  otherwise generates a high-resolution cortical pack once and caches it

Replace any `.obj` under `assets/bones/` to swap anatomical models without
code changes.

## Rendering flow

1. Playback seeks frame → `SkeletonViewer.seek` → pose
2. If mode is stick: existing shaft/joint draw path
3. If mode is bones: `BoneRenderer.render_pose` updates actor `user_matrix` only
4. If mode is avatar: existing digital-twin body callback

## Extending

Add a new `BaseVisualizationRenderer` subclass, register it on
`VisualizationManager`, and expose a toolbar/command entry. Future modes
(muscles, GRF, heatmaps) plug into the same framework.
