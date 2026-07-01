import assert from "node:assert/strict";
import {
  createEffectiveModelProfile,
  loadModelProfile,
  modelJsonUrlToProfileUrl,
  normalizeModelProfile
} from "./model-profile.js";

function testModelJsonUrlToProfileUrlUsesSameDirectory() {
  assert.equal(
    modelJsonUrlToProfileUrl("./assets/models/sample/Hiyori/Hiyori.model3.json"),
    "http://127.0.0.1/live2d-prototype/assets/models/sample/Hiyori/profile.json"
  );
}

function testNormalizeModelProfileSanitizesMotionBindings() {
  assert.deepEqual(
    normalizeModelProfile({
      displayName: "Hiyori",
      motionBindings: {
        happy: { group: "Idle", index: "5" },
        sad: { group: "TapBody", index: -1 }
      }
    }),
    {
      schemaVersion: 1,
      displayName: "Hiyori",
      motionBindings: {
        happy: { group: "Idle", index: 5 },
        sad: { group: "TapBody", index: 0 }
      },
      mappings: {
        actions: {
          happy: { group: "Idle", index: 5 },
          sad: { group: "TapBody", index: 0 }
        },
        expressions: {}
      },
      desktopPlacement: {},
      parameters: defaultParameters()
    }
  );
}

function testNormalizeModelProfileUsesContractMappings() {
  assert.deepEqual(
    normalizeModelProfile({
      schemaVersion: 1,
      displayName: "Hiyori",
      mappings: {
        actions: {
          idle: { group: "Idle", index: 0 },
          listening: { group: "Idle", index: 3 },
          wave: { group: "TapBody", index: 0 }
        },
        expressions: {
          neutral: "default",
          reply: "smile",
          wow: "surprised"
        }
      }
    }),
    {
      schemaVersion: 1,
      displayName: "Hiyori",
      motionBindings: {
        idle: { group: "Idle", index: 0 },
        listen: { group: "Idle", index: 3 }
      },
      mappings: {
        actions: {
          idle: { group: "Idle", index: 0 },
          listen: { group: "Idle", index: 3 }
        },
        expressions: {
          neutral: "default",
          engaged: "smile"
        }
      },
      desktopPlacement: {},
      parameters: defaultParameters()
    }
  );
}

function testNormalizeModelProfileSanitizesDesktopPlacement() {
  assert.deepEqual(
    normalizeModelProfile({
      displayName: "Hiyori",
      desktopPlacement: {
        scaleMultiplier: "1.12",
        xOffsetRatio: "-0.08",
        yRatio: "0.57",
        pointerFollowXRatio: "0.01",
        pointerFollowYRatio: "0.006",
        headTrackingMultiplier: "1.15",
        eyeTrackingMultiplier: "1.25",
        bodyTrackingMultiplier: "0.8",
        ambientGestureIntervalMs: "8500",
        pointerFollow: false
      }
    }),
    {
      schemaVersion: 1,
      displayName: "Hiyori",
      motionBindings: {},
      mappings: {
        actions: {},
        expressions: {}
      },
      desktopPlacement: {
        scaleMultiplier: 1.12,
        xOffsetRatio: -0.08,
        yRatio: 0.57,
        pointerFollowXRatio: 0.01,
        pointerFollowYRatio: 0.006,
        headTrackingMultiplier: 1.15,
        eyeTrackingMultiplier: 1.25,
        bodyTrackingMultiplier: 0.8,
        ambientGestureIntervalMs: 8500,
        pointerFollow: false
      },
      parameters: defaultParameters()
    }
  );
}

function testNormalizeModelProfileClampsInteractionTuning() {
  assert.deepEqual(
    normalizeModelProfile({
      desktopPlacement: {
        pointerFollowXRatio: 1,
        pointerFollowYRatio: 1,
        headTrackingMultiplier: 4,
        eyeTrackingMultiplier: 4,
        bodyTrackingMultiplier: 4,
        ambientGestureIntervalMs: 1000
      }
    }).desktopPlacement,
    {
      pointerFollowXRatio: 0.035,
      pointerFollowYRatio: 0.025,
      headTrackingMultiplier: 1.6,
      eyeTrackingMultiplier: 1.8,
      bodyTrackingMultiplier: 1.4,
      ambientGestureIntervalMs: 4000
    }
  );
}

function testNormalizeModelProfileProvidesDefaultParameterAliases() {
  const parameters = normalizeModelProfile({}).parameters;

  assert.equal(parameters.mouthOpen.id, "ParamMouthOpenY");
  assert.equal(parameters.mouthForm.id, "ParamMouthForm");
  assert.equal(parameters.breath.id, "ParamBreath");
  assert.equal(parameters.headX.id, "ParamAngleX");
  assert.equal(parameters.headY.id, "ParamAngleY");
  assert.equal(parameters.headZ.id, "ParamAngleZ");
  assert.equal(parameters.eyeX.id, "ParamEyeBallX");
  assert.equal(parameters.eyeY.id, "ParamEyeBallY");
  assert.equal(parameters.bodyX.id, "ParamBodyAngleX");
  assert.equal(parameters.mouthOpen.source, "default");
}

