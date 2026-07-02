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
      closing: true,
      source: "tts",
      ttsState: "ended",
      mouth: 0
    },
    now: 180
  });

  assert.equal(visualizer.visible, true);
  assert.equal(visualizer.active, false);
  assert.equal(visualizer.state, "fading");
  assert.equal(visualizer.intensity, 0);
}

function testVoiceVisualizerShowsPendingBeforeTtsPlaying() {
  const visualizer = resolveVoiceVisualizerState({
    speakingState: {
      active: false,
      pending: true,
      source: "tts",
      ttsState: "started",
      mouth: 0.04
    },
    now: 180
  });

  assert.equal(visualizer.visible, true);
  assert.equal(visualizer.active, false);
  assert.equal(visualizer.state, "pending");
  assert.ok(visualizer.intensity > 0);
  assert.ok(visualizer.intensity < 0.3);
  assert.equal(visualizer.bars.length, 5);
}

function testEmotionalSurfaceStatesAreDistinct() {
  assert.equal(resolveEmotionalSurfaceState({ emotionState: { state: "listening" } }).visualIntent, "listening");
  assert.equal(resolveEmotionalSurfaceState({ emotionState: { state: "thinking" } }).visualIntent, "thinking");
  assert.equal(resolveEmotionalSurfaceState({ emotionState: { state: "comfort" } }).visualIntent, "comfort");
  assert.equal(resolveEmotionalSurfaceState({ emotionState: { state: "happy" } }).visualIntent, "happy");
  assert.equal(resolveEmotionalSurfaceState({ emotionState: { state: "error" } }).visualIntent, "error");
  assert.equal(resolveEmotionalSurfaceState({ emotionState: { state: "idle" } }).visualIntent, "idle");
}

function testPendingSurfaceUsesPreparingIntent() {
  const surface = resolveEmotionalSurfaceState({
    emotionState: {
      state: "speaking"
    },
    speakingState: {
      active: false,
      pending: true,
      source: "tts",
      ttsState: "started",
      mouth: 0.04
    },
    now: 80
  });

  assert.equal(surface.visualIntent, "preparing");
  assert.equal(surface.visualizer.visible, true);
  assert.equal(surface.visualizer.state, "pending");
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
testVoiceVisualizerShowsPendingBeforeTtsPlaying();
testEmotionalSurfaceStatesAreDistinct();
testPendingSurfaceUsesPreparingIntent();
testSpeakingSurfaceOverridesGenericState();
console.log("surface-feedback tests passed");
