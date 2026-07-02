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
  const state = resolveSpeakingState({
    emotionState: {
      state: "speaking",
      activity: "speak",
      mouth: 0.65
    },
    now: 0
  });

  assert.equal(state.active, true);
  assert.equal(state.source, "state");
  assert.equal(state.ttsState, "none");
  assert.equal(state.mouth, 0.533);
  assert.equal(state.baseMouth, 0.65);
  assert.equal(state.rhythm, "simulated");
  assert.equal(state.mouthForm, 0.096);
}

function testIdleSpeakingDriverKeepsMouthStable() {
  const state = resolveSpeakingState({
    emotionState: {
      state: "idle",
      activity: "idle",
      mouth: 0
    },
    now: 1000
  });

  assert.equal(state.active, false);
  assert.equal(state.source, "idle");
  assert.equal(state.ttsState, "none");
  assert.equal(state.mouth, 0);
  assert.equal(state.baseMouth, 0);
  assert.equal(state.rhythm, "none");
  assert.equal(state.mouthForm, 0);
}

function testTtsPlayingKeepsSpeakingActiveAndVariesMouthForm() {
  const first = resolveSpeakingState({
    emotionState: {
      state: "speaking",
      activity: "speak",
      mouth: 0.65,
      turn: { ttsState: "playing", source: "tts_controller" }
    },
    now: 120
  });
  const second = resolveSpeakingState({
    emotionState: {
      state: "speaking",
      activity: "speak",
      mouth: 0.65,
      turn: { ttsState: "playing" }
    },
    now: 260
  });

  assert.equal(first.active, true);
  assert.equal(first.source, "tts");
  assert.equal(first.ttsSource, "tts_controller");
  assert.equal(first.ttsState, "playing");
  assert.notEqual(first.mouth, second.mouth);
  assert.notEqual(first.mouthForm, second.mouthForm);
}

function testTtsStartedIsPendingWithoutObviousMouthMotion() {
  const state = resolveSpeakingState({
    emotionState: {
      state: "speaking",
      activity: "speak",
      mouth: 0.65,
      turn: { ttsState: "started", source: "tts_controller" }
    },
    now: 120
  });

  assert.equal(state.active, false);
  assert.equal(state.pending, true);
  assert.equal(state.source, "tts");
  assert.equal(state.ttsSource, "tts_controller");
  assert.equal(state.ttsState, "started");
  assert.equal(state.rhythm, "pending");
  assert.equal(state.mouth, 0.04);
  assert.equal(state.mouthForm, 0);
}

function testDialogueFallbackExpiresWithoutRealTtsPlayback() {
  const state = resolveSpeakingState({
    emotionState: {
      state: "speaking",
      activity: "speak",
      mouth: 0.65,
      turn: {
        ttsState: "speaking",
        source: "dialogue.turn",
        receivedAt: 0,
        fallbackTimeoutMs: 1000
      }
    },
    now: 1400
  });

  assert.equal(state.active, false);
  assert.equal(state.pending, false);
  assert.equal(state.closing, true);
  assert.equal(state.fallbackExpired, true);
  assert.equal(state.source, "tts");
  assert.equal(state.ttsState, "ended");
  assert.equal(state.rhythm, "none");
  assert.equal(state.mouth, 0);
  assert.equal(state.mouthForm, 0);
}

function testTtsEndedAndInterruptedCloseMouth() {
  for (const ttsState of ["ended", "interrupted"]) {
    const state = resolveSpeakingState({
      emotionState: {
        state: "speaking",
        activity: "speak",
        mouth: 0.65,
        turn: { ttsState }
      },
      now: 400
    });

    assert.equal(state.active, false);
    assert.equal(state.closing, true);
    assert.equal(state.source, "tts");
    assert.equal(state.ttsState, ttsState);
    assert.equal(state.mouth, 0);
    assert.equal(state.mouthForm, 0);
  }
}

function testTtsErrorClosesMouthButKeepsTtsSource() {
  const state = resolveSpeakingState({
    emotionState: {
      state: "error",
      activity: "sad",
      mouth: 0.2,
      turn: { ttsState: "error" }
    },
    now: 400
  });

  assert.equal(state.active, false);
  assert.equal(state.source, "tts");
  assert.equal(state.ttsState, "error");
  assert.equal(state.mouth, 0);
  assert.equal(state.mouthForm, 0);
}

function testMouthEnvelopeStaysInRange() {
  assert.equal(calculateMouthEnvelope(0.65, 0), 0.533);
  assert.ok(calculateMouthEnvelope(0.65, 300) <= 1);
  assert.ok(calculateMouthEnvelope(0.65, 300) >= 0.12);
}

testTtsSpeakingActivatesSpeakingDriver();
testStateSpeakingActivatesWithoutTts();
testIdleSpeakingDriverKeepsMouthStable();
testTtsPlayingKeepsSpeakingActiveAndVariesMouthForm();
testTtsStartedIsPendingWithoutObviousMouthMotion();
testDialogueFallbackExpiresWithoutRealTtsPlayback();
testTtsEndedAndInterruptedCloseMouth();
testTtsErrorClosesMouthButKeepsTtsSource();
testMouthEnvelopeStaysInRange();
console.log("speaking-driver tests passed");
