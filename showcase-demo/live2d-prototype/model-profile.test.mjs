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
      displayName: "Hiyori",
      motionBindings: {
        happy: { group: "Idle", index: 5 },
        sad: { group: "TapBody", index: 0 }
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
      displayName: "Hiyori",
      motionBindings: {},
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
    displayName: "",
    motionBindings: {},
    desktopPlacement: {}
  });
}

async function testLoadModelProfileParsesProfileJson() {
  globalThis.fetch = async () => ({
    ok: true,
    async json() {
      return {
        displayName: "Hiyori",
        motionBindings: {
          think: { group: "Idle", index: 1 }
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
    displayName: "Hiyori",
    motionBindings: {
      think: { group: "Idle", index: 1 }
    },
    desktopPlacement: {
      scaleMultiplier: 1.08,
      yRatio: 0.56
    }
  });
}

testModelJsonUrlToProfileUrlUsesSameDirectory();
testNormalizeModelProfileSanitizesMotionBindings();
testNormalizeModelProfileSanitizesDesktopPlacement();
await testLoadModelProfileReturnsEmptyProfileWhenMissing();
await testLoadModelProfileParsesProfileJson();
console.log("model-profile tests passed");
