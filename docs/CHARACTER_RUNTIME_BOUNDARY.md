# Character Runtime Boundary

This document records the current code facts and the target ownership boundary for the Live2D character runtime. It is a guardrail for the next implementation steps, especially Attention / Gaze System v1.

## 1. Current Code Facts

Current branch:

```text
codex/live2d-model-mainline
```

Live2D is already on the main application path. It is not only an isolated showcase page.

Python-side mainline components:

```text
app/main.py
  - starts Live2DBridgeServer
  - starts Live2DBridgeEventDispatcher
  - optionally starts Live2DDesktopProcess
  - scans Live2D model catalog
  - persists selected model id
  - wires main-window Live2D controls

app/live2d_desktop.py
  - command entrypoint for the separate desktop companion window

app/ui/live2d_bridge_server.py
  - local WebSocket broadcaster consumed by the Live2D page

app/ui/live2d_bridge.py
  - maps EventBus events into bridge messages

app/ui/live2d_desktop_process.py
  - launches and stops the desktop Live2D process

app/ui/live2d_desktop_window.py
  - PySide6 WebView desktop shell for the Live2D runtime page

app/ui/live2d_model_catalog.py
  - scans and diagnoses local model3 packages
```

Web-side runtime components:

```text
showcase-demo/live2d-prototype/emotion-state.js
  - maps bridge messages into renderer-neutral emotion state

showcase-demo/live2d-prototype/behavior-planner.js
  - maps emotion state into semantic behavior

showcase-demo/live2d-prototype/model-adapter.js
  - maps semantic behavior through profile.json into model commands

showcase-demo/live2d-prototype/character-runtime.js
  - assembles mapped state, emotion state, behavior, and model commands

showcase-demo/live2d-prototype/avatar-controller.js
  - coordinates UI state, renderer calls, bubble/readout updates

showcase-demo/live2d-prototype/runtime-app.js
  - composes renderer, bridge, model route, profile, debug/runtime controls

showcase-demo/live2d-prototype/adapters/live2d-renderer.js
  - loads and executes Live2D model commands
```

The project is not missing concepts. It is missing stricter boundary convergence.

## 2. Required Runtime Flow

The next stable flow is:

```text
bridge message
  -> emotion state
  -> attention target
  -> semantic behavior
  -> model command
  -> renderer execution
  -> Live2D visible output
```

Layer responsibilities:

```text
Bridge message -> Emotion State
  Owner: emotion-state.js
  Output: renderer-neutral emotion state
  Must not output: motion group, motion index, model expression filename

Emotion State -> Attention Target
  Owner: future attention-system.js
  Output: semantic attention target such as cursor, user, down-left, idle-scan, away
  Must not directly write Cubism parameters

Emotion / Attention -> Behavior
  Owner: behavior-planner.js
  Output: semantic behavior such as speak, think, comfort, happy, idle
  Must not output model-specific motion group/index

Behavior -> Model Command
  Owner: model-adapter.js
  Input: behavior + effective profile
  Output: model-specific motion, expression, and parameter intent

Model Command -> Renderer
  Owner: Live2DRenderer
  Output: actual Cubism parameter writes, expression application, motion playback, drawing
```

## 3. Current Responsibility Distribution

### Bridge Message -> Emotion State

Current owner:

```text
emotion-state.js
```

Current status:

```text
Mostly correct.
```

Risk:

```text
state-mapper.js still contains state presets for UI bubble/readout support.
Python bridge mapper also contains semantic mapping.
```

Rule:

```text
emotion-state.js is the semantic source of truth.
state-mapper.js may support UI bubble/readout, but must not become a second behavior contract.
```

### Emotion State -> Behavior

Current owner:

```text
behavior-planner.js
```

Current status:

```text
Correct direction.
```

Rule:

```text
Behavior Planner outputs semantic actions and expressions only.
It must not know Hiyori, Natori, Idle, TapBody, or expression filenames.
```

### Behavior -> Model Command

Current owner:

```text
model-adapter.js
```

Current status:

```text
Correct direction.
Motion override now flows through effective profile before adapter output.
```

Rule:

```text
Model Adapter is the only layer that translates semantic behavior into model-specific commands.
```

### Model Command -> Renderer

Current owner:

```text
adapters/live2d-renderer.js
```

Current status:

```text
Works, but still contains too much behavior timing and reaction logic.
```

Renderer may own:

```text
- SDK loading
- model3 package loading
- Cubism parameter writes
- expression application
- motion playback
- fallback texture preview
- canvas drawing
- renderer diagnostics
```

Renderer should not keep gaining:

```text
- high-level attention decisions
- dialogue-state interpretation
- model selection logic
- AI behavior policy
```

### Passive / Hover / Ambient / Idle Rotation

Current location:

```text
passive-behavior-scheduler.js
adapters/live2d-renderer.js
```

Current status:

