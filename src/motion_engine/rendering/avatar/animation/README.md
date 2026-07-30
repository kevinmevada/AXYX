# M5 Animation Runtime

Package: `motion_engine.rendering.avatar.animation`

## Pipeline

```
AnimationClip → TrackSampler → PoseBuilder → AnimationPose → M4 SkinningRuntime
```

## Quick start

```python
from motion_engine.rendering.avatar.animation import AnimationFactory, AnimationPlayer

clips = AnimationFactory().locomotion_set(bind, bone="upperarm_l")
player = AnimationPlayer(bind=bind)
player.load(clips["walk"])
player.play()
pose = player.tick(1.0 / 60.0)
# deform = SkinningRuntime().deform(mesh, skin, bind_pose=bind, pose=pose)
```

## Features

- Keyframes / sparse tracks / quaternion SLERP
- Timeline: play, pause, seek, loop, reverse, speed, frame step
- Controller states: Idle / Walk / Run / Jump / Custom + crossfade
- Events & markers
- JSON / glTF / FBX loaders via `AnimationFactory`
- Evaluation cache + statistics + serialization

Does **not** modify frozen M1–M4 APIs.
