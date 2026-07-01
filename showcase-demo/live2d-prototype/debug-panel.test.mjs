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

function createDebugElements() {
  return {
    "#rendererSelect": createElement("live2d"),
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
  };
}

function testShowcasePanelWiresRendererSelect() {
  const rendererSelect = createElement("live2d");
  const elements = createDebugElements();
  elements["#rendererSelect"] = rendererSelect;
  const runtime = createRuntime();
  mountLive2DDebugPanel({
    document: createDocument(elements),
    window: { localStorage: { getItem: () => null, setItem: () => {} } },
    runtime,
    mode: "showcase"
  });

  rendererSelect.value = "placeholder";
  rendererSelect.listeners.change();

  assert.deepEqual(runtime.setRendererModeCalls, ["placeholder"]);
}

function testShowcasePanelRendersAdapterCommands() {
  const elements = createDebugElements();
  const runtime = createRuntime();
  runtime.getLastRendererStatus = () => ({
    loadState: "live2d-ready",
    hasLive2DModel: true,
    activeMotion: { group: "TapBody", index: 0 },
    activeExpression: "smile",
    modelCapabilities: { motionGroupCounts: { TapBody: 1 }, expressionNames: ["smile"] },
    modelAdapterCommands: {
      motion: { group: "TapBody", index: 0, action: "happy" },
      expression: { name: "smile", semantic: "engaged" },
      parameters: { mouth: 0.64, intensity: 0.7, gaze: "cursor" }
    }
  });

  mountLive2DDebugPanel({
    document: createDocument(elements),
    window: { localStorage: { getItem: () => null, setItem: () => {} } },
    runtime,
    mode: "showcase"
  });

  assert.match(elements["#modelStatus"].textContent, /adapter: happy -> TapBody\[0\]/);
  assert.match(elements["#modelStatus"].textContent, /engaged -> smile/);
  assert.match(elements["#modelStatus"].textContent, /mouth 0.64; intensity 0.7; gaze cursor/);
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
testShowcasePanelRendersAdapterCommands();
testDesktopPanelDoesNotWireDebugControls();
console.log("debug-panel tests passed");
