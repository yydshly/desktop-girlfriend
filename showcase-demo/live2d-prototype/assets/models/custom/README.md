# Custom Live2D Candidate Models

Put candidate models here using one folder per model:

```text
custom/<ModelName>/<ModelName>.model3.json
custom/<ModelName>/profile.json
custom/<ModelName>/source.md
```

Do not commit a model unless its source and license are clear.

Workflow:

1. Copy `profile.template.json` into the model folder as `profile.json`.
2. Start the showcase page.
3. Set the Model URL to `./assets/models/custom/<ModelName>/<ModelName>.model3.json`.
4. Use Motion Probe to test motion groups and indexes.
5. Fill `mappings.actions`.
6. Fill `mappings.expressions` only with expression names that exist in the model package.
7. Run the fixed model experiment.
8. Check candidate score and missing items.

The goal is not just to load a model. The goal is to find a model whose dynamic
behavior is suitable for Xiaoyun as a desktop companion.
