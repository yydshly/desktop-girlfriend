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
  - PySide6 desktop WebView shell
  - local WebSocket bridge from the Python app to the Live2D page
  - runtime-app.js / debug-panel.js split with a thin live2d.js entrypoint

Not done yet:
  - profile-based expression aliases and parameter ranges
  - product-facing desktop controls and packaging polish
  - custom character production
```

## Target Runtime Flow

```text
User input / voice / mouse / desktop event
  -> Dialogue layer
  -> Intent and emotion layer
  -> Avatar state layer
  -> Motion planner
  -> Renderer adapter
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

### Avatar State Layer

Converts dialogue intent into stable character state.

Current state fields:

```json
{
  "emotion": "soft",
  "mouth": 0.18,
  "gaze": "cursor",
  "motion": "comfort",
  "intensity": 0.68
}
```

This layer should stay independent from Live2D, VRM, or any specific renderer.

### Motion Planner

Chooses short behavior sequences from the current avatar state.

Examples:

```text
greet   -> happy expression + light head movement + wave motion
listen  -> thinking expression + low mouth value + focused gaze
reply   -> engaged expression + speaking mouth + subtle body motion
comfort -> soft expression + slower movement + warm gaze
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

`profile.json` is the model-specific tuning file. It should hold motion bindings,
expression aliases, and later parameter ranges. Browser `localStorage` is only a
debug override for the currently selected model.

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
motionBindings
expressionAliases
parameterRanges
debug notes for chosen motion indexes
```

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
