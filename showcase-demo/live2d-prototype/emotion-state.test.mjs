import assert from "node:assert/strict";
import {
  mapAvatarStateToEmotionState,
  mapAvatarSequenceToEmotionState,
  mapBridgeMessageToEmotionState,
  mapDialogueTurnToEmotionState,
  mapTtsPlaybackToEmotionState,
  normalizeEmotionState
} from "./emotion-state.js";

function testNormalizeEmotionStateKeepsRendererNeutralFields() {
  assert.deepEqual(
    normalizeEmotionState({
      state: "speaking",
      emotion: "happy",
      intensity: "0.72",
      activity: "reply",
      gaze: "cursor",
      mouth: "0.5",
      motion: "TapBody",
      group: "Idle",
      index: 2
    }),
    {
      state: "speaking",
      emotion: "happy",
      intensity: 0.72,
      activity: "reply",
      gaze: "cursor",
      mouth: 0.5
    }
  );
}

function testAvatarStateMapsToEmotionState() {
  const state = mapAvatarStateToEmotionState({ state: "think", intensity: 0.9 });

  assert.deepEqual(state, {
    state: "thinking",
    emotion: "thinking",
    intensity: 0.9,
    activity: "think",
    gaze: "down-left",
    mouth: 0.05
  });
}

function testAvatarSequenceMapsToSemanticActivity() {
  assert.deepEqual(mapAvatarSequenceToEmotionState({ name: "greet" }), {
    state: "happy",
    emotion: "happy",
    intensity: 0.72,
    activity: "greet",
    gaze: "cursor",
    mouth: 0.28
  });
}

function testDialogueTurnDoesNotExposeMotion() {
  const state = mapDialogueTurnToEmotionState({
    intent: "comfort",
    tts_state: "speaking",
    response_text: "I am here."
  });

  assert.deepEqual(state, {
    state: "comfort",
    emotion: "soft",
    intensity: 0.68,
    activity: "speak",
    gaze: "cursor",
    mouth: 0.65,
    turn: {
      turnId: "",
      userText: "",
      responseText: "I am here.",
      ttsState: "speaking"
    }
  });
  assert.equal("motion" in state, false);
}

function testBridgeMessageFallsBackToIdleEmotionState() {
  assert.deepEqual(mapBridgeMessageToEmotionState({ type: "unknown" }), {
    state: "idle",
    emotion: "neutral",
    intensity: 0.25,
    activity: "idle",
    gaze: "cursor",
    mouth: 0,
    source: "unknown"
  });
}

function testTtsPlaybackPlayingMapsToSpeakingEmotionState() {
  const state = mapTtsPlaybackToEmotionState({
    request_id: "req-1",
    tts_state: "playing",
    source: "tts_controller"
  });

  assert.deepEqual(state, {
    state: "speaking",
    emotion: "engaged",
    intensity: 0.76,
    activity: "speak",
    gaze: "cursor",
    mouth: 0.65,
    turn: {
      turnId: "req-1",
      source: "tts_controller",
      ttsState: "playing"
    }
  });
}

function testTtsPlaybackEndedMapsToIdleEmotionStateButKeepsTurnState() {
  const state = mapBridgeMessageToEmotionState({
    type: "tts.playback",
    payload: {
      request_id: "req-1",
      tts_state: "ended",
      source: "tts_controller"
    }
  });

  assert.equal(state.state, "idle");
  assert.equal(state.activity, "idle");
  assert.equal(state.mouth, 0);
  assert.equal(state.turn.ttsState, "ended");
  assert.equal(state.source, "tts.playback");
}

testNormalizeEmotionStateKeepsRendererNeutralFields();
testAvatarStateMapsToEmotionState();
testAvatarSequenceMapsToSemanticActivity();
testDialogueTurnDoesNotExposeMotion();
testBridgeMessageFallsBackToIdleEmotionState();
testTtsPlaybackPlayingMapsToSpeakingEmotionState();
testTtsPlaybackEndedMapsToIdleEmotionStateButKeepsTurnState();
console.log("emotion-state tests passed");
