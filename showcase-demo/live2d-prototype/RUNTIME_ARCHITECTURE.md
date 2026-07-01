# Live2D Runtime Architecture

This document defines the mainline architecture after the PNG puppet prototype.

The current UI is not the final visual target. It is a runtime harness for proving that AI dialogue state can drive a real Live2D model and for tuning model-specific behavior before the desktop shell becomes product-facing.

## Current Position

```text
Done:
  - PNG puppet legacy prototype
  - avatar.state / avatar.sequence / dialogue.turn protocol
  - Live2D prototype shell
  - model asset path entrypoint
  - renderer mode switching
  - avatar state to Live2D parameter mapping
  - legal sample Live2D model package for technical validation
  - local Live2D SDK runtime loading
  - .model3.json loading through PIXI Live2D
  - parameter, expression, and motion playback
  - model package capability diagnostics
  - Motion Probe controls for testing motion groups and indexes
  - model profile.json motion binding support
  - Character Contract v1 for stable semantic states, actions, and expressions
  - profile.json schemaVersion 1 mappings for model-specific action/expression adapters
  - renderer-neutral Emotion State module
  - semantic Behavior Planner module
  - profile-backed Model Adapter module
  - PySide6 desktop WebView shell
  - local WebSocket bridge from the Python app to the Live2D page
  - runtime-app.js / debug-panel.js split with a thin live2d.js entrypoint
  - Emotion State / Behavior Planner / Model Adapter chain wired into the active renderer path
  - adapter-driven Live2D motion, expression, mouth, and intensity parameters
  - browser diagnostics for model adapter commands

Not done yet:
  - profile-based expression aliases and parameter ranges
  - product-facing desktop controls and packaging polish
  - custom character production
  - Model Gallery fixed-sequence candidate evaluation
```

## Target Runtime Flow

```text
User input / voice / mouse / desktop event
  -> Dialogue layer
  -> Emotion State layer
  -> Behavior Planner
  -> Model Adapter
  -> Live2D model
  -> Desktop shell
```

## Component Boundaries

### Dialogue Layer

Owns user text, assistant response text, TTS lifecycle, and turn identity.

Current protocol message:

```json
{
  "type": "dialogue.turn",
  "payload": {
    "turn_id": "turn-001",
    "intent": "comfort",
    "user_text": "我今天有点累",
    "response_text": "先放松一下，我陪你慢慢来。",
    "tts_state": "queued"
  }
}
```

### Emotion State Layer

Converts bridge messages and dialogue intent into stable, renderer-neutral
emotion state.

Current module:

```text
emotion-state.js
```

Current state shape:

```json
{
  "state": "comfort",
  "emotion": "soft",
  "intensity": 0.68,
  "activity": "comfort",
  "gaze": "cursor",
  "mouth": 0.18,
  "turn": {
    "turnId": "turn-001",
    "ttsState": "speaking"
  }
}
```

This layer must stay independent from Live2D, VRM, or any specific renderer.
It must not expose motion groups, motion indexes, or model expression names.

### Behavior Planner

Chooses semantic behavior intent from the current emotion state.

Examples:

```text
speak   -> engaged expression + speaking mouth + cursor gaze
think   -> thinking expression + low mouth value + down-left gaze
comfort -> soft expression + slow return to idle
greet   -> happy expression + greet action
```

Current module:

```text
behavior-planner.js
```

### Model Adapter

Translates semantic behavior through the active model profile.

Current module:

```text
model-adapter.js
```

Input:

```json
{
  "action": "speak",
  "expression": "engaged",
  "intensity": 0.76,
  "gaze": "cursor",
  "mouth": 0.65
}
```

Output:

```json
{
  "motion": { "group": "TapBody", "index": 0, "action": "speak" },
  "expression": { "name": "smile", "semantic": "engaged" },
  "parameters": { "gaze": "cursor", "mouth": 0.65, "intensity": 0.76 }
}
```

### Renderer Adapter

Owns renderer-specific translation.

Current adapters:

```text
PlaceholderRenderer
  - proves UI and state flow
  - not a product visual target

Live2DRenderer
  - loads .model3.json through the local Live2D SDK runtime
  - applies parameters, expressions, and motions
  - treats adapter speak/reply commands as speaking for mouth pulse animation
  - reads model package capabilities before issuing expression and motion commands
  - uses model profile motion bindings before falling back to generic mappings
```