function testNormalizeModelProfileSanitizesParameterAliases() {
  const parameters = normalizeModelProfile({
    parameters: {
      mouthOpen: {
        id: "ParamCustomMouth",
        min: "-0.5",
        max: "1.5",
        scale: "0.8",
        invert: true
      },
      headX: "ParamCustomHeadX",
      unknown: { id: "ParamIgnored" }
    }
  }).parameters;

  assert.deepEqual(parameters.mouthOpen, {
    id: "ParamCustomMouth",
    min: -0.5,
    max: 1.5,
    scale: 0.8,
    invert: true,
    source: "profile"
  });
  assert.deepEqual(parameters.headX, {
    id: "ParamCustomHeadX",
    min: -30,
    max: 30,
    scale: 1,
    invert: false,
    source: "profile"
  });
  assert.equal(parameters.eyeX.id, "ParamEyeBallX");
  assert.equal(parameters.eyeX.source, "default");
  assert.equal(parameters.unknown, undefined);
}

function testCreateEffectiveModelProfileAppliesActionOverrides() {
  const effectiveProfile = createEffectiveModelProfile(
    {
      displayName: "Hiyori",
      mappings: {
        actions: {
          idle: { group: "Idle", index: 0 },
          speak: { group: "TapBody", index: 0 }
        },
        expressions: {
          engaged: "smile"
        }
      },
      desktopPlacement: {
        yRatio: 0.56
      }
    },
    {
      speak: { group: "Idle", index: 4 }
    }
  );

  assert.deepEqual(effectiveProfile.mappings.actions, {
    idle: { group: "Idle", index: 0 },
    speak: { group: "Idle", index: 4 }
  });
  assert.deepEqual(effectiveProfile.motionBindings, effectiveProfile.mappings.actions);
  assert.deepEqual(effectiveProfile.mappings.expressions, {
    engaged: "smile"
  });
  assert.deepEqual(effectiveProfile.desktopPlacement, {
    yRatio: 0.56
  });
}

async function testLoadModelProfileReturnsEmptyProfileWhenMissing() {
  globalThis.fetch = async () => ({
    ok: false,
    status: 404,
    statusText: "Not Found"
  });

  const profile = await loadModelProfile("./assets/models/sample/Hiyori/Hiyori.model3.json");

  assert.deepEqual(profile, {
    schemaVersion: 1,
    displayName: "",
    motionBindings: {},
    mappings: {
      actions: {},
      expressions: {}
    },
    desktopPlacement: {},
    parameters: defaultParameters()
  });
}

async function testLoadModelProfileParsesProfileJson() {
  globalThis.fetch = async () => ({
    ok: true,
    async json() {
      return {
        schemaVersion: 1,
        displayName: "Hiyori",
        mappings: {
          actions: {
            think: { group: "Idle", index: 1 }
          },
          expressions: {
            thinking: "think"
          }
        },
        desktopPlacement: {
          scaleMultiplier: 1.08,
          yRatio: 0.56
        }
      };
    }
  });

  const profile = await loadModelProfile("./assets/models/sample/Hiyori/Hiyori.model3.json");

  assert.deepEqual(profile, {
    schemaVersion: 1,
    displayName: "Hiyori",
    motionBindings: {
      think: { group: "Idle", index: 1 }
    },
    mappings: {
      actions: {
        think: { group: "Idle", index: 1 }
      },
      expressions: {
        thinking: "think"
      }
    },
    desktopPlacement: {
      scaleMultiplier: 1.08,
      yRatio: 0.56
    },
    parameters: defaultParameters()
  });
}

function defaultParameters() {
  return {
    mouthOpen: { id: "ParamMouthOpenY", min: 0, max: 1, scale: 1, invert: false, source: "default" },
    mouthForm: { id: "ParamMouthForm", min: -1, max: 1, scale: 1, invert: false, source: "default" },
    breath: { id: "ParamBreath", min: 0, max: 1, scale: 1, invert: false, source: "default" },
    headX: { id: "ParamAngleX", min: -30, max: 30, scale: 1, invert: false, source: "default" },
    headY: { id: "ParamAngleY", min: -30, max: 30, scale: 1, invert: false, source: "default" },
    headZ: { id: "ParamAngleZ", min: -30, max: 30, scale: 1, invert: false, source: "default" },
    eyeX: { id: "ParamEyeBallX", min: -1, max: 1, scale: 1, invert: false, source: "default" },
    eyeY: { id: "ParamEyeBallY", min: -1, max: 1, scale: 1, invert: false, source: "default" },
    eyeLOpen: { id: "ParamEyeLOpen", min: 0, max: 1, scale: 1, invert: false, source: "default" },
    eyeROpen: { id: "ParamEyeROpen", min: 0, max: 1, scale: 1, invert: false, source: "default" },
    bodyX: { id: "ParamBodyAngleX", min: -10, max: 10, scale: 1, invert: false, source: "default" },
    bodyY: { id: "ParamBodyAngleY", min: -10, max: 10, scale: 1, invert: false, source: "default" }
  };
}

testModelJsonUrlToProfileUrlUsesSameDirectory();
testNormalizeModelProfileSanitizesMotionBindings();
testNormalizeModelProfileUsesContractMappings();
testNormalizeModelProfileSanitizesDesktopPlacement();
testNormalizeModelProfileClampsInteractionTuning();
testNormalizeModelProfileProvidesDefaultParameterAliases();
testNormalizeModelProfileSanitizesParameterAliases();
testCreateEffectiveModelProfileAppliesActionOverrides();
await testLoadModelProfileReturnsEmptyProfileWhenMissing();
await testLoadModelProfileParsesProfileJson();
console.log("model-profile tests passed");
