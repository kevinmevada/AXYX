# Milestone 1 — Asset Pipeline

Implemented under `src/motion_engine/rendering/avatar/`:

- `loader/` — manifest, mesh (GLB/GLTF/NPZ), texture, material, skeleton, orchestrator
- `models/` — immutable manifest/mesh/material/texture/skeleton/LoadedAvatar
- `validation/` — manifest + asset validators
- `registry/` — AvatarRegistry + AvatarFactory
- `digital_avatar.py` — Avatar ABC adapter (bind-pose display)

Public imports: `motion_engine.api.avatar` (AvatarLoader, DigitalAvatar, …).

Viewer / Studio / frozen rendering APIs unchanged.
