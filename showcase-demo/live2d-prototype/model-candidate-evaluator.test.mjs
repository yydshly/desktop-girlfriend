import assert from "node:assert/strict";
import { evaluateModelCandidate } from "./model-candidate-evaluator.js";

const strongPackage = {
  motionCount: 8,
  motionGroupCounts: { Idle: 5, TapBody: 3 },
  expressionCount: 6,
  expressionNames: ["default", "smile", "thinking", "sad", "soft", "engaged"],
  lipSyncIds: ["ParamMouthOpenY"],
  eyeBlinkIds: ["ParamEyeLOpen", "ParamEyeROpen"],
  physics: "model.physics3.json",
  textureCount: 2
};

const strongProfile = {
  mappings: {
    actions: {
      idle: { group: "Idle", index: 0 },
      listen: { group: "Idle", index: 1 },
      think: { group: "Idle", index: 2 },
      speak: { group: "TapBody", index: 0 },
      happy: { group: "TapBody", index: 1 },
      comfort: { group: "Idle", index: 3 },
      greet: { group: "TapBody", index: 2 }
    },
    expressions: {
      neutral: "default",
      happy: "smile",
      thinking: "thinking",
      sad: "sad",
      soft: "soft",
      engaged: "engaged"
    }
  }
};

function testStrongCandidateScoresAsProductionCandidate() {
  const evaluation = evaluateModelCandidate(strongPackage, strongProfile);

  assert.equal(evaluation.score, 100);
  assert.equal(evaluation.grade, "strong");
  assert.deepEqual(evaluation.missing, []);
}

function testProfileAwareCandidateDoesNotRequireSampleMotionNames() {
  const evaluation = evaluateModelCandidate(
    {
      motionCount: 8,
      motionGroupCounts: { Standby: 5, Talk: 3 },
      expressionCount: 6,
      expressionNames: ["default", "smile", "thinking", "sad", "soft", "engaged"],
      lipSyncIds: ["ParamMouthOpenY"],
      eyeBlinkIds: ["ParamEyeLOpen", "ParamEyeROpen"],
      physics: "model.physics3.json",
      textureCount: 2
    },
    {
      mappings: {
        actions: {
          idle: { group: "Standby", index: 0 },
          listen: { group: "Standby", index: 1 },
          think: { group: "Standby", index: 2 },
          comfort: { group: "Standby", index: 3 },
          speak: { group: "Talk", index: 0 },
          happy: { group: "Talk", index: 1 },
          greet: { group: "Talk", index: 2 }
        },
        expressions: {
          neutral: "default",
          happy: "smile",
          thinking: "thinking",
          sad: "sad",
          soft: "soft",
          engaged: "engaged"
        }
      }
    }
  );

  assert.equal(evaluation.score, 100);
  assert.equal(evaluation.grade, "strong");
  assert.deepEqual(evaluation.missing, []);
}

function testWeakCandidateReportsMissingExpressionAndMotionCoverage() {
  const evaluation = evaluateModelCandidate(
    {
      motionCount: 10,
      motionGroupCounts: { Idle: 9, TapBody: 1 },
      expressionCount: 0,
      expressionNames: [],
      lipSyncIds: ["ParamMouthOpenY"],
      eyeBlinkIds: ["ParamEyeLOpen", "ParamEyeROpen"],
      physics: "",
      textureCount: 2
    },
    {
      mappings: {
        actions: {
          idle: { group: "Idle", index: 0 },
          speak: { group: "TapBody", index: 0 }
        },
        expressions: {}
      }
    }
  );

  assert.equal(evaluation.grade, "weak");
  assert.ok(evaluation.score < 70);
  assert.ok(evaluation.missing.includes("expression mappings: neutral, happy, thinking, sad, soft, engaged"));
  assert.ok(evaluation.missing.includes("action mappings: listen, think, happy, comfort, greet"));
  assert.ok(evaluation.missing.includes("physics"));
}

testStrongCandidateScoresAsProductionCandidate();
testProfileAwareCandidateDoesNotRequireSampleMotionNames();
testWeakCandidateReportsMissingExpressionAndMotionCoverage();
console.log("model-candidate-evaluator tests passed");
