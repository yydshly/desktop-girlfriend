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
    now: 0,
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
    mouth: 0.533,
    speaking: {
      active: true,
      source: "state",
      mouth: 0.533,
      baseMouth: 0.65,
      rhythm: "simulated"
    },
    attention: {
      target: "cursor",
      source: "state",
      gaze: "cursor",
      bodyFollow: "soft",
      intensity: 0.55
    }
  });
  assert.deepEqual(state.modelCommands.motion, {
    group: "Talk",
    index: 2,
    action: "speak"
  });
  assert.deepEqual(state.speakingState, {
    active: true,
    source: "state",
    mouth: 0.533,
    baseMouth: 0.65,
    rhythm: "simulated"
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
  assert.deepEqual(state.attentionState, {
    target: "down-left",
    source: "thinking",
    gaze: "down-left",
    bodyFollow: "minimal",
    intensity: 0.34
  });
}

function testPointerStateOverridesRuntimeAttention() {
  const state = buildCharacterRuntimeState({
    mappedState: {
      state: "thinking"
    },
    pointerState: {
      available: true,
      active: true,
      x: 0.4,
      y: -0.2
    },
    profile: {
      mappings: {
        actions: {
          think: { group: "Idle", index: 3 }
        }
      }
    },
    updatedAt: "2026-07-02T00:00:00.000Z"
  });

  assert.deepEqual(state.attentionState, {
    target: "cursor",
    source: "pointer",
    gaze: "cursor",
    bodyFollow: "soft",
    intensity: 0.45
  });
  assert.equal(state.behavior.gaze, "cursor");
}

function testDialogueTtsSpeakingIsRuntimeSpeakingSource() {
  const state = buildCharacterRuntimeState({
    mappedState: {
      state: "speaking"
    },
    emotionState: {
      state: "speaking",
      emotion: "engaged",
      intensity: 0.76,
      activity: "speak",
      gaze: "cursor",
      mouth: 0.65,
      turn: {
        ttsState: "speaking"
      },
      source: "dialogue.turn"
    },
    now: 0,
    profile: {
      mappings: {
        actions: {
          speak: { group: "Talk", index: 2 }
        }
      }
    },
    updatedAt: "2026-07-02T00:00:00.000Z"
  });

  assert.equal(state.speakingState.source, "tts");
  assert.equal(state.attentionState.source, "tts");
  assert.equal(state.modelCommands.parameters.speaking.source, "tts");
  assert.equal(state.modelCommands.parameters.speaking.active, true);
}

testRuntimeStateBuildsBehaviorAndModelCommands();
testExplicitEmotionStateOverridesMappedStatePreset();
testPointerStateOverridesRuntimeAttention();
testDialogueTtsSpeakingIsRuntimeSpeakingSource();
console.log("character-runtime tests passed");
