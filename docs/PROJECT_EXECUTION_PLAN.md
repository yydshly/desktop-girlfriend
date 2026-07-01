# Desktop Girlfriend Current Project Execution Plan

This document is the current engineering map for the desktop-girlfriend project. It is intentionally more concrete than a vision document. Future implementation units should align with this plan unless the plan is explicitly updated.

## 1. Project Positioning

This project should no longer be understood as a normal Live2D showcase page or as a search for a prettier model.

The actual target is:

```text
Build a desktop AI companion system with replaceable Live2D models, driven by emotion, attention, and behavior.
```

Target flow:

```text
User input / voice / mouse / desktop event
  -> Dialogue / App Event
  -> Emotion State
  -> Attention / Gaze
  -> Behavior Planner
  -> Model Adapter
  -> Live2D Renderer
  -> Desktop Presence
```

The model is not the whole project. It is the presentation shell. The project body is:

```text
Character Runtime Core
+ Live2D Model Layer
+ Desktop Presence
+ AI Interaction
```

## 2. Current Status

The current branch has completed or mostly completed:

```text
1. Live2D model3.json loading path
2. Independent PySide6 WebView desktop character window
3. WebSocket bridge from Python main app to Live2D page
4. Live2D desktop process launch/stop
5. Model directory scan and model catalog
6. profile.json action/expression mapping
7. Character Contract v1
8. Emotion State module
9. Behavior Planner module
10. Model Adapter module
11. Hiyori baseline model
12. Natori expression candidate model
13. Model intake / candidate scoring / debug panel foundation
14. Passive behavior scheduling for hover, ambient, tap, and suppression windows
15. Behavior event log in the debug panel
16. Character Runtime pipeline entrypoint in `character-runtime.js`
17. Motion Probe overrides routed through effective profile into Model Adapter
18. Profile-aware model candidate scoring for non-Idle / non-TapBody motion names
```

This means the project is currently between:

```text
Phase A: Live2D technical integration complete
Phase B: Character Runtime convergence in progress
```

It has not yet reached:

```text
digital-human-like interaction
stable desktop product experience
long-term companion behavior
```

## 3. Core Problems Now

### 3.1 `app/main.py` Is Too Heavy

`app/main.py` currently owns too many responsibilities:

```text
- QApplication initialization
- EventBus / StateMachine initialization
- Live2D bridge server initialization
- Live2D bridge dispatcher initialization
- Live2D desktop process initialization
- model catalog scan
- model selection persistence
- Live2D scale / opacity / visibility control
- Live2D process restart
- opening model directory
- main window callback wiring
```

This can run, but it will become harder to maintain.

Direction:

```text
Extract Live2DDesktopController / Live2DDesktopCoordinator.
Keep main.py as a composition root.
Do not keep adding feature logic to main.py.
```

### 3.2 State / Emotion Mapping Is Duplicated

Semantic mapping currently appears in several places:

```text
Python bridge mapper
emotion-state.js
state-mapper.js
renderer speaking/thinking checks
```

This can cause semantic drift:

```text
speaking / reply / speak / engaged
listening / listen / think
comfort / soft
```

Direction:

```text
emotion-state.js should become the only renderer-neutral semantic state source.
state-mapper.js should keep only UI bubble / readout support.
Do not let multiple modules redefine complete state presets.
```

### 3.3 Character Runtime Boundary Is Not Clear Enough

Behavior decisions are currently spread across:

```text
AvatarController
runtime-app.js
Live2DRenderer
state-mapper.js
behavior-planner.js
passive-behavior-scheduler.js
```

Live2DRenderer still contains or coordinates:

```text
passive behavior
hover reaction
ambient gesture
idle rotation
return to idle
speaking mouth pulse
pointer reaction
```

Not all of that is renderer responsibility.

Direction:

```text
Converge Character Runtime boundaries before adding Attention / Gaze logic.
Do not put Attention logic directly into Live2DRenderer.
```

Target boundary:

