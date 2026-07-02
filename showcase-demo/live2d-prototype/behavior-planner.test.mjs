import assert from "node:assert/strict";
import {
  planBehaviorFromEmotionState,
  planBehaviorTimeline
} from "./behavior-planner.js";

function testSpeakingEmotionPlansSpeakBehavior() {
  assert.deepEqual(
    planBehaviorFromEmotionState({
      state: "speaking",
      emotion: "engaged",
      intensity: 0.76,
      activity: "speak",
      gaze: "cursor",
      mouth: 0.65
    }),
    {
      action: "speak",
      expression: "engaged",
      intensity: 0.76,
      gaze: "cursor",
      mouth: 0.65,
      mouthForm: 0
    }
  );
}

function testThinkingEmotionPlansThinkBehavior() {
  assert.deepEqual(
    planBehaviorFromEmotionState({
      state: "thinking",
      emotion: "thinking",
      intensity: 0.48,
      activity: "think",
      gaze: "down-left",
      mouth: 0.05
    }),
    {
      action: "think",
      expression: "thinking",
      intensity: 0.48,
      gaze: "down-left",
      mouth: 0.05,
      mouthForm: 0
    }
  );
}

function testPlannerNormalizesInvalidTerms() {
  assert.deepEqual(
    planBehaviorFromEmotionState({
      state: "happy",
      emotion: "reply",
      intensity: 9,
      activity: "unknown",
      gaze: "",
      mouth: -1
    }),
    {
      action: "idle",
      expression: "engaged",
      intensity: 1,
      gaze: "cursor",
      mouth: 0,
      mouthForm: 0
    }
  );
}

function testPlannerUsesAttentionGazeWhenProvided() {
  assert.deepEqual(
    planBehaviorFromEmotionState(
      {
        state: "thinking",
        emotion: "thinking",
        intensity: 0.48,
        activity: "think",
        gaze: "down-left",
        mouth: 0.05
      },
      {
        target: "cursor",
        source: "pointer",
        gaze: "cursor",
        bodyFollow: "soft",
        intensity: 0.45
      }
    ),
    {
      action: "think",
      expression: "thinking",
      intensity: 0.48,
      gaze: "cursor",
      mouth: 0.05,
      mouthForm: 0,
      attention: {
        target: "cursor",
        source: "pointer",
        gaze: "cursor",
        bodyFollow: "soft",
        intensity: 0.45
      }
    }
  );
}

function testPlannerUsesSpeakingMouthWhenProvided() {
  assert.deepEqual(
    planBehaviorFromEmotionState(
      {
        state: "speaking",
        emotion: "engaged",
        intensity: 0.76,
        activity: "speak",
        gaze: "cursor",
        mouth: 0.65
      },
      null,
      {
        active: true,
        source: "tts",
        mouth: 0.533,
        baseMouth: 0.65,
        rhythm: "simulated",
        mouthForm: 0.22
      }
    ),
    {
      action: "speak",
      expression: "engaged",
      intensity: 0.76,
      gaze: "cursor",
      mouth: 0.533,
      mouthForm: 0.22,
      speaking: {
        active: true,
        source: "tts",
        mouth: 0.533,
        baseMouth: 0.65,
        rhythm: "simulated",
        mouthForm: 0.22
      }
    }
  );
}

function testBehaviorTimelineUsesStableDelays() {
  const timeline = planBehaviorTimeline({
    state: "comfort",
    emotion: "soft",
    intensity: 0.68,
    activity: "comfort",
    gaze: "cursor",
    mouth: 0.18
  });

  assert.deepEqual(timeline, [
    {
      atMs: 0,
      behavior: {
        action: "comfort",
        expression: "soft",
        intensity: 0.68,
        gaze: "cursor",
        mouth: 0.18,
        mouthForm: 0
      }
    },
    {
      atMs: 4200,
      behavior: {
        action: "idle",
        expression: "neutral",
        intensity: 0.25,
        gaze: "cursor",
        mouth: 0
      }
    }
  ]);
}

testSpeakingEmotionPlansSpeakBehavior();
testThinkingEmotionPlansThinkBehavior();
testPlannerNormalizesInvalidTerms();
testPlannerUsesAttentionGazeWhenProvided();
testPlannerUsesSpeakingMouthWhenProvided();
testBehaviorTimelineUsesStableDelays();
console.log("behavior-planner tests passed");
