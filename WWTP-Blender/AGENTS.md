# WWTP Blender Project Rules

- Use metres: 1 Blender Unit = 1 m; Z is vertical.
- Keep engineering dimensions in `data/*.json`; generators consume data and create geometry.
- Scripts must be idempotent: rerunning removes/rebuilds their owned collections without duplicate names.
- Change formal design by editing JSON, never by manually moving generated objects.
- Name generated objects `TYPE_Name_Index` and retain the fixed collection hierarchy.
- Inspect the target collection before any large deletion. Do not modify files outside this project.
- External models require a known permissive licence and a record in `docs/ASSET_LICENSES.md` and `docs/ASSET_MANIFEST.json`.
- Major process structures are parameterically generated; downloaded assets are detail only.
- Use linked meshes/collection instances for repeated equipment, lights, trees, valves, and aerators.
