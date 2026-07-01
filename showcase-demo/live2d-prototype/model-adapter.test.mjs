import assert from "node:assert/strict";
import {
  adaptBehaviorToModelCommands,
  adaptEmotionStateToModelCommands
} from "./model-adapter.js";

const profile = {
  mappings: {
    actions: {
      idle: { group: "Idle", index: 0 },
      speak: { group: "TapBody", index: 0 },
      think: { group: "Idle", index: 2 }
    },
    expressions: {
      neutral: "default",
      engaged: "smile",
      thinking: "think"
    }
  }
};

function testBehaviorAdaptsToModelMotionAndExpression() {
  assert.deepEqual(
    adaptBehaviorToModelCommands(
      {
        action: "speak",
        expression: "engaged",
        intensity: 0.76,
        gaze: "cursor",
        mouth: 0.65
      },
      profile
    ),
    {
      motion: {
        group: "TapBody",
        index: 0,
        action: "speak"
      },
      expression: {
        name: "smile",
        semantic: "engaged"
      },
      parameters: {
        gaze: "cursor",
        mouth: 0.65,
        intensity: 0.76,
        speaking: {
          active: false,
          source: "idle",
          rhythm: "none"
        }
      }
    }
  );
}

function testMissingProfileMappingFallsBackToIdleMotion() {
  assert.deepEqual(
    adaptBehaviorToModelCommands(
      {
        action: "comfort",
        expression: "soft",
        intensity: 0.4,
        gaze: "down",
        mouth: 0.1
      },
      profile
    ).motion,
    {
      group: "Idle",
      index: 0,
      action: "idle"
    }
  );
}

function testEmotionStateAdaptsThroughPlanner() {
  const commands = adaptEmotionStateToModelCommands(
    {
      state: "thinking",
      emotion: "thinking",
      intensity: 0.48,
      activity: "think",
      gaze: "down-left",
      mouth: 0.05
    },
    profile
  );

  assert.deepEqual(commands.motion, {
    group: "Idle",
    index: 2,
    action: "think"
  });
  assert.deepEqual(commands.expression, {
    name: "think",
    semantic: "thinking"
  });
  assert.deepEqual(commands.parameters.speaking, {
    active: false,
    source: "idle",
    rhythm: "none"
  });
}

function testSpeakingMetadataPassesToModelParameters() {
  const commands = adaptBehaviorToModelCommands(
    {
      action: "speak",
      expression: "engaged",
      intensity: 0.76,
      gaze: "cursor",
      mouth: 0.533,
      speaking: {
        active: true,
        source: "tts",
        rhythm: "simulated"
      }
    },
    profile
  );

  assert.deepEqual(commands.parameters.speaking, {
    active: true,
    source: "tts",
    rhythm: "simulated"
  });
}

testBehaviorAdaptsToModelMotionAndExpression();
testMissingProfileMappingFallsBackToIdleMotion();
testEmotionStateAdaptsThroughPlanner();
testSpeakingMetadataPassesToModelParameters();
console.log("model-adapter tests passed");
