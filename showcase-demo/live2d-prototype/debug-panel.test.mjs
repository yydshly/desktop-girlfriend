import assert from "node:assert/strict";
import { mountLive2DDebugPanel } from "./debug-panel.js";

function createElement(value = "") {
  const listeners = {};
  return {
    value,
    textContent: "",
    hidden: false,
    src: "",
    dataset: {},
    listeners,
    addEventListener(type, handler) {
      listeners[type] = handler;
    },
    removeAttribute(name) {
      delete this[name];
    }
  };
}

function createDocument(elements, lists = {}) {
  return {
    querySelector(selector) {
      return elements[selector] || null;
    },
    querySelectorAll(selector) {
      return lists[selector] || [];
    }
  };
}

function createRuntime() {
  return {
    setStatusListeners(listeners) {
      this.listeners = listeners;
    },
    setRendererModeCalls: [],
    setRendererMode(mode) {
      this.setRendererModeCalls.push(mode);
    },
    getRendererMode() {
      return "live2d";
    },
    getRendererLabel() {
      return "Live2D";
    },
    getModelUrl() {
      return "./model.model3.json";
    },
    getLastRendererStatus() {
      return { loadState: "idle", hasLive2DModel: false };
    },
    getMotionBindings() {
      return {};
    },
    getModelProfile() {
      return { displayName: "" };
    }
  };
}

function testShowcasePanelWiresRendererSelect() {
  const rendererSelect = createElement("live2d");
  const runtime = createRuntime();
  mountLive2DDebugPanel({
    document: createDocument({
      "#rendererSelect": rendererSelect,
      "#modelUrl": createElement(),
      "#modelStatus": createElement(),
      "#modelPackageStatus": createElement(),
      "#modelTexturePreview": createElement(),
      "#sdkStatus": createElement(),
      "#rendererMode": createElement(),
      "#summaryRenderer": createElement(),
      "#summaryModel": createElement(),
      "#summaryMotion": createElement(),
      "#summaryExpression": createElement(),
      "#summaryCapabilities": createElement(),
      "#summarySdk": createElement(),
      "#setModelUrl": createElement(),
      "#motionBindingState": createElement(),
      "#bindActiveMotion": createElement(),
      "#applyMotionBindings": createElement(),
      "#clearMotionBindings": createElement(),
      "#motionBindingEditor": createElement(),
      "#motionBindingStatus": createElement(),
      "#bridgeUrl": createElement("ws://127.0.0.1:8879"),
      "#connectBridge": createElement(),
      "#disconnectBridge": createElement(),
      "#bridgeStatus": createElement()
    }),
    window: { localStorage: { getItem: () => null, setItem: () => {} } },
    runtime,
    mode: "showcase"
  });

  rendererSelect.value = "placeholder";
  rendererSelect.listeners.change();

  assert.deepEqual(runtime.setRendererModeCalls, ["placeholder"]);
}

function testDesktopPanelDoesNotWireDebugControls() {
  const rendererSelect = createElement("live2d");
  const runtime = createRuntime();
  mountLive2DDebugPanel({
    document: createDocument({ "#rendererSelect": rendererSelect }),
    window: {},
    runtime,
    mode: "desktop"
  });

  assert.equal(rendererSelect.listeners.change, undefined);
  assert.equal(runtime.listeners, undefined);
}

testShowcasePanelWiresRendererSelect();
testDesktopPanelDoesNotWireDebugControls();
console.log("debug-panel tests passed");
