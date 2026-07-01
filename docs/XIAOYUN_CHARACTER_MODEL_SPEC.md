# Xiaoyun Character Model Spec

This document defines the model target for Xiaoyun. It is the product-facing
asset standard that should guide model search, Live2D customization, and later
3D avatar exploration.

## Product Target

Xiaoyun is a desktop AI companion, not a streamer avatar and not a short-form
animation character. The model must look comfortable during long idle periods,
react softly to conversation, and support low-frequency emotional changes.

The first production target is Live2D because it is realistic for desktop
rendering, transparent windows, model replacement, expression control, and
incremental customization. A later 3D/VRM track can be explored after the
Live2D character standard is stable.

## Visual Direction

The character should feel:

- warm, present, and calm
- clear enough to read at desktop scale
- expressive through subtle face and posture changes
- suitable for always-on desktop presence
- distinct from a game battle character or livestream performer

Avoid models that depend on:

- large camera-facing performance gestures
- frequent exaggerated motion
- heavy outfit motion that distracts during idle
- complex scene backgrounds baked into the avatar
- aggressive facial expressions as the default state

## Required Runtime States

These are the minimum semantic states the model must support through
`profile.json` mappings.

| State | Use | Required Output |
| --- | --- | --- |
| `idle` | Normal desktop presence | calm breathing, occasional blink, small posture shift |
| `listen` | User is speaking or typing | attentive gaze, slight head focus |
| `think` | AI is preparing a response | subtle downward/side gaze, low mouth value |
| `speak` | AI is responding | mouth open control, gentle upper-body motion |
| `happy` | positive reaction | soft smile, small brightening motion |
| `sad` | user or AI low mood | softened eyes, reduced movement |
| `comfort` | emotional support | warm expression, slow calming motion |
| `greet` | first appearance / return | small wave or friendly acknowledgement |

## Required Live2D Capabilities

The model package should ideally include:

- `.model3.json` and `.moc3`
- multiple idle motions
- at least one short greet motion
- at least one speak-friendly motion
- expression files for neutral, happy, thinking, sad, soft, engaged
- `ParamMouthOpenY` or equivalent lip-sync parameter
- eye-ball parameters or a focus controller-compatible setup
- breath/body parameters for subtle movement
- physics for hair/clothes, tuned to be gentle rather than noisy

If a model does not include expression files, it can still be used as a
technical baseline, but it should not be considered a strong Xiaoyun candidate.

## Dynamic Quality Bar

The model should be scored by behavior, not only by still-image appeal.

| Dimension | Good | Weak |
| --- | --- | --- |
| Idle quality | can sit on desktop for minutes without fatigue | frozen, noisy, or repetitive |
| Expression coverage | states are visually distinguishable but soft | only neutral, or overly dramatic |
| Motion controllability | motions can be mapped to semantic actions | random, unclear, or hard-coded only |
| Speech readiness | mouth parameter works independently | only baked talking motion |
| Gaze behavior | can look at cursor/user naturally | eyes fixed or uncanny |
| Desktop fit | readable at small scale | needs full-screen framing |

## Profile Contract

Every Xiaoyun candidate must provide a `profile.json` that maps Character
Contract semantics to model-specific assets.

Minimum shape:

```json
{
  "schemaVersion": 1,
  "displayName": "Candidate Name",
  "desktopPlacement": {
    "scaleMultiplier": 1,
    "xOffsetRatio": 0,
    "yRatio": 0.55
  },
  "mappings": {
    "actions": {
      "idle": { "group": "Idle", "index": 0 },
      "think": { "group": "Idle", "index": 1 },
      "speak": { "group": "TapBody", "index": 0 },
      "happy": { "group": "TapBody", "index": 0 },
      "comfort": { "group": "Idle", "index": 2 },
      "greet": { "group": "TapBody", "index": 0 }
    },
    "expressions": {
      "neutral": "",
      "happy": "smile",
      "thinking": "thinking",
      "sad": "sad",
      "soft": "soft",
      "engaged": "smile"
    }
  }
}
```

The AI layer must not depend on these model-specific names. It should only
produce emotion and behavior intent. The adapter is responsible for translating
intent into this profile.

## Candidate Model Strategy

Use three model categories during evaluation:

1. Baseline sample model
   - Purpose: proves runtime loading and adapter wiring.
   - Current example: Hiyori.
   - It is not the final visual standard.

2. Rich Live2D candidate
   - Purpose: checks whether better motions and expressions improve presence.
   - Needs a clear license and complete model package.

3. Xiaoyun custom target
   - Purpose: defines the desired final asset.
   - Production should be based on this document and the Character Contract.

Do not judge the final product by the baseline model. Judge baseline only by
whether the runtime and diagnostics behave correctly.

## Evaluation Sequence

Model Gallery should use a fixed sequence:

```text
idle -> listen -> think -> speak -> happy -> comfort -> idle
```

For each step, record:

- semantic state
- behavior planner output
- adapter motion
- adapter expression
- adapter parameters
- active Live2D motion
- active Live2D expression
- visible quality notes

This lets us identify whether a weak result is caused by the model asset, the
profile mapping, or the runtime.

## Near-Term Decision

The next development milestone is not a prettier UI. It is a model evaluation
loop:

1. keep Hiyori as baseline
2. add Model Gallery sequence playback
3. test at least one stronger Live2D candidate
4. update profile mappings from observed results
5. decide whether to continue with a found model or commission/customize Xiaoyun

