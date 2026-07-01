import assert from "node:assert/strict";
import {
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
      desktopPlacement: {}
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
      desktopPlacement: {}
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
        yRatio: "0.57"
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
        yRatio: 0.57
      }
    }
  );
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
    desktopPlacement: {}
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
    }
  });
}

testModelJsonUrlToProfileUrlUsesSameDirectory();
testNormalizeModelProfileSanitizesMotionBindings();
testNormalizeModelProfileUsesContractMappings();
testNormalizeModelProfileSanitizesDesktopPlacement();
await testLoadModelProfileReturnsEmptyProfileWhenMissing();
await testLoadModelProfileParsesProfileJson();
console.log("model-profile tests passed");
