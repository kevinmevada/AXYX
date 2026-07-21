# Skinning Debug Studio

Interactive M4 visual validation tool (does **not** modify frozen Studio APIs).

## Run

Use the **project venv** (`venv311`) — system/Anaconda Python often lacks PyVista:

```powershell
cd C:\Users\mevad\Desktop\AXYX
.\venv311\Scripts\Activate.ps1

# Synthetic 2-bone fixture (always works)
python -m experiments.skinning_debug.run --fixture

# Army girl FBX (full body mesh)
python -m experiments.skinning_debug.run --army-girl

# Local MetaHuman pack (assets/avatars/metahuman) — NPZ caches are partial
python -m experiments.skinning_debug.run --lod 3
```

If deps are missing:

```powershell
python -m pip install pyvista pyvistaqt PySide6
```

## Features

- Mesh / wireframe / weight heatmap
- Skeleton bones + joints overlay
- Bone picker + XYZ rotation sliders (−180°…180°)
- Reset to bind
- Diagnostics (vert/bone counts, LBS CPU time, PASS/FAIL)

## Manual test checklist

1. Bind pose — no distortion  
2. Rotate `upperarm_l` (or fixture `forearm`)  
3. Rotate `spine_01` / `head` / `thigh_l`  
4. Weight heatmap for selected bone  
5. Skeleton overlay inside mesh  
6. Stress angles 0→45→90→135→180  

## Automated sweep

```bash
python -m pytest tests/visual/test_m4_skinning_validation.py -q
```
