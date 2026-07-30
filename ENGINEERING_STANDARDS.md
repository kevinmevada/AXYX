# AXYX Engineering Standards (Phase 0+)

Mandatory rules for Motion Studio and the Motion Engine.

## Platform

1. **Native PySide6 only** — no React, Electron, WebViews, HTML/CSS/JS UI.
2. **Preserve behavior** — evolve; do not rewrite frozen M1–M7 public APIs.
3. **Domain has zero Qt imports** — Qt stays in `studio/` / presentation.
4. **No circular imports** — gated by `tests/test_dependency_rules.py`.

## Studio

5. **Commands** — every user action via `CommandRegistry` (menu / toolbar / shortcut / palette).
6. **No blocking UI thread** for I/O >16 ms — use `TaskManager` (`QThreadPool` + `QRunnable`).
7. **No widget→widget app logic** — signals → commands/controller → state → UI.
8. **No raw colors** outside design tokens (`studio/theme/`).
9. **Dock layouts** persist via `WorkspaceManager` + `QSettings`.
10. **State** — prefer `ApplicationState` + `ApplicationEventBus`.

## Quality

11. Every public class typed + docstring.
12. Every new service/command has unit tests under `tests/test_studio/`.
13. Quarantine broken tests in `tests/test_studio/_quarantine/` — never leave red CI.
14. Delete unused widgets/components; do not keep dead `_archive` copies in-tree.
15. Benchmark load + frame path when changing playback/render hot paths.

## Plugins

16. Extensions implement `Plugin.activate(PluginContext)` and register under entry-point group `axyx.studio_plugins`.
17. **Undo** — selection changes push `QUndoCommand` via `StudioUndoStack`; guard with `_applying_undo`.
18. **Theme** — `StudioSettings.theme_mode` (`light` | `dark` | `high_contrast`); QSS tokens only (no hardcoded hex in `.qss`).
19. **Logging** — `configure_studio_logging()` writes to `~/.axyx/logs/studio.log` (rotating) + console.
20. **Command palette** — `view.command_palette` (`Ctrl+Shift+P`) must stay wired in menus and CommandBar.