```text
Partially separated.
Scheduler decides passive timing, but renderer still coordinates when to run it and how to apply pointer reactions.
```

Near-term rule:

```text
Do not add more passive behavior policy directly to Live2DRenderer.
New passive decisions should move toward Character Runtime Core.
```

### Speaking Mouth / Expression / Motion

Current location:

```text
emotion-state.js
behavior-planner.js
model-adapter.js
adapters/live2d-renderer.js
```

Current status:

```text
The semantic speak state is runtime-driven.
Speaking Driver v1 owns active/source/base mouth/rhythm.
Model Adapter passes speaking and mouth parameters to the renderer.
The renderer consumes those parameters and may add low-level head/body motion while speaking.
```

Near-term rule:

```text
Speaking Driver v1 should make speaking timing explicit before the renderer writes mouth parameters.
The renderer can execute mouth values, but should not decide conversation state.
```

## 4. Known Architecture Problems

### app/main.py Is Too Heavy

`app/main.py` currently owns application composition plus many Live2D desktop control details.

Problem:

```text
It is becoming a feature coordinator instead of only a composition root.
```

Recommended extraction:

```text
app/ui/live2d_desktop_coordinator.py
```

Suggested ownership:

```text
- bridge server lifecycle
- bridge dispatcher lifecycle
- desktop process lifecycle
- model catalog scan/refresh
- model selection persistence
- scale / opacity / visibility / restart logic
- model folder open request
```

`app/main.py` should construct the coordinator and wire its callbacks into the main window.

### Renderer Still Has Runtime Decisions

`Live2DRenderer` still handles:

```text
- return-to-idle timing
- idle motion rotation
- pointer reaction timing
- passive suppression windows
```

This is acceptable as a transitional state, but Attention / Gaze must not be added there.

Boundary note:

```text
Speaking mouth active/source/base mouth/rhythm now comes from Speaking Driver through adapter parameters.
Renderer auto-return-to-idle still bypasses the runtime chain and remains a known transitional risk.
```

### State Semantics Are Still Duplicated

Current semantic mapping appears in:

```text
- Python bridge mapper
- emotion-state.js
- state-mapper.js
- renderer speaking/thinking checks
```

Next cleanup should reduce this drift.

## 5. Next Refactoring Order

Use this order. Do not do a broad rewrite.

### Step 1: Keep Character Runtime Pipeline As The Entry Point

Current file:

```text
character-runtime.js
```

Next change:

```text
Route future attention and speaking-driver outputs through this pipeline.
```

Acceptance:

```text
AvatarController remains a coordinator, not the behavior engine.
```

### Step 2: Add Attention / Gaze System v1

Suggested file:

```text
attention-system.js
```

Inputs:

```text
emotion state
pointer state
recent interaction time
speaking/thinking/idle status
```

Output:

```text
attention target:
  cursor
  user
  down-left
  idle-scan
  away
```

Guardrail:

```text
Do not implement this inside Live2DRenderer.
```

### Step 3: Add Speaking Driver v1

Suggested file:

```text
speaking-driver.js
```

Outputs:

```text
mouth envelope
speaking active/inactive
source: tts / simulated / idle
```

Guardrail:

```text
Renderer executes mouth values but does not decide dialogue state.
```

### Step 4: Extract Live2D Desktop Coordinator From main.py

Suggested file:

```text
app/ui/live2d_desktop_coordinator.py
```

Goal:

```text
Keep app/main.py as a composition root.
```

### Step 5: Model Gallery Fixed Sequence

Suggested file group:

```text
showcase-demo/live2d-prototype/model-gallery-runtime.js
```

Validation models:

```text
Hiyori  - baseline loading and idle/motion proof
Natori  - expression-rich candidate
Custom  - future Xiaoyun or third-party candidate entry
```

Fixed sequence:

```text
idle -> listen -> think -> speak -> happy -> comfort -> idle
```

Each step should record:

```text
semantic state
emotion state
attention target
behavior output
adapter motion
adapter expression
active Live2D motion
active Live2D expression
visible quality notes
```

## 6. Deferred Items

Do not prioritize now:

```text
- complex Memory / Relationship behavior
- gesture / vision control
- final Xiaoyun model production
- large UI beautification
- more agent/tool systems
- direct AI-to-motion control
```

These should wait until runtime boundaries are stable.

## 7. Acceptance For The Next Attention Work

Attention / Gaze System v1 is acceptable only if:

```text
1. It is implemented outside Live2DRenderer.
2. It consumes renderer-neutral state.
3. It outputs semantic attention targets.
4. Debug diagnostics show attention target and source.
5. Mouse tracking changes gaze/head intent without large body translation.
6. Speaking, thinking, idle, and pointer interaction have distinct attention sources.
```

## 8. One-Line Rule

```text
Runtime decides what the character wants to do.
Adapter decides how the active model can do it.
Renderer only performs it.
```
