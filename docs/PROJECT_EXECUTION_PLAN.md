# Desktop Girlfriend Project Execution Plan

This document is the working map for the current project phase. It does not replace the older roadmap. It explains what we are building now, what already exists, what is still missing, and how each next module should be accepted.

## 1. Current Mission

We are building a desktop AI companion runtime:

```text
User / dialogue / mouse / voice / desktop events
  -> Emotion State
  -> Attention and Behavior Systems
  -> Character Contract
  -> Model Adapter
  -> Live2D Renderer
  -> Desktop companion presence
```

The project is not just a Live2D demo and not just a pretty model. The final product needs both:

- a good character asset layer
- a strong control system that decides gaze, speech rhythm, passive behavior, active companionship, and desktop presence

## 2. Current Status

### Completed Foundation

- PySide6 desktop shell exists.
- Live2D browser/runtime prototype exists.
- Live2D SDK and PIXI Live2D loading path works.
- Model packages can be inspected.
- Model `profile.json` maps semantic actions to model-specific motions.
- Character Contract v1 exists.
- Emotion State, Behavior Planner, and Model Adapter exist.
- Passive behavior scheduling exists for hover, ambient gestures, tap feedback, and suppression after interactions.
- Behavior event log exists in the browser debug panel.
- Custom model intake validation exists.
- Browser showcase is usable as the main model/debug cockpit.

### Current Gap

The technical runtime is useful, but the product experience is still early. The current sample model is a baseline validation asset, not the final Xiaoyun character. The main missing experience systems are attention, speaking/voice driving, companionship, desktop presence polish, memory, and gesture/vision.

## 3. Module Boundaries

### 3.1 Character Runtime Core

Owns the high-level runtime state and coordinates emotion, attention, behavior, and model commands.

Must not:

- know model motion group names directly
- write Cubism parameters directly
- own UI rendering

### 3.2 Live2D Model Layer

Owns model package loading, package inspection, profile mappings, candidate score, and intake validation.

Key files:

```text
showcase-demo/live2d-prototype/model-package-inspector.js
showcase-demo/live2d-prototype/model-profile.js
showcase-demo/live2d-prototype/model-adapter.js
showcase-demo/live2d-prototype/custom-model-intake.js
```

### 3.3 Attention / Gaze System

Owns where the character is paying attention.

Examples:

- cursor gaze
- idle gaze drift
- thinking gaze
- speaking gaze
- focus target lock
- gaze cooldown
- attention event log

### 3.4 Speaking / Voice Driver

Owns speech rhythm and mouth/body movement while speaking.

Examples:

- TTS playback state
- mouth level
- pause detection
- sentence rhythm
- speaking gaze
- end-of-speech return

### 3.5 Companion Interaction

Owns active companionship decisions.

Examples:

- idle greeting
- long-time no-interaction check-in
- listening while user types
- comfort when user is low
- do-not-disturb cooldown
- companionship event log

### 3.6 Desktop Presence

Owns desktop-window behavior.

Examples:

- drag stability
- position persistence
- topmost policy
- transparency
- click-through policy
- dock-to-edge
- small/large modes

### 3.7 Memory / Relationship

Owns long-term personalization.

Examples:

- user preferences
- recent context
- important memories
- relationship continuity
- privacy and deletion

### 3.8 Gesture / Vision Control

Owns camera/gesture-driven events.

Examples:

- camera permission
- MediaPipe hand recognition
- wave
- summon/hide
- stop speaking
- gesture-to-behavior mapping

## 4. Milestones

### M1. Live2D Runtime Foundation

Status: mostly complete.

Acceptance:

- Live2D SDK is detected.
- `.model3.json` can be loaded through the runtime.
- Browser debug panel shows renderer, SDK, motion, expression, model package status.
- A sample model can play motions and respond to state buttons.

### M2. Replaceable Model System

Status: mostly complete.

Acceptance:

- Each model can have `profile.json`.
- Profile maps semantic actions to model-specific motion groups/indexes.
- Model candidate score is visible.
- Intake status is visible as `ready`, `usable-with-warnings`, or `blocked`.
- Blockers and warnings explain what to fix.

### M3. Attention / Gaze System v1

Status: next.

Goal: make the character feel like it has attention instead of only following the mouse.

Acceptance:

