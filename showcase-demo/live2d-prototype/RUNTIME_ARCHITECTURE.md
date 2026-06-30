# Live2D Runtime Architecture

This document defines the mainline architecture after the PNG puppet prototype.

The current UI is not the final visual target. It is a runtime harness for proving that AI dialogue state can drive a real Live2D model later.

## Current Position

```text
Done:
  - PNG puppet legacy prototype
  - avatar.state / avatar.sequence / dialogue.turn protocol
  - Live2D prototype shell
  - model asset path entrypoint
  - renderer mode switching
  - avatar state to Live2D parameter mapping

Not done yet:
  - legal sample Live2D model
  - real Live2D SDK loader
  - expression and motion playback against a real .model3.json
  - Electron transparent desktop shell
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
  - dry-run adapter now
  - will load .model3.json through a Live2D SDK
  - will apply parameters, expressions, motions, and physics
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
textures/
motions/
expressions/
physics3.json
```

### Desktop Shell

The Web prototype should later be wrapped by Electron.

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

### Step 1: Real Model Loading

Add a legal Live2D sample model under `assets/models/sample/`.

Record the model source in `assets/models/sample-model-manifest.json` before connecting it to runtime code.

Then implement the first real `Live2DRenderer` loader:

```text
detect SDK runtime
load SDK
load .model3.json
fit model to stage
keep current renderer mode switch
show clear loading and error states
```

### Step 2: Parameter Drive

Apply `live2d-parameter-mapper.js` output to the model:

```text
eye tracking
head angle
body angle
mouth open
mouth form
breathing
```

### Step 3: Expressions And Motions

Map product states to Live2D expressions and motions:

```text
happy -> happy expression + greet/reply motion
thinking -> thinking expression + listen motion
sad -> sad expression + slower idle
soft -> comfort expression + comfort motion
engaged -> speaking expression + reply motion
```

### Step 4: Desktop Runtime

Move from browser prototype to desktop shell:

```text
Electron window
transparent background
window controls outside the character stage
bridge connection to local AI runtime
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

The current UI uses a canvas placeholder. It can prove data flow, but it cannot provide final product presence.

Visual quality will improve only after these are true:

```text
real model asset
real renderer
real expression and motion playback
desktop transparent shell
custom character art direction
```

Until then, UI polish should support debugging and model integration. It should not be treated as the final desktop girlfriend visual.
