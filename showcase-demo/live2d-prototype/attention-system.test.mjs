import assert from "node:assert/strict";
import { resolveAttentionState } from "./attention-system.js";

function testSpeakingLooksAtCursorWhenPointerAvailable() {
  assert.deepEqual(
    resolveAttentionState({
      emotionState: {
        emotion: "engaged"
      },
      speakingState: {
        active: true,
        source: "tts"
      },
      pointerState: { available: true }
    }),
    {
      target: "cursor",
      source: "tts",
      gaze: "cursor",
      bodyFollow: "soft",
      intensity: 0.55
    }
  );
}

function testAttentionDoesNotInferSpeakingWithoutSpeakingState() {
  assert.equal(
    resolveAttentionState({
      emotionState: {
        state: "speaking",
        activity: "speak",
        emotion: "engaged"
      },
      pointerState: { available: true }
    }).source,
    "idle"
  );
}

function testPendingTtsKeepsSoftAttentionWithoutSpeakingMouth() {
  assert.deepEqual(
    resolveAttentionState({
      emotionState: {
        state: "speaking",
        activity: "speak",
        emotion: "engaged"
      },
      speakingState: {
        active: false,
        pending: true,
        source: "tts"
      },
      pointerState: { available: true }
    }),
    {
      target: "cursor",
      source: "tts",
      gaze: "cursor",
      bodyFollow: "soft",
      intensity: 0.38
    }
  );
}

function testThinkingLooksDownLeft() {
  assert.deepEqual(
    resolveAttentionState({
      emotionState: {
        state: "thinking",
        activity: "think",
        emotion: "thinking"
      }
    }),
    {
      target: "down-left",
      source: "thinking",
      gaze: "down-left",
      bodyFollow: "minimal",
      intensity: 0.34
    }
  );
}

function testIdleUsesIdleScanFallback() {
  assert.deepEqual(
    resolveAttentionState({
      emotionState: {
        state: "idle",
        activity: "idle",
        emotion: "neutral"
      }
    }),
    {
      target: "idle-scan",
      source: "idle",
      gaze: "idle-scan",
      bodyFollow: "minimal",
      intensity: 0.22
    }
  );
}

function testPointerActiveOverridesStateAttention() {
  assert.deepEqual(
    resolveAttentionState({
      emotionState: {
        state: "thinking",
        activity: "think",
        emotion: "thinking"
      },
      pointerState: {
        available: true,
        active: true,
        x: 0.4,
        y: -0.2
      }
    }),
    {
      target: "cursor",
      source: "pointer",
      gaze: "cursor",
      bodyFollow: "soft",
      intensity: 0.45
    }
  );
}

function testSadLooksAwayWithLowBodyFollow() {
  assert.deepEqual(
    resolveAttentionState({
      emotionState: {
        state: "sad",
        activity: "sad",
        emotion: "sad"
      }
    }),
    {
      target: "away",
      source: "fallback",
      gaze: "down",
      bodyFollow: "none",
      intensity: 0.2
    }
  );
}

testSpeakingLooksAtCursorWhenPointerAvailable();
testAttentionDoesNotInferSpeakingWithoutSpeakingState();
testPendingTtsKeepsSoftAttentionWithoutSpeakingMouth();
testThinkingLooksDownLeft();
testIdleUsesIdleScanFallback();
testPointerActiveOverridesStateAttention();
testSadLooksAwayWithLowBodyFollow();
console.log("attention-system tests passed");
