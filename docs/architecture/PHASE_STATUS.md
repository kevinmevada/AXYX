# Studio Platform — Implementation Status (truthful)

Verified by `pytest tests/test_studio tests/test_dependency_rules.py` plus targeted smokes.

| System | Status | Used by live app? |
|--------|--------|-------------------|
| CommandRegistry + menus + shortcuts | **Production** | Yes |
| Command palette (`Ctrl+Shift+P`) | **Production** | Yes |
| Camera / fullscreen / charts commands | **Production** | Yes (View menu + palette) |
| Undo/Redo with push on selection | **Production** | Yes |
| ApplicationState + observers | **Production** | Yes (title, docks, status, scene) |
| ApplicationEventBus + listeners | **Production** | Yes (incl. frame → charts playhead) |
| TaskManager async loads + progress | **Production** | Yes |
| Workspace docks + presets + reset recipe | **Production** | Yes (explorer/inspector/**charts**) |
| Charts dock (pyqtgraph) | **Production** | Yes |
| Theme light/dark/high_contrast | **Production** | Yes |
| Settings schema migrate/validate + dialog | **Production** | Yes (path, speed, theme, loop) |
| Lucide icons + pixmap cache | **Production** | CommandBar |
| Accessibility names | **Partial** | Key chrome + settings |
| Sample plugin + entry point | **Production** | `plugin.hello`; docks → WorkspaceManager |
| Rotating file logging | **Production** | `~/.axyx/logs/studio.log` |
| Dataset path+mtime cache | **Production** | MotionService |
| ViewportSceneBridge SceneGraph read model | **Production** | Inspector Scene card + avatar layer toggle |
| Full SceneGraph-driven renderer | **Not done** | PyVista draw queues remain primary |
| `renderer.py` split | **Not done** | Still large module |
| Quarantine tests revival | **Not done** | Deleted APIs; keep ignored |

## Commercial bar

Research Studio shell is production-wired. Blender-class SceneGraph renderer and full golden/a11y suites remain open work — documented, not pretended complete.