### Live2D Parameter Mapper

Maps product-level avatar state into Cubism-style parameter commands.

Current parameter targets:

```text
ParamAngleX
ParamAngleY
ParamAngleZ
ParamBodyAngleX
ParamEyeLOpen
ParamEyeROpen
ParamEyeBallX
ParamEyeBallY
ParamMouthOpenY
ParamMouthForm
ParamBreath
```

When a real model uses different parameter names or ranges, change the mapper instead of changing dialogue or state protocols.

### Model Asset Layer

Expected custom model location:

```text
showcase-demo/live2d-prototype/assets/models/custom/model.model3.json
```

Expected asset package:

```text
model.model3.json
profile.json
textures/
motions/
expressions/
physics3.json
```

`profile.json` is the model-specific tuning file. It implements Character
Contract v1 and should use this shape:

```json
{
  "schemaVersion": 1,
  "displayName": "Hiyori",
  "desktopPlacement": {
    "scaleMultiplier": 1.06,
    "xOffsetRatio": 0,
    "yRatio": 0.54
  },
  "mappings": {
    "actions": {
      "idle": { "group": "Idle", "index": 0 },
      "speak": { "group": "TapBody", "index": 0 }
    },
    "expressions": {
      "neutral": "default",
      "happy": "smile"
    }
  }
}
```

Browser `localStorage` is only a debug override for the currently selected
model. Legacy `motionBindings` are still accepted by the loader so older test
profiles do not break, but new models should use `mappings.actions`.

### Desktop Shell

The Web prototype is currently hosted by a PySide6 `QWebEngineView` desktop shell.
Electron remains an optional future packaging route, but it is not required for
the current Python app integration.

Expected shell features:

```text
transparent window
always-on-top mode
click-through toggle
drag to reposition
desktop edge behavior
local websocket bridge to AI runtime
```

## Iteration Plan

### Step 1: Model Profile Mainline

Move all model-specific runtime decisions into `profile.json`:

```text
schemaVersion 1
mappings.actions
mappings.expressions
desktopPlacement
parameterRanges
debug notes for chosen motion indexes
```

Status: Character Contract v1 and profile mappings are now the mainline shape.
The remaining work is using expression mappings and parameter ranges in the
renderer adapter.

### Step 2: Stable Avatar Protocol

Make Python and JavaScript share one small, renderer-neutral avatar state contract:

```text
idle
listening
thinking
speaking
happy
sad
comfort
error
```

Python should emit stable intent/state messages. JavaScript should translate
those messages through the active model profile.

### Step 3: Runtime / Debug Split

The browser code is now separated into focused modules:

```text
live2d.js         -> thin mode-aware entrypoint
runtime-app.js   -> renderer, model, profile, bridge, avatar controller
bridge-client.js -> WebSocket lifecycle and reconnects
debug-panel.js   -> showcase-only controls and diagnostics
model-profile.js -> profile loading
```

The desktop shell should load the runtime without showing debug controls by
default. The browser showcase can keep the debug panel.

### Step 4: Desktop Runtime Polish

Continue hardening the PySide6 shell:

```text
transparent background
drag and position persistence
always-on-top and click-through controls
startup diagnostics
bridge reconnect diagnostics
```

### Step 5: Custom Character

Use `showcase-demo/model-production/` to create the custom asset:

```text
character brief
MiniMax or image-model concept references
layered PSD
Live2D Cubism rigging
exported model3 package
runtime integration
```

The Xiaoyun model target is defined in:

```text
docs/XIAOYUN_CHARACTER_MODEL_SPEC.md
```

The core point is that model quality and dynamic behavior are the product
ceiling. Hiyori remains a baseline validation model, not the final visual
standard.

## Why The Current UI Looks Weak

The current model is a sample validation asset with limited motions and no rich
expression set. It proves the runtime but does not represent final product
presence.

Visual quality will improve only after these are true:

```text
custom model asset
profile tuned for that model
rich expression and motion set
desktop transparent shell
custom character art direction
```

Until then, UI polish should support debugging, model integration, and profile
tuning. It should not be treated as the final desktop girlfriend visual.
