import assert from "node:assert/strict";
import { buildCharacterRuntimeState } from "./character-runtime.js";

function testRuntimeStateBuildsBehaviorAndModelCommands() {
  const state = buildCharacterRuntimeState({
    previousState: {
      source: "boot"
    },
    mappedState: {
      state: "speaking",
      source: "avatar.state"
    },
    profile: {
      mappings: {
        actions: {
          idle: { group: "Idle", index: 0 },
          speak: { group: "Talk", index: 2 }
        },
        expressions: {
          engaged: "smile"
        }
      }
    },
    updatedAt: "2026-07-02T00:00:00.000Z"
  });

  assert.equal(state.source, "avatar.state");
  assert.deepEqual(state.emotionState, {
    state: "speaking",
    emotion: "engaged",
    intensity: 0.76,
    activity: "speak",
    gaze: "cursor",
    mouth: 0.65
  });
  assert.deepEqual(state.behavior, {
    action: "speak",
    expression: "engaged",
    intensity: 0.76,
    gaze: "cursor",
    mouth: 0.65
  });
  assert.deepEqual(state.modelCommands.motion, {
    group: "Talk",
    index: 2,
    action: "speak"
  });
  assert.equal(state.updatedAt, "2026-07-02T00:00:00.000Z");
}

function testExplicitEmotionStateOverridesMappedStatePreset() {
  const state = buildCharacterRuntimeState({
    mappedState: {
      state: "idle"
    },
    emotionState: {
      state: "thinking",
      emotion: "thinking",
      intensity: 0.48,
      activity: "think",
      gaze: "down-left",
      mouth: 0.05,
      source: "dialogue.turn"
    },
    profile: {
      mappings: {
        actions: {
          think: { group: "Idle", index: 3 }
        },
        expressions: {
          thinking: "think"
        }
      }
    },
    updatedAt: "2026-07-02T00:00:00.000Z"
  });

  assert.equal(state.emotionState.source, "dialogue.turn");
  assert.deepEqual(state.modelCommands.motion, {
    group: "Idle",
    index: 3,
    action: "think"
  });
  assert.deepEqual(state.modelCommands.expression, {
    name: "think",
    semantic: "thinking"
  });
}

testRuntimeStateBuildsBehaviorAndModelCommands();
testExplicitEmotionStateOverridesMappedStatePreset();
console.log("character-runtime tests passed");
