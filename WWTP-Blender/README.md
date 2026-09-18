# CAU Environmental Engineering — WWTP Blender

Parametric engineering presentation model for a municipal wastewater treatment plant.

Current generated deliverable: `blender/plant.blend`, rebuilt from
`data/plan_extracted.json`. The refined preview uses Poly Haven 2K PBR surfaces,
CC0 instanced street lights, CC0 generic industrial equipment/valve proxies, and
four Geometry Nodes aerator grids (1,500 instances per A2/O series). Downloaded
equipment is visual context only; process dimensions and counts remain
parameter-driven.

## Workflow

`data/*.json` → `scripts/generators/*.py` → Blender geometry.

All dimensions are metres. The current model is a DXF-derived engineering white
model with a first refinement pass; vertical dimensions remain provisional until
the formal design documents are added.

Run inside Blender from the project root:

```python
exec(open(r"E:\AI\WWTP-Blender\scripts\build_test_scene.py", encoding="utf-8").read())
```

The test script creates, previews, saves the project file, then removes its `TEST` collection. `build_plant.py` is deliberately a scaffold until formal design data is supplied.
