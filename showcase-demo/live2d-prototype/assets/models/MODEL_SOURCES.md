# Live2D Model Sources

This directory only accepts models with a clear source and license record.

Do not commit random `.model3.json` packages without documenting where they came from and what the project is allowed to do with them.

## Candidate Source: Live2D Cubism Web Samples

Official repository:

```text
https://github.com/Live2D/CubismWebSamples
```

License page:

```text
https://github.com/Live2D/CubismWebSamples/blob/develop/LICENSE.md
```

Use this source for technical validation only after confirming the specific model asset and license terms are acceptable for the current project use.

## Required Record

Every model folder should include a source record with:

```text
model_id
display_name
source_url
license_url
allowed_use
local_model_json
notes
```

## Local Layout

Recommended sample model location:

```text
showcase-demo/live2d-prototype/assets/models/sample/
```

Recommended custom model location:

```text
showcase-demo/live2d-prototype/assets/models/custom/
```

## Next Runtime Step

After adding a legal sample model, update `sample-model-manifest.json`, then implement `Live2DRenderer` so it loads the recorded `local_model_json` path.
