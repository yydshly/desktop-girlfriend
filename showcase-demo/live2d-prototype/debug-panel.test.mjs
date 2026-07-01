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
      return {
        displayName: "Candidate",
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
    },
    interactionTuning: {
      headTrackingMultiplier: 1,
      eyeTrackingMultiplier: 1,
      bodyTrackingMultiplier: 1,
      pointerFollowXRatio: 0.0075,
      pointerFollowYRatio: 0.005,
      ambientGestureIntervalMs: 7200
    },
    getInteractionTuning() {
      return this.interactionTuning;
    },
    applyInteractionTuning(tuning) {
      this.interactionTuning = {
        ...this.interactionTuning,
        ...tuning
      };
      this.appliedInteractionTuning = tuning;
    },
    resetInteractionTuning() {
      this.interactionTuning = {
        headTrackingMultiplier: 1,
        eyeTrackingMultiplier: 1,
        bodyTrackingMultiplier: 1,
        pointerFollowXRatio: 0.0075,
        pointerFollowYRatio: 0.005,
        ambientGestureIntervalMs: 7200
      };
      this.resetInteractionTuningCalls = (this.resetInteractionTuningCalls || 0) + 1;
    },
    applyState(state) {
      this.appliedState = state;
    },
    runModelExperiment() {
      this.modelExperimentCalls = (this.modelExperimentCalls || 0) + 1;
      return [
        {
          index: 0,
          state: "idle",
          modelCommands: {
            motion: { group: "Idle", index: 0, action: "idle" },
            expression: { name: "default", semantic: "neutral" },
            parameters: { mouth: 0, intensity: 0.25, gaze: "cursor" }
          }
        },
        {
          index: 1,
          state: "speaking",
          modelCommands: {
            motion: { group: "TapBody", index: 0, action: "speak" },
            expression: { name: "smile", semantic: "engaged" },
            parameters: { mouth: 0.65, intensity: 0.76, gaze: "cursor" }
          }
        }
      ];
    }
  };
}

function createDebugElements() {
  return {
    "#rendererSelect": createElement("live2d"),
    "#modelUrl": createElement(),
    "#modelStatus": createElement(),
    "#modelPackageStatus": createElement(),
    "#modelCandidateStatus": createElement(),
    "#modelTexturePreview": createElement(),
    "#sdkStatus": createElement(),
    "#behaviorEventLog": createElement(),
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
    "#runModelExperiment": createElement(),
    "#modelExperimentStatus": createElement(),
    "#headTrackingMultiplier": createElement("1"),
    "#headTrackingValue": createElement(),
    "#eyeTrackingMultiplier": createElement("1"),
    "#eyeTrackingValue": createElement(),
    "#bodyTrackingMultiplier": createElement("1"),
    "#bodyTrackingValue": createElement(),
    "#pointerFollowXRatio": createElement("0.0075"),
    "#pointerFollowXValue": createElement(),
    "#pointerFollowYRatio": createElement("0.005"),
    "#pointerFollowYValue": createElement(),
    "#ambientGestureIntervalMs": createElement("7200"),
    "#ambientGestureValue": createElement(),
    "#resetInteractionTuning": createElement(),
    "#probeInteractionTuning": createElement(),
    "#copyInteractionTuning": createElement(),
    "#interactionTuningSnippet": createElement(),
    "#interactionTuningStatus": createElement(),
    "#bridgeUrl": createElement("ws://127.0.0.1:8879"),
    "#connectBridge": createElement(),
    "#disconnectBridge": createElement(),
    "#bridgeStatus": createElement()
  };
}

function testShowcasePanelAppliesInteractionTuning() {
  const elements = createDebugElements();
  const runtime = createRuntime();

  mountLive2DDebugPanel({
    document: createDocument(elements),
    window: { localStorage: { getItem: () => null, setItem: () => {} } },
    runtime,
    mode: "showcase"
  });

  elements["#headTrackingMultiplier"].value = "1.25";
  elements["#headTrackingMultiplier"].listeners.input();

  assert.equal(runtime.appliedInteractionTuning.headTrackingMultiplier, 1.25);
  assert.equal(runtime.appliedInteractionTuning.eyeTrackingMultiplier, 1);
  assert.equal(elements["#headTrackingValue"].textContent, "1.25");
  assert.equal(elements["#interactionTuningStatus"].textContent, "Tuning applied and saved.");
  assert.match(elements["#interactionTuningSnippet"].textContent, /"headTrackingMultiplier": 1.25/);
}

function testShowcasePanelResetsInteractionTuning() {
  const elements = createDebugElements();
  const runtime = createRuntime();
  runtime.interactionTuning.headTrackingMultiplier = 1.4;

  mountLive2DDebugPanel({
    document: createDocument(elements),
    window: { localStorage: { getItem: () => null, setItem: () => {} } },
    runtime,
    mode: "showcase"
  });

  elements["#resetInteractionTuning"].listeners.click();

  assert.equal(runtime.resetInteractionTuningCalls, 1);
  assert.equal(elements["#headTrackingValue"].textContent, "1.00");
  assert.equal(elements["#interactionTuningStatus"].textContent, "Reset to profile defaults.");
}

function testShowcasePanelProbesInteractionTuning() {
  const elements = createDebugElements();
  const runtime = createRuntime();

  mountLive2DDebugPanel({
    document: createDocument(elements),
    window: { localStorage: { getItem: () => null, setItem: () => {} } },
    runtime,
    mode: "showcase"
  });

  elements["#probeInteractionTuning"].listeners.click();

  assert.equal(runtime.appliedState, "idle");
  assert.equal(elements["#interactionTuningStatus"].textContent, "Idle probe triggered.");
}

