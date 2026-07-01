import assert from "node:assert/strict";
import { mapAvatarState, mapDialogueTurn } from "./state-mapper.js";

function testCanonicalStateNamesAreStable() {
  assert.equal(mapAvatarState({ state: "thinking" }).state, "thinking");
  assert.equal(mapAvatarState({ state: "speaking" }).state, "speaking");
  assert.equal(mapAvatarState({ state: "listening" }).state, "listening");
}

function testLegacyStateAliasesNormalizeToCanonicalStates() {
  assert.equal(mapAvatarState({ state: "think" }).state, "thinking");
  assert.equal(mapAvatarState({ state: "speak" }).state, "speaking");
}

function testDialogueTurnCreatesShortReplyBubble() {
  const state = mapDialogueTurn({
    turn_id: "turn-1",
    user_text: "hello",
    response_text: "  我在这里，慢慢说就好。 ",
    tts_state: "speaking"
  });

  assert.deepEqual(state.bubble, {
    text: "我在这里，慢慢说就好。",
    tone: "reply",
    ttlMs: 5200
  });
}

function testThinkingStateCreatesThinkingBubble() {
  const state = mapAvatarState({ state: "thinking" });

  assert.deepEqual(state.bubble, {
    text: "让我想想...",
    tone: "thinking",
    ttlMs: 3200
  });
}

function testStateCarriesStableVisualIntent() {
  assert.equal(mapAvatarState({ state: "speaking" }).visualIntent, "speaking");
  assert.equal(mapAvatarState({ state: "happy" }).visualIntent, "happy");
}

function testDialogueTurnCarriesSpeakingVisualIntent() {
  const state = mapDialogueTurn({
    response_text: "好的，我听见了。",
    tts_state: "speaking"
  });

  assert.equal(state.visualIntent, "speaking");
}

testCanonicalStateNamesAreStable();
testLegacyStateAliasesNormalizeToCanonicalStates();
testDialogueTurnCreatesShortReplyBubble();
testThinkingStateCreatesThinkingBubble();
testStateCarriesStableVisualIntent();
testDialogueTurnCarriesSpeakingVisualIntent();
console.log("state-mapper tests passed");
