import assert from "node:assert/strict";
import { mapAvatarState, mapDialogueTurn } from "./state-mapper.js";

function testDialogueTurnCreatesShortReplyBubble() {
  const state = mapDialogueTurn({
    turn_id: "turn-1",
    user_text: "hello",
    response_text: "  我在这里，慢慢说就好。  ",
    tts_state: "speaking"
  });

  assert.deepEqual(state.bubble, {
    text: "我在这里，慢慢说就好。",
    tone: "reply",
    ttlMs: 5200
  });
}

function testThinkingStateCreatesThinkingBubble() {
  const state = mapAvatarState({ state: "think" });

  assert.deepEqual(state.bubble, {
    text: "让我想想...",
    tone: "thinking",
    ttlMs: 3200
  });
}

testDialogueTurnCreatesShortReplyBubble();
testThinkingStateCreatesThinkingBubble();
console.log("state-mapper tests passed");
