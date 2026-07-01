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

function testBaselineCandidateReportsMissingExpressionAndMotionCoverage() {
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

  assert.equal(evaluation.grade, "baseline");
  assert.ok(evaluation.score < 70);
  assert.ok(evaluation.missing.includes("expression mappings: neutral, happy, thinking, sad, soft, engaged"));
  assert.ok(evaluation.missing.includes("action mappings: listen, think, happy, comfort, greet"));
  assert.ok(evaluation.missing.includes("physics"));
}

testStrongCandidateScoresAsProductionCandidate();
testBaselineCandidateReportsMissingExpressionAndMotionCoverage();
console.log("model-candidate-evaluator tests passed");
