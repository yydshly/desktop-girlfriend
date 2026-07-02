import assert from "node:assert/strict";
import {
  resolveEmotionalSurfaceState,
  resolveVoiceVisualizerState
} from "./surface-feedback.js";

function testVoiceVisualizerActivatesForTtsPlaying() {
  const visualizer = resolveVoiceVisualizerState({
    speakingState: {
      active: true,
      source: "tts",
      ttsState: "playing",
      mouth: 0.62
    },
    now: 180
  });

  assert.equal(visualizer.visible, true);
  assert.equal(visualizer.state, "playing");
  assert.ok(visualizer.intensity > 0.4);
  assert.equal(visualizer.bars.length, 5);
  assert.ok(visualizer.bars.every((bar) => bar >= 0.12 && bar <= 1));
}

function testVoiceVisualizerFadesOutAfterTtsEnded() {
  const visualizer = resolveVoiceVisualizerState({
    speakingState: {
      active: false,
      source: "tts",
      ttsState: "ended",
      mouth: 0
    },
    now: 180
  });

  assert.equal(visualizer.visible, false);
  assert.equal(visualizer.state, "hidden");
  assert.equal(visualizer.intensity, 0);
}

function testEmotionalSurfaceStatesAreDistinct() {
  assert.equal(resolveEmotionalSurfaceState({ emotionState: { state: "listening" } }).visualIntent, "listening");
  assert.equal(resolveEmotionalSurfaceState({ emotionState: { state: "thinking" } }).visualIntent, "thinking");
  assert.equal(resolveEmotionalSurfaceState({ emotionState: { state: "comfort" } }).visualIntent, "comfort");
  assert.equal(resolveEmotionalSurfaceState({ emotionState: { state: "happy" } }).visualIntent, "happy");
  assert.equal(resolveEmotionalSurfaceState({ emotionState: { state: "error" } }).visualIntent, "error");
  assert.equal(resolveEmotionalSurfaceState({ emotionState: { state: "idle" } }).visualIntent, "idle");
}

function testSpeakingSurfaceOverridesGenericState() {
  const surface = resolveEmotionalSurfaceState({
    emotionState: {
      state: "happy"
    },
    speakingState: {
      active: true,
      source: "tts",
      ttsState: "playing",
      mouth: 0.5
    },
    now: 80
  });

  assert.equal(surface.visualIntent, "speaking");
  assert.equal(surface.visualizer.visible, true);
}

testVoiceVisualizerActivatesForTtsPlaying();
testVoiceVisualizerFadesOutAfterTtsEnded();
testEmotionalSurfaceStatesAreDistinct();
testSpeakingSurfaceOverridesGenericState();
console.log("surface-feedback tests passed");