```text
Character Runtime Core:
  decides emotion / attention / behavior / timing

Model Adapter:
  translates semantic behavior into profile-backed model commands

Renderer:
  executes model commands and writes Cubism parameters, motions, expressions, and drawing
```

### 3.4 Motion Binding Override And Model Adapter Path May Diverge

The runtime supports Motion Probe and localStorage motion binding overrides.

Risk:

```text
If adapter commands already come from profile, renderer fallback overrides may not affect adapter-driven states.
```

Direction:

```text
motion override should become part of the effective profile.
Model Adapter should output commands from the effective profile.
Do not let overrides only affect renderer fallback.
```

Target path:

```text
profile.mappings.actions
+ localStorage motion override
= effectiveProfile.mappings.actions
-> model-adapter
-> renderer
```

### 3.5 Idle / TapBody Assumptions Still Exist

Some logic still treats official sample motion groups as generic:

```text
Idle
TapBody
```

That works for Hiyori and Natori, but is unreliable for commercial or custom models.

Direction:

```text
Idle / TapBody should be fallback heuristics only.
The real source of truth should be profile mappings.
Candidate evaluation should first check required semantic actions and whether the mapped group/index exists.
```

### 3.6 profile.json Needs Parameter Alias And Range Support

Current profile supports:

```text
actions
expressions
desktopPlacement
```

Missing for future models:

```text
parameters
parameter ranges
expression aliases
```

Reason:

Not every model will use standard Cubism parameter names:

```text
ParamMouthOpenY
ParamBreath
ParamAngleX
ParamEyeBallX
```

Target direction:

```json
{
  "parameters": {
    "mouthOpen": "ParamMouthOpenY",
    "mouthForm": "ParamMouthForm",
    "breath": "ParamBreath",
    "headX": "ParamAngleX",
    "headY": "ParamAngleY",
    "headZ": "ParamAngleZ",
    "eyeX": "ParamEyeBallX",
    "eyeY": "ParamEyeBallY"
  }
}
```

Keep standard Cubism parameters as defaults, but allow profile-specific aliases.

### 3.7 Bridge Is Mostly One-Way

Python can send state into the Live2D page, but Python does not yet know:

```text
Live2D runtime is actually ready
SDK loaded successfully
model failed to load
current active motion
current active expression
```

Direction:

```text
Add a minimal reverse status channel later.
```

Minimum useful events:

```text
live2d.runtime_ready
live2d.model_loaded
live2d.model_error
live2d.motion_played
live2d.expression_applied
```

## 4. Recommended Milestone Route

Do not keep adding unrelated features. Use this route:

```text
M1   Live2D runnable foundation                         done
M2   Replaceable model + profile / intake               done
M2.5 Character Runtime Boundary convergence             current priority
M3   Attention / Gaze System v1
M4   Speaking Driver v1
M5   Model Gallery fixed-sequence evaluation
M6   Desktop Presence polish
M7   Companion Interaction v1
M8   Xiaoyun custom Live2D model
M9   Memory / Relationship v1
M10  Gesture / Vision Control
```

Key adjustments:

```text
1. Character Runtime Boundary must happen before Attention.
2. Model Gallery should move earlier, not wait until the final model.
3. Xiaoyun custom model can be later, while candidate model evaluation starts now.
4. Memory / Relationship / Gesture should wait.
```

## 5. Current Priorities

### P0. Project Execution Map

Status: done in this document.

This document is not a vision document. It is the engineering map.

It defines:

```text
1. project target
2. current state
3. module boundaries
4. milestone route
5. current priorities
6. deferred items
7. acceptance criteria
8. architecture guard rules
```

### P0. Character Runtime Boundary Convergence

Goal:

Do not do a large rewrite. First clarify ownership and create the smallest boundaries needed for the next modules.

Required flow:

```text
bridge message -> emotion state
emotion state -> attention target
emotion/attention -> behavior
behavior -> model command
model command -> renderer
renderer -> actual Live2D execution
```

Acceptance:

