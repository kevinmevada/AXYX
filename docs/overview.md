# AXYX — Overview

AXYX is a **research software platform** for clinical gait analysis workflows.

## Problem

Gait labs produce dense marker / joint-center trajectories in MATLAB catalogs. Researchers need a reproducible path from raw sessions to:

- a validated skeletal model  
- interactive 3D review  

## Approach

1. **Parse** filtered MATLAB datasets into a typed `MotionDatabase`  
2. **Map** markers → anatomical joints via `config/skeleton_definition.yaml`  
3. **Measure** bone lengths as Euclidean distances in lab space  
4. **Visualize** with a studio viewport (PyVista) inside AXYX Studio  

## Units & coordinates

Dataset units are preserved from the capture lab (often millimeters; labeled Unknown until fully catalogued). Coordinate conventions live in `config/coordinate_system.yaml`.

## Reproducibility

- Reconstruction rules are YAML, not buried in notebooks  
- Studio and SDK share the same `SkeletonBuilder`  
- Tests under `tests/` cover Studio services and skeleton reconstruction  
