# Custom Live2D Model Intake Guide

This prototype is ready for a dedicated Xiaoyun-style Live2D model. Put custom models under:

```text
showcase-demo/live2d-prototype/assets/models/custom/<ModelName>/
```

Expected entry:

```text
assets/models/custom/<ModelName>/<ModelName>.model3.json
assets/models/custom/<ModelName>/profile.json
```

## Required Model Package

The `.model3.json` package must include:

- `FileReferences.Moc`
- at least one texture
- at least one motion

Recommended for a desktop companion:

- `Groups` entry for `LipSync`, ideally `ParamMouthOpenY`
- `Groups` entry for `EyeBlink`, ideally both left and right eye parameters
- physics file for hair and clothing softness
- several low-intensity idle motions

## Required Profile Contract

`profile.json` is the adapter between the product behavior system and the model-specific assets. The AI and dialogue layers should never call model motion names directly.

```json
{
  "schemaVersion": 1,
  "displayName": "Xiaoyun",
  "desktopPlacement": {
    "scaleMultiplier": 1,
    "xOffsetRatio": 0,
    "yRatio": 0.54,
    "pointerFollowXRatio": 0.006,
    "pointerFollowYRatio": 0.004,
    "headTrackingMultiplier": 1.1,
    "eyeTrackingMultiplier": 1.2,
    "bodyTrackingMultiplier": 0.45,
    "ambientGestureIntervalMs": 9000
  },
  "mappings": {
    "actions": {
      "idle": { "group": "Idle", "index": 0 },
      "greet": { "group": "Wave", "index": 0 },
      "listen": { "group": "Idle", "index": 1 },
      "think": { "group": "Idle", "index": 2 },
      "reply": { "group": "TapBody", "index": 0 },
      "comfort": { "group": "Idle", "index": 3 },
      "sad": { "group": "Idle", "index": 4 },
      "happy": { "group": "TapBody", "index": 1 },
      "speak": { "group": "TapBody", "index": 2 }
    },
    "expressions": {
      "neutral": "neutral",
      "happy": "smile",
      "thinking": "thinking",
      "sad": "sad",
      "soft": "soft",
      "engaged": "engaged"
    }
  }
}
```

## Acceptance Rules

The browser debug panel now shows both candidate score and intake status.

- `intake ready`: model can become the active desktop character.
- `intake usable-with-warnings`: model can run, but some quality features are missing.
- `intake blocked`: model/profile must be fixed before it should be used.

Blocking issues include:

- missing `Moc`, texture, or motion assets
- invalid profile contract
- required action missing from `mappings.actions`
- action mapping points to a missing motion group/index
- expression mapping points to a missing expression asset

Warnings include:

- missing expression mapping
- missing desktop placement tuning
- missing lip sync, eye blink, or physics

## How To Test A New Model

1. Copy the model folder into `assets/models/custom/<ModelName>/`.
2. Add `profile.json` next to the model entry.
3. Open the browser prototype.
4. Set model URL to:

```text
./assets/models/custom/<ModelName>/<ModelName>.model3.json
```

5. Check the right panel:

- `Capabilities`
- texture preview
- candidate score
- intake status
- behavior event log

6. Use Motion Probe to find better motion indexes.
7. Use Interaction Tuning to adjust gaze/body/move/idle timing.
8. Copy the tuning snippet back into `profile.json`.
