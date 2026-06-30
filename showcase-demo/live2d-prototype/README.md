# Live2D Prototype

This directory is the new B-plan mainline for the desktop girlfriend project.

The first version deliberately uses a placeholder renderer. That renderer is not the final visual target. It proves that the existing `avatar.state`, `avatar.sequence`, and `dialogue.turn` protocol can drive a model-shaped runtime before a real `.model3.json` file is available.

Read `RUNTIME_ARCHITECTURE.md` for the mainline architecture and iteration order.

The intended upgrade path is:

1. Run placeholder renderer and validate state mapping.
2. Add a legally usable sample Live2D model.
3. Replace `placeholder-renderer.js` with `live2d-renderer.js` at runtime.
4. Replace sample model with custom character model.
5. Wrap the prototype in Electron for transparent desktop rendering.

`live2d-parameter-mapper.js` is the bridge from product state to Cubism-style parameters. Keep AI/dialogue states stable and change this mapper when a real model uses different parameter names or ranges.
