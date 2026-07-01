import assert from "node:assert/strict";
import { validateCustomModelIntake } from "./custom-model-intake.js";

const strongPackage = {
  version: 3,
  moc: "Xiaoyun.moc3",
  textureCount: 2,
  motionCount: 12,
  motionGroupCounts: { Idle: 6, TapBody: 4, Wave: 2 },
  expressionCount: 6,
  expressionNames: ["neutral", "smile", "thinking", "sad", "soft", "engaged"],
  lipSyncIds: ["ParamMouthOpenY"],
  eyeBlinkIds: ["ParamEyeLOpen", "ParamEyeROpen"],
  physics: "Xiaoyun.physics3.json"
};

const strongProfile = {
  schemaVersion: 1,
  displayName: "Xiaoyun",
  desktopPlacement: {
    scaleMultiplier: 1,
    xOffsetRatio: 0,
    yRatio: 0.54,
    pointerFollowXRatio: 0.006,
    pointerFollowYRatio: 0.004,
    headTrackingMultiplier: 1.1,
    eyeTrackingMultiplier: 1.2,
    bodyTrackingMultiplier: 0.45,
    ambientGestureIntervalMs: 9000
  },
  mappings: {
    actions: {
      idle: { group: "Idle", index: 0 },
      greet: { group: "Wave", index: 0 },
      listen: { group: "Idle", index: 1 },
      think: { group: "Idle", index: 2 },
      reply: { group: "TapBody", index: 0 },
      comfort: { group: "Idle", index: 3 },
      sad: { group: "Idle", index: 4 },
      happy: { group: "TapBody", index: 1 },
      speak: { group: "TapBody", index: 2 }
    },
    expressions: {
      neutral: "neutral",
      happy: "smile",
      thinking: "thinking",
      sad: "sad",
      soft: "soft",
      engaged: "engaged"
    }
  }
};

function testReadyCustomModelPassesIntake() {
  const result = validateCustomModelIntake(strongPackage, strongProfile);

  assert.equal(result.ready, true);
  assert.equal(result.grade, "ready");
  assert.deepEqual(result.blockers, []);
  assert.deepEqual(result.warnings, []);
  assert.equal(result.summary.displayName, "Xiaoyun");
  assert.equal(result.summary.mappedActions.length, 9);
}

function testMissingMotionMappingBlocksIntake() {
  const profile = structuredClone(strongProfile);
  profile.mappings.actions.greet = { group: "Wave", index: 9 };

  const result = validateCustomModelIntake(strongPackage, profile);

  assert.equal(result.ready, false);
  assert.equal(result.grade, "blocked");
  assert.ok(result.blockers.includes("mappings.actions.greet points to missing motion Wave[9]"));
}

function testMissingOptionalRuntimeFeaturesWarn() {
  const packageInfo = {
    ...strongPackage,
    lipSyncIds: [],
    eyeBlinkIds: [],
    physics: ""
  };
  const result = validateCustomModelIntake(packageInfo, strongProfile);

  assert.equal(result.ready, true);
  assert.equal(result.grade, "usable-with-warnings");
  assert.ok(result.warnings.includes("lip sync parameter is recommended for speaking"));
  assert.ok(result.warnings.includes("eye blink parameters are recommended"));
  assert.ok(result.warnings.includes("physics is recommended for hair and clothing softness"));
}

function testMissingDesktopPlacementWarns() {
  const profile = structuredClone(strongProfile);
  profile.desktopPlacement = {};

  const result = validateCustomModelIntake(strongPackage, profile);

  assert.equal(result.ready, true);
  assert.equal(result.grade, "usable-with-warnings");
  assert.ok(result.warnings.includes("desktopPlacement.scaleMultiplier should be tuned for desktop mode"));
  assert.ok(result.warnings.includes("desktopPlacement.ambientGestureIntervalMs should be tuned for desktop mode"));
}

testReadyCustomModelPassesIntake();
testMissingMotionMappingBlocksIntake();
testMissingOptionalRuntimeFeaturesWarn();
testMissingDesktopPlacementWarns();
console.log("custom-model-intake tests passed");
