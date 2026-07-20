# AXYX Rendering Architecture — Migration Deliverable (Phase-0)

## Complete new folder structure

```text
src/motion_engine/rendering/
  __init__.py
  avatar/
    __init__.py
    avatar.py
    avatar_manager.py
    avatar_loader.py
    avatar_renderer.py
    bind_pose.py
    retarget.py
    skinning.py
    procedural/
      __init__.py
      bone_geometry.py
      procedural_avatar.py
  environment/
    __init__.py
    environment.py
    floor.py
    hdri.py
    atmosphere.py
    reflections.py
  lighting/
    __init__.py
    lighting_manager.py
    studio_lighting.py
    shadows.py
  materials/
    __init__.py
    material_library.py
    pbr.py
  effects/
    __init__.py
    motion_trails.py
    glow.py
    fog.py
  rendergraph/
    __init__.py
    render_pass.py
    render_graph.py
  assets/
    __init__.py
  backend/
    __init__.py
    protocol.py

assets/
  README.md
  avatars/{metahuman,procedural,future}/
  hdri/  environments/  materials/

docs/architecture/
  README.md
  rendering.md
```

## Moved files

| From | To |
|------|----|
| `src/motion_engine/bone_geometry.py` (implementation) | `src/motion_engine/rendering/avatar/procedural/bone_geometry.py` |

## Renamed / conceptual renames

| Old concept | New name |
|-------------|----------|
| “visualization” (brief) | **`rendering/`** (AAA-aligned) |
| Inline PBR in renderer | `rendering.materials.apply_pbr` |
| Inline studio lights | `rendering.lighting.LightingManager` |
| Metallic stick figure | `ProceduralAvatar` (default avatar) |
| Experimental `KILI/` | Target: `assets/avatars/metahuman/` |

## Compatibility wrappers

| Module | Behavior |
|--------|----------|
| `motion_engine.bone_geometry` | Re-exports procedural bone_geometry |
| `motion_engine.renderer` | Same public classes; uses rendering internals |
| `motion_engine.viewer` | Unchanged public API |

## Import changes (preferred new style)

```python
from motion_engine.rendering import (
    AvatarManager,
    ProceduralAvatar,
    MaterialLibrary,
    RenderGraph,
    StudioEnvironment,
)
from motion_engine.rendering.avatar.procedural import transform_bone
# still valid:
from motion_engine.bone_geometry import transform_bone
from motion_engine.renderer import PyVistaRenderer
```

## What was intentionally NOT done

* No SDK rewrite (loader/parser/models/skeleton)
* No Studio UI rewrite
* No MetaHuman integration
* Metallic renderer not deleted — it is the default ProceduralAvatar path
* Public Viewer / Renderer draw_* APIs preserved

## See also

* `docs/architecture/rendering.md` — diagrams, frame lifecycle, extension guide
