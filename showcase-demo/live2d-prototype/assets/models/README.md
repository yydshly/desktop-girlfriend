# Live2D Model Assets

Put legal Live2D runtime model folders here.

Read `MODEL_SOURCES.md` before adding a sample or custom model.

Expected custom model location for the prototype:

```text
showcase-demo/live2d-prototype/assets/models/custom/<ModelName>/<ModelName>.model3.json
```

Current technical validation sample:

```text
showcase-demo/live2d-prototype/assets/models/sample/Hiyori/Hiyori.model3.json
```

The Live2D prototype now loads `.model3.json` packages through the local
Live2D runtime. The placeholder renderer remains only as a debug fallback.

Each model folder should include:

```text
<ModelName>.model3.json
profile.json
source.md
textures/
motions/
expressions/
```

Use `custom/profile.template.json` as the starting point for candidate model
profiles. The profile maps Xiaoyun semantic actions and expressions to the
model-specific motion groups, indexes, and expression names.

After adding a candidate model:

1. put the model folder under `assets/models/custom/<ModelName>/`
2. copy `custom/profile.template.json` to `<ModelName>/profile.json`
3. update action and expression mappings from Motion Probe observations
4. open the showcase page and check candidate score / missing items
5. run the fixed model experiment sequence