async function testShowcasePanelCopiesInteractionTuningSnippet() {
  const elements = createDebugElements();
  const runtime = createRuntime();
  const copied = [];
  const previousNavigator = globalThis.navigator;
  Object.defineProperty(globalThis, "navigator", {
    configurable: true,
    value: {
      clipboard: {
        async writeText(text) {
          copied.push(text);
        }
      }
    }
  });

  mountLive2DDebugPanel({
    document: createDocument(elements),
    window: { localStorage: { getItem: () => null, setItem: () => {} } },
    runtime,
    mode: "showcase"
  });

  await elements["#copyInteractionTuning"].listeners.click();

  assert.match(copied[0], /"desktopPlacement"/);
  assert.match(copied[0], /"ambientGestureIntervalMs": 7200/);
  assert.equal(elements["#interactionTuningStatus"].textContent, "Profile JSON copied.");

  Object.defineProperty(globalThis, "navigator", {
    configurable: true,
    value: previousNavigator
  });
}

async function testShowcasePanelHandlesUnavailableClipboard() {
  const elements = createDebugElements();
  const runtime = createRuntime();
  const previousNavigator = globalThis.navigator;
  Object.defineProperty(globalThis, "navigator", {
    configurable: true,
    value: {}
  });

  mountLive2DDebugPanel({
    document: createDocument(elements),
    window: { localStorage: { getItem: () => null, setItem: () => {} } },
    runtime,
    mode: "showcase"
  });

  await elements["#copyInteractionTuning"].listeners.click();

  assert.equal(elements["#interactionTuningStatus"].textContent, "Copy unavailable; use the JSON snippet.");

  Object.defineProperty(globalThis, "navigator", {
    configurable: true,
    value: previousNavigator
  });
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
    commandDiagnostics: {
      requestedMotion: "idle",
      requestedExpression: "neutral",
      resolvedMotion: { group: "Idle", index: 0 },
      expressionSupport: "missing"
    },
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
  assert.doesNotMatch(elements["#modelStatus"].textContent, /legacy command:/);
  assert.doesNotMatch(elements["#modelStatus"].textContent, /expression neutral missing/);
}

function testShowcasePanelRendersBehaviorEventLog() {
  const elements = createDebugElements();
  const runtime = createRuntime();
  runtime.getLastRendererStatus = () => ({
    loadState: "live2d-ready",
    hasLive2DModel: true,
    behaviorEvents: [
      { at: 1200, type: "pointer.hover-dwell", detail: { x: 0.1, y: -0.2 } },
      { at: 900, type: "motion.play", detail: { group: "Idle", index: 1 } }
    ]
  });

  mountLive2DDebugPanel({
    document: createDocument(elements),
    window: { localStorage: { getItem: () => null, setItem: () => {} } },
    runtime,
    mode: "showcase"
  });

  assert.match(elements["#behaviorEventLog"].textContent, /1200 pointer\.hover-dwell/);
  assert.match(elements["#behaviorEventLog"].textContent, /"x":0\.1/);
  assert.match(elements["#behaviorEventLog"].textContent, /900 motion\.play/);
}

function testShowcasePanelRunsModelExperiment() {
  const elements = createDebugElements();
  const runtime = createRuntime();

  mountLive2DDebugPanel({
    document: createDocument(elements),
    window: { localStorage: { getItem: () => null, setItem: () => {} } },
    runtime,
    mode: "showcase"
  });

  elements["#runModelExperiment"].listeners.click();

  assert.equal(runtime.modelExperimentCalls, 1);
  assert.match(elements["#modelExperimentStatus"].textContent, /0\. idle -> Idle\[0\]/);
  assert.match(elements["#modelExperimentStatus"].textContent, /1\. speaking -> TapBody\[0\]/);
  assert.match(elements["#modelExperimentStatus"].textContent, /mouth 0.65/);
}

function testShowcasePanelRendersModelCandidateEvaluation() {
  const elements = createDebugElements();
  const runtime = createRuntime();

  mountLive2DDebugPanel({
    document: createDocument(elements),
    window: { localStorage: { getItem: () => null, setItem: () => {} } },
    runtime,
    mode: "showcase"
  });

  runtime.listeners.onModelPackageStatus({
    motionCount: 8,
    motionGroupCounts: { Idle: 5, TapBody: 3 },
    expressionCount: 6,
    expressionNames: ["default", "smile", "thinking", "sad", "soft", "engaged"],
    lipSyncIds: ["ParamMouthOpenY"],
    eyeBlinkIds: ["ParamEyeLOpen", "ParamEyeROpen"],
    physics: "model.physics3.json",
    textureCount: 2
  });

  assert.match(elements["#modelCandidateStatus"].textContent, /score 100\/100/);
  assert.match(elements["#modelCandidateStatus"].textContent, /grade strong/);
  assert.match(elements["#modelCandidateStatus"].textContent, /missing none/);
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
testShowcasePanelRendersBehaviorEventLog();
testShowcasePanelRunsModelExperiment();
testShowcasePanelRendersModelCandidateEvaluation();
testShowcasePanelAppliesInteractionTuning();
testShowcasePanelResetsInteractionTuning();
testShowcasePanelProbesInteractionTuning();
await testShowcasePanelCopiesInteractionTuningSnippet();
await testShowcasePanelHandlesUnavailableClipboard();
testDesktopPanelDoesNotWireDebugControls();
console.log("debug-panel tests passed");
