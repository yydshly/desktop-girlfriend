import assert from "node:assert/strict";
import {
  calculateMouthEnvelope,
  resolveSpeakingState
} from "./speaking-driver.js";

function testTtsSpeakingActivatesSpeakingDriver() {
  const state = resolveSpeakingState({
    emotionState: {
      state: "speaking",
      activity: "speak",
      mouth: 0.65,
      turn: {
        ttsState: "speaking"
      }
    },
    now: 0
  });

  assert.equal(state.active, true);
  assert.equal(state.source, "tts");
  assert.equal(state.rhythm, "simulated");
  assert.equal(state.baseMouth, 0.65);
  assert.ok(state.mouth > 0);
}

function testStateSpeakingActivatesWithoutTts() {
  assert.deepEqual(
    resolveSpeakingState({
      emotionState: {
        state: "speaking",
        activity: "speak",
        mouth: 0.65
      },
      now: 0
    }),
    {
      active: true,
      source: "state",
      mouth: 0.533,
      baseMouth: 0.65,
      rhythm: "simulated"
    }
  );
}

function testIdleSpeakingDriverKeepsMouthStable() {
  assert.deepEqual(
    resolveSpeakingState({
      emotionState: {
        state: "idle",
        activity: "idle",
        mouth: 0
      },
      now: 1000
    }),
    {
      active: false,
      source: "idle",
      mouth: 0,
      baseMouth: 0,
      rhythm: "none"
    }
  );
}

function testMouthEnvelopeStaysInRange() {
  assert.equal(calculateMouthEnvelope(0.65, 0), 0.533);
  assert.ok(calculateMouthEnvelope(0.65, 300) <= 1);
  assert.ok(calculateMouthEnvelope(0.65, 300) >= 0.12);
}

testTtsSpeakingActivatesSpeakingDriver();
testStateSpeakingActivatesWithoutTts();
testIdleSpeakingDriverKeepsMouthStable();
testMouthEnvelopeStaysInRange();
console.log("speaking-driver tests passed");
