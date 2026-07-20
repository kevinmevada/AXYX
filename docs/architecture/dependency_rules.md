# Dependency Rules — AXYX Rendering Architecture

Allowed dependency direction (top depends on bottom, never reverse):

```text
Studio (Qt / widgets)
    ↓
Viewer
    ↓
API (motion_engine.api.*)     ← preferred public imports
    ↓
Rendering (context, scene, avatar, …)
    ↓
Backend (PyVista / future GL / Vulkan / Unreal)
```

## Forbidden

| From | Must not import |
|------|-----------------|
| `rendering.backend` | `motion_engine.studio`, `PySide6`, `PyQt*` |
| `rendering.avatar` | `PySide6`, `PyQt*`, `motion_engine.studio` |
| `rendering.scene` | `motion_engine.models` (MotionDatabase), `motion_engine.studio` |
| `rendering.resources` | `motion_engine.studio`, `PySide6` |
| `rendering.interfaces` | `motion_engine.studio`, `PySide6` |
| `motion_engine.api` | `motion_engine.studio` (API stays UI-agnostic) |

## Rules of thumb

1. **Studio may know about Viewer / API.** Viewer must not import Studio widgets.
2. **Avatar code must not depend on Qt.** Avatars are data + backend drawables.
3. **Backend must not know Studio or MotionDatabase.** It only presents frames.
4. **Scene graph is pure.** No database / UI imports.
5. Prefer `motion_engine.api.*` in application code over deep `rendering.*` paths.

Enforcement: `tests/test_dependency_rules.py` scans source for forbidden imports.