```text
1. Renderer no longer gains new high-level behavior decisions.
2. emotion-state is the single semantic state source.
3. state-mapper no longer duplicates full state presets.
4. behavior log can explain each action source.
5. passive / hover / ambient / idle / speaking ownership is explicit.
```

Current boundary document:

```text
docs/CHARACTER_RUNTIME_BOUNDARY.md
```

### P1. Fix Motion Override And Adapter Path

Status: done.

Goal:

Motion Probe saved overrides must affect adapter-driven state output.

Acceptance:

```text
1. User binds speak to a motion group/index through Motion Probe.
2. User triggers speaking state.
3. Adapter command uses the new group/index.
4. Debug panel shows the override is active.
```

### P1. Make Model Evaluation Profile-Aware

Status: done.

Goal:

Model scoring should not strongly depend on `Idle` / `TapBody` names.

Acceptance:

```text
1. Required actions are checked from profile mappings.
2. Mapped group/index must exist in the package.
3. Idle / TapBody are fallback hints only.
4. Non-official sample naming can be evaluated correctly.
```

### P1. Attention / Gaze System v1

Prerequisite:

Complete Character Runtime Boundary documentation and initial convergence first.

Do not write this directly into Live2DRenderer.

Suggested module:

```text
attention-system.js
```

Inputs:

```text
emotion state
pointer state
speaking/thinking/idle state
recent user interaction
```

Output:

```text
attention target:
- cursor
- user
- down-left
- idle-scan
- away
```

Acceptance:

```text
1. Mouse movement makes gaze follow without excessive body movement.
2. Speaking prefers user / cursor gaze.
3. Thinking shifts gaze away.
4. Idle has natural scan.
5. Debug panel shows attention target and source.
```

### P1. Speaking Driver v1

Goal:

Upgrade speaking from a simple mouth preset into an explainable speaking driver.

Acceptance:

```text
1. Speaking state drives rhythmic mouth movement.
2. TTS playback state can drive mouth.
3. End of speech returns naturally to idle.
4. Passive behavior does not interrupt speaking.
5. Speaking behavior source is visible in the behavior log.
```

### P2. Model Gallery Fixed-Sequence Evaluation

Goal:

Compare Hiyori / Natori / a third candidate with the same sequence.

Fixed sequence:

```text
idle -> listen -> think -> speak -> happy -> comfort -> idle
```

Each step records:

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

Purpose:

Distinguish whether a problem comes from:

```text
1. model asset
2. profile mapping
3. runtime behavior
4. renderer execution
```

## 6. Deferred Items

Do not prioritize now:

```text
1. large-scale UI beautification
2. complex Memory / Relationship
3. Gesture / Vision Control
4. final Xiaoyun custom model production
5. more Agent tool ability
6. complex active companion strategy
```

These matter, but they should wait until the Character Runtime chain is stable.

## 7. Architecture Guard Rules

All future changes must follow:

```text
1. AI / Dialogue must not directly call model motion / expression.
2. Emotion State must be renderer-neutral.
3. Attention / Gaze is a runtime decision, not renderer-local temporary logic.
4. Behavior Planner outputs semantic behavior, not concrete motion group/index.
5. Model Adapter is the only layer that translates semantic behavior into model-specific commands.
6. profile.json describes model capabilities, mappings, placement, and parameter aliases. It must not contain business logic.
7. Live2DRenderer executes commands. It must not keep accumulating high-level business decisions.
8. main.py is the composition root. It must not keep accumulating feature logic.
9. Model scoring must be based on the profile contract, not fixed official sample naming.
10. New behavior must be explainable through debug panel / behavior log.
```

## 8. One-Line Conclusion

The current project is no longer:

```text
find a model and make it move
```

The current project is:

```text
build a replaceable-model desktop digital companion system driven by emotion and attention
```

Next steps:

```text
1. Keep this PROJECT_EXECUTION_PLAN.md as the project map.
2. Converge Character Runtime Boundary.
3. Implement Attention / Gaze System v1.
4. Implement Speaking Driver v1.
5. Use Model Gallery fixed sequence to evaluate model and runtime limits.
```
