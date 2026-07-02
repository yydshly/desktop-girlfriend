import assert from "node:assert/strict";
import {
  buildModelExperimentTimeline,
  getDefaultModelExperimentStates,
  getRuntimeValidationSequenceStates
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
    ["idle", "listen", "think", "speak", "happy", "comfort", "idle"]
  );
}

function testRuntimeValidationSequenceUsesCompactSemanticInputs() {
  assert.deepEqual(
    getRuntimeValidationSequenceStates(),
    ["idle", "listen", "think", "speak", "happy", "comfort", "idle"]
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
    mouthForm: -0.187,
    speaking: {
      active: true,
      source: "state",
      mouth: 0.514,
      baseMouth: 0.65,
      rhythm: "simulated",
      ttsState: "none",
      ttsSource: "unknown",
      mouthForm: -0.187
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
      mouthForm: -0.187,
      intensity: 0.76,
      speaking: {
        active: true,
        source: "state",
        rhythm: "simulated",
        ttsState: "none",
        ttsSource: "unknown",
        mouth: 0.514,
        baseMouth: 0.65,
        mouthForm: -0.187
      }
    }
  });
  assert.deepEqual(timeline[3].speakingState, {
    active: true,
    source: "state",
    mouth: 0.514,
    baseMouth: 0.65,
    rhythm: "simulated",
    ttsState: "none",
    ttsSource: "unknown",
    mouthForm: -0.187
  });
  assert.equal(timeline[3].semanticState, "speak");
  assert.equal(timeline[3].validation.blockers.length, 0);
  assert.equal(timeline[3].validation.warnings.length, 0);
  assert.equal(timeline[3].resolvedParameters.mouthOpen.id, "ParamMouthOpenY");
  assert.equal(timeline[3].resolvedParameters.mouthOpen.source, "default");
}

function testTimelineUsesStableStepDurations() {
  const timeline = buildModelExperimentTimeline(profile);

  assert.deepEqual(
    timeline.map((step) => step.atMs),
    [0, 3200, 6400, 9600, 12800, 16000, 19200]
  );
  assert.equal(timeline.at(-1).durationMs, 3200);
}

function testTimelineReportsProfileAndModelCapabilityProblems() {
  const weakProfile = {
    mappings: {
      actions: {
        idle: { group: "Idle", index: 0 },
        speak: { group: "TapBody", index: 4 }
      },
      expressions: {}
    }
  };
  const timeline = buildModelExperimentTimeline(weakProfile, {
    modelCapabilities: {
      motionGroupCounts: {
        Idle: 1,
        TapBody: 1
      },
      expressionNames: []
    }
  });
  const speakingStep = timeline.find((step) => step.semanticState === "speak");
  const happyStep = timeline.find((step) => step.semanticState === "happy");

  assert.match(speakingStep.validation.blockers.join("; "), /motion TapBody\[4\] unavailable/);
  assert.match(speakingStep.validation.warnings.join("; "), /expression engaged is unmapped/);
  assert.match(happyStep.validation.warnings.join("; "), /action happy is unmapped/);
  assert.equal(speakingStep.validation.layer, "profile/model");
}

function testTimelineReportsProfileParameterAliases() {
  const timeline = buildModelExperimentTimeline({
    ...profile,
    parameters: {
      mouthOpen: { id: "ParamCustomMouth", min: 0, max: 2, scale: 2, invert: false, source: "profile" }
    }
  });

  assert.equal(timeline[3].resolvedParameters.mouthOpen.id, "ParamCustomMouth");
  assert.equal(timeline[3].resolvedParameters.mouthOpen.source, "profile");
}

testDefaultExperimentStatesMatchXiaoyunModelSpec();
testRuntimeValidationSequenceUsesCompactSemanticInputs();
testTimelineBuildsEmotionBehaviorAndAdapterCommands();
testTimelineUsesStableStepDurations();
testTimelineReportsProfileAndModelCapabilityProblems();
testTimelineReportsProfileParameterAliases();
console.log("model-experiment-runner tests passed");