- Cursor gaze is still supported.
- Speaking state can lock attention toward the user/cursor.
- Thinking state can shift gaze away from the cursor.
- Idle state can drift gaze naturally without large body movement.
- Gaze target changes have cooldown and smoothing.
- Debug panel shows current attention target and reason.
- Tests cover cursor, speaking, thinking, idle drift, and cooldown behavior.

### M4. Speaking / Voice Driver v1

Status: not started.

Goal: make speaking feel rhythmic and coordinated.

Acceptance:

- Speaking state drives mouth level.
- Placeholder voice envelope can drive mouth level before real audio analysis.
- Speaking state suppresses passive gestures.
- Pauses reduce mouth movement and allow blink/gaze micro-behavior.
- End-of-speech returns naturally to idle/listening.
- Tests cover speaking, pause, and return.

### M5. Character Runtime Controller v1

Status: not started.

Goal: centralize dialogue, mouse, idle, voice, and desktop events before they reach the renderer.

Acceptance:

- Dialogue events do not directly drive model-specific motions.
- Mouse events, passive events, and voice events pass through one runtime controller.
- Renderer only executes commands.
- Behavior log can explain action source.
- Tests cover event priority and state transition.

### M6. Companion Interaction v1

Status: not started.

Goal: add active companionship without becoming annoying.

Acceptance:

- Character can initiate a low-frequency idle check-in.
- User typing/input shifts character into listening.
- Comfort intent can be triggered by dialogue/emotion.
- Active companionship has cooldown.
- Do-not-disturb state prevents active prompts.
- Tests cover cooldown and suppression.

### M7. Desktop Presence v1

Status: partial.

Goal: make the character feel like a desktop companion, not only a WebView.

Acceptance:

- Character window can be dragged reliably.
- Position, scale, opacity, and visibility persist.
- Topmost/hide/show behavior is stable.
- Window avoids blocking normal work by default.
- Desktop mode can launch with the selected model.

### M8. Xiaoyun Model Intake

Status: pending asset.

Goal: replace baseline sample with a purpose-built Xiaoyun model.

Acceptance:

- Model has expressions or equivalent controllable expression parameters.
- Model has multiple low-intensity idle motions.
- Model has speak, greet, listen, think, comfort, happy, sad mappings.
- Model has lip sync and eye blink parameters.
- Model has physics.
- Intake is `ready` or only minor warnings.
- Motion Probe and Interaction Tuning can produce a final `profile.json`.

### M9. Memory / Relationship v1

Status: not started.

Goal: make interaction persistent across sessions.

Acceptance:

- User preferences can be stored and recalled.
- Recent conversation context can influence emotion/behavior.
- User can inspect and delete remembered items.
- Memory is not required for renderer operation.

### M10. Gesture / Vision Control v1

Status: not started.

Goal: add camera/gesture input after the core companion loop is useful.

Acceptance:

- Gesture events are standardized before behavior mapping.
- Wave, summon, hide, and stop-speaking gestures can be recognized.
- Gesture system is optional and permission-gated.
- Character behavior responds through the runtime controller, not directly through the renderer.

## 5. Current Priority

Next implementation module:

```text
Attention / Gaze System v1
```

Why this is next:

- It improves perceived life immediately.
- It does not depend on final Xiaoyun model assets.
- It strengthens the control system instead of only adding more motions.
- It creates a clean bridge to later speaking and companion systems.

Expected first files:

```text
showcase-demo/live2d-prototype/attention-state.js
showcase-demo/live2d-prototype/attention-state.test.mjs
```

Likely integration points:

```text
showcase-demo/live2d-prototype/live2d-parameter-mapper.js
showcase-demo/live2d-prototype/adapters/live2d-renderer.js
showcase-demo/live2d-prototype/debug-panel.js
```

## 6. Deferred Items

Do not prioritize these until the runtime control loop is stronger:

- camera gesture recognition
- full memory system
- advanced agent tools
- final product packaging
- custom Xiaoyun asset production blocking all engineering work

These are important, but they should not interrupt M3 to M6.

## 7. Working Rule For Future Changes

Before each implementation unit:

1. State current project plan.
2. State completed steps.
3. State current step.
4. State next step.
5. Implement one coherent change.
6. Run focused tests.
7. Commit that unit.

This keeps the project from becoming a pile of unrelated experiments.
