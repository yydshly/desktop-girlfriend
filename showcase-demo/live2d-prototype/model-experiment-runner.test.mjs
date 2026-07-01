import assert from "node:assert/strict";
import {
  buildModelExperimentTimeline,
  getDefaultModelExperimentStates
} from "./model-experiment-runner.js";

const profile = {
  mappings: {
    actions: {
      idle: { group: "Idle", index: 0 },
      listen: { group: "Idle", index: 1 },
      think: { group: "Idle", index: 2 },
      speak: { group: "TapBody", index: 0 },
      happy: { group: "TapBody", index: 1 },
      comfort: { group: "Idle", index: 3 }
    },
    expressions: {
      neutral: "default",
      thinking: "think",
      engaged: "smile",
      happy: "smile",
      soft: "soft"
    }
  }
};

function testDefaultExperimentStatesMatchXiaoyunModelSpec() {
  assert.deepEqual(
    getDefaultModelExperimentStates(),
    ["idle", "listening", "thinking", "speaking", "happy", "comfort", "idle"]
  );
}

function testTimelineBuildsEmotionBehaviorAndAdapterCommands() {
  const timeline = buildModelExperimentTimeline(profile);

  assert.equal(timeline.length, 7);
  assert.deepEqual(
    timeline.map((step) => step.state),
    ["idle", "listening", "thinking", "speaking", "happy", "comfort", "idle"]
  );
  assert.deepEqual(timeline[3].behavior, {
    action: "speak",
    expression: "engaged",
    intensity: 0.76,
    gaze: "cursor",
    mouth: 0.514,
    speaking: {
      active: true,
      source: "state",
      mouth: 0.514,
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
  assert.deepEqual(timeline[2].attentionState, {
    target: "down-left",
    source: "thinking",
    gaze: "down-left",
    bodyFollow: "minimal",
    intensity: 0.34
  });
  assert.deepEqual(timeline[3].modelCommands, {
    motion: { group: "TapBody", index: 0, action: "speak" },
    expression: { name: "smile", semantic: "engaged" },
    parameters: {
      gaze: "cursor",
      mouth: 0.514,
      intensity: 0.76,
      speaking: {
        active: true,
        source: "state",
        rhythm: "simulated"
      }
    }
  });
  assert.deepEqual(timeline[3].speakingState, {
    active: true,
    source: "state",
    mouth: 0.514,
    baseMouth: 0.65,
    rhythm: "simulated"
  });
}

function testTimelineUsesStableStepDurations() {
  const timeline = buildModelExperimentTimeline(profile);

  assert.deepEqual(
    timeline.map((step) => step.atMs),
    [0, 3200, 6400, 9600, 12800, 16000, 19200]
  );
  assert.equal(timeline.at(-1).durationMs, 3200);
}

testDefaultExperimentStatesMatchXiaoyunModelSpec();
testTimelineBuildsEmotionBehaviorAndAdapterCommands();
testTimelineUsesStableStepDurations();
console.log("model-experiment-runner tests passed");
