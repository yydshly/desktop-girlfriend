import assert from "node:assert/strict";
import { detectLive2DSdk, ensureLive2DSdk } from "./live2d-sdk-loader.js";

const LOCAL_PIXI_SRC = "./assets/vendor/live2d/pixi.min.js";
const LOCAL_LIVE2D_PLUGIN_SRC = "./assets/vendor/live2d/pixi-live2d-display-cubism4.min.js";

class FakeScript {
  constructor(src) {
    this.src = src;
    this.dataset = { live2dSdk: src };
    this.listeners = new Map();
  }

  addEventListener(type, listener) {
    this.listeners.set(type, listener);
  }

  dispatch(type) {
    this.listeners.get(type)?.();
  }
}

function createDocumentWithPendingLive2DPlugin(root) {
  const pendingPluginScript = new FakeScript(LOCAL_LIVE2D_PLUGIN_SRC);

  return {
    head: {
      appendChild(script) {
        queueMicrotask(() => {
          if (script.src.includes("cubismcore")) {
            root.Live2DCubismCore = {};
          }
          if (script.src.includes("pixi-live2d-display")) {
            root.PIXI ||= {};
            root.PIXI.live2d = { Live2DModel: { from: () => Promise.resolve({}) } };
          }
          script.dispatch("load");
        });
      }
    },
    createElement() {
      return new FakeScript("");
    },
    querySelector(selector) {
      if (selector.includes(LOCAL_LIVE2D_PLUGIN_SRC)) {
        setTimeout(() => {
          root.PIXI.live2d = { Live2DModel: { from: () => Promise.resolve({}) } };
          pendingPluginScript.dispatch("load");
        }, 0);
        return pendingPluginScript;
      }
      return null;
    }
  };
}

async function testWaitsForExistingSdkScript() {
  const root = { PIXI: {}, Live2DCubismCore: {} };
  root.document = createDocumentWithPendingLive2DPlugin(root);

  const status = await ensureLive2DSdk(root);

  assert.equal(status.ready, true);
  assert.deepEqual(status.missing, []);
}

async function testWaitsForSdkGlobalsAfterScriptLoad() {
  const root = { PIXI: {}, Live2DCubismCore: {} };
  const scripts = [];
  root.document = {
    head: {
      appendChild(script) {
        scripts.push(script);
        queueMicrotask(() => script.dispatch("load"));
      }
    },
    createElement() {
      return new FakeScript("");
    },
    querySelector() {
      return null;
    }
  };

  setTimeout(() => {
    root.PIXI.live2d = { Live2DModel: { from: () => Promise.resolve({}) } };
  }, 0);

  const status = await ensureLive2DSdk(root);

  assert.equal(status.ready, true);
  assert.equal(scripts.length, 3);
  assert.equal(scripts[0].src, LOCAL_PIXI_SRC);
}

async function testFallsBackToCdnWhenLocalScriptFails() {
  const root = { PIXI: {}, Live2DCubismCore: {} };
  const scripts = [];
  root.document = {
    head: {
      appendChild(script) {
        scripts.push(script);
        queueMicrotask(() => {
          if (script.src.startsWith("./assets/vendor")) {
            script.dispatch("error");
            return;
          }
          if (script.src.includes("cubismcore")) {
            root.Live2DCubismCore = {};
          }
          if (script.src.includes("pixi-live2d-display")) {
            root.PIXI.live2d = { Live2DModel: { from: () => Promise.resolve({}) } };
          }
          script.dispatch("load");
        });
      }
    },
    createElement() {
      return new FakeScript("");
    },
    querySelector() {
      return null;
    }
  };

  const status = await ensureLive2DSdk(root);

  assert.equal(status.ready, true);
  assert.ok(scripts.some((script) => script.src.startsWith("https://")));
}

function testRequiresLive2DModelFactory() {
  const root = { PIXI: { live2d: {} }, Live2DCubismCore: {} };

  const status = detectLive2DSdk(root);

  assert.equal(status.ready, false);
  assert.deepEqual(status.missing, ["PIXI.live2d.Live2DModel.from"]);
}

testRequiresLive2DModelFactory();
await testWaitsForExistingSdkScript();
await testWaitsForSdkGlobalsAfterScriptLoad();
await testFallsBackToCdnWhenLocalScriptFails();
console.log("live2d-sdk-loader tests passed");
