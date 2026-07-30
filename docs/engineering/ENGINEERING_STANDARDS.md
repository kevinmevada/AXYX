# AXYX Engineering Standards

## Platform

- **Native PySide6 only** for Motion Studio — no embedded web/React UI.
- Preserve existing behavior; evolve modules incrementally.
- Keep `motion_engine` public API stable; add shims (`domain/`) instead of breaking imports.

## Studio Layout

- **Commands** — register via `CommandRegistry`; menus and shortcuts derive from actions.
- **Background work** — use `TaskManager`; never touch Qt widgets from worker threads.
- **State** — prefer `ApplicationState` + `ApplicationEventBus` for cross-panel sync.
- **Docking** — register docks with `WorkspaceManager`; persist layout in `QSettings`.

## Code Style

- Small focused modules under `studio/<area>/`.
- Match surrounding naming, typing, and docstring conventions.
- Comments only for non-obvious logic.
- Tests for new infrastructure (`tests/test_studio/`); quarantine flaky UI tests rather than deleting.

## Dependencies

- Core motion engine: `pyproject.toml` `[project.dependencies]`.
- Desktop stack: `[project.optional-dependencies.studio]` (matches `requirements-studio.txt`).

## Plugins

Third-party extensions implement `Plugin.activate(PluginContext)` and register under the `axyx.studio_plugins` entry-point group. Loader ignores failures.
