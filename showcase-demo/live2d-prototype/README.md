# Live2D Prototype

This directory is the new B-plan mainline for the desktop girlfriend project.

The prototype now loads a sample Live2D model and keeps the placeholder renderer only as a fallback/debug path. It proves that the existing `avatar.state`, `avatar.sequence`, and `dialogue.turn` protocol can drive a model-shaped runtime.

Read `RUNTIME_ARCHITECTURE.md` for the mainline architecture and iteration order.

The current mainline is:

1. Load a legally usable sample Live2D model.
2. Inspect model package capabilities.
3. Tune motion bindings through Motion Probe and profile.json.
4. Drive the model from avatar and dialogue bridge messages.
5. Replace the sample model with a custom character model.
6. Harden the PySide6 transparent desktop shell.

`live2d-parameter-mapper.js` is the bridge from product state to Cubism-style parameters. Keep AI/dialogue states stable and change this mapper when a real model uses different parameter names or ranges.

Each model can include a `profile.json` next to its `.model3.json`. The profile is the model-specific place for motion bindings and later expression aliases or parameter ranges.
