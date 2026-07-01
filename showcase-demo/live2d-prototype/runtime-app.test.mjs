import assert from "node:assert/strict";
import { createLive2DRuntime } from "./runtime-app.js";

function createElement(value = "") {
  return {
    value,
    textContent: "",
    hidden: false,
    className: "",
    listeners: {},
    addEventListener(type, handler) {
      this.listeners[type] = handler;
    },
    getBoundingClientRect() {
      return { left: 0, top: 0, width: 900, height: 1200 };
    }
  };
}

function createCanvas() {
  return {
    width: 900,
    height: 1200,
    cloneNode() {
      return createCanvas();
    },
    replaceWith() {}
  };
}

function createDocument(elements) {
  return {
    querySelector(selector) {
      return elements[selector] || null;
    }
  };
}

function createRuntimeHarness() {
  const elements = {
    "#avatarCanvas": createCanvas(),
    "#avatarStage": createElement(),
    "#stateReadout": createElement(),
    "#avatarBubble": createElement(),
    "#modelUrl": createElement("./assets/models/sample/Hiyori/Hiyori.model3.json")
  };
  const runtime = createLive2DRuntime({
    document: createDocument(elements),
    window: {
      localStorage: {
        getItem: () => null,
        setItem: () => {}
      },
      addEventListener() {}
    },
    routeParams: new URLSearchParams(),
    mode: "showcase"
  });
  return { runtime, elements };
}

function testRuntimeRunsModelExperimentTimeline() {
  const { runtime, elements } = createRuntimeHarness();

  const timeline = runtime.runModelExperiment();
  const readout = JSON.parse(elements["#stateReadout"].textContent);

  assert.deepEqual(
    timeline.map((step) => step.state),
    ["idle", "listening", "thinking", "speaking", "happy", "comfort", "idle"]
  );
  assert.equal(readout.source, "model-experiment");
  assert.equal(readout.experimentStep, 6);
  assert.equal(readout.emotionState.state, "idle");
  assert.equal(readout.modelCommands.motion.group, "Idle");
}

testRuntimeRunsModelExperimentTimeline();
console.log("runtime-app tests passed");
