# Model Pipeline

## Phase 1: Concept

Generate multiple character concepts with MiniMax or another image model. Pick one visual direction and freeze the core identity: hair, face, outfit, palette, and emotional tone.

## Phase 2: Production Art

Create or commission a clean front-facing character illustration designed for Live2D. Convert the final illustration into a layered PSD that follows `LIVE2D_ASSET_SPEC.md`.

## Phase 3: Rigging

Import the PSD into Live2D Cubism Editor. Bind face angle, eye movement, blink, mouth open, mouth form, breathing, hair physics, and basic body movement.

## Phase 4: Export

Export the Live2D runtime package. The expected main entry is a `.model3.json` file with textures, expressions, motions, and physics in the same model directory.

## Phase 5: Runtime Integration

Place the exported model under `showcase-demo/live2d-prototype/assets/models/custom/`. Configure the Live2D renderer to load that `.model3.json`. Keep the existing `avatar.state`, `avatar.sequence`, and `dialogue.turn` protocol unchanged.
