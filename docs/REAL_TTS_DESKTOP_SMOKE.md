# Real TTS Desktop Smoke

This checklist verifies the real Python TTS playback lifecycle drives the Live2D web runtime without bypassing the runtime chain.

## Scope

- Python `TTSController` emits playback lifecycle only.
- Bridge broadcasts `tts.playback` events.
- Web runtime resolves speaking state, mouth, mouthForm, attention, behavior, adapter parameters, and surface feedback.
- Renderer only executes parameters and visual state.

## Checklist

1. Start the desktop app.
2. Send an assistant reply that triggers TTS.
3. Confirm the debug/runtime chain shows `tts started`.
4. Confirm the avatar enters preparing state: soft attention, low mouth value, pending voice visualizer.
5. Confirm playback changes to `tts playing`.
6. Confirm mouthOpen and mouthForm keep changing while audio plays.
7. Confirm the voice visualizer is visible and active only during playing.
8. Wait for playback to finish.
9. Confirm `tts ended`, mouth and mouthForm return to zero, visualizer fades, and stage returns to idle.
10. Trigger another reply and press stop during playback.
11. Confirm `tts interrupted`, mouth closes, visualizer fades, and no speaking state stays active.
12. Trigger or simulate a TTS error.
13. Confirm `tts error`, stage enters error surface state, mouth closes, and visualizer fades.

## Expected Event Flow

```text
assistant reply
  -> tts.playback started
  -> runtime preparing / pending visualizer
  -> tts.playback playing
  -> speaking-driver active / mouth rhythm / voice visualizer active
  -> tts.playback ended
  -> mouth zero / mouthForm zero / visualizer fading / idle stage
```

## Fallback Check

If a `dialogue.turn` arrives with simulated `tts_state=speaking` but real playback never follows, the simulated speaking state must timeout and return to idle.

```text
dialogue.turn speaking
  -> simulated rhythm
  -> no real tts.playback playing
  -> fallback timeout
  -> mouth zero / mouthForm zero / visualizer fading / idle stage
```
