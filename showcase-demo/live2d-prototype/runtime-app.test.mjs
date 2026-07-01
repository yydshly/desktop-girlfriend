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
    getContext() {
      return new Proxy({}, {
        get(target, key) {
          if (!(key in target)) {
            target[key] = () => {};
          }
          return target[key];
        }
      });
    },
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

async function flushAsyncWork() {
  await new Promise((resolve) => setTimeout(resolve, 0));
  await new Promise((resolve) => setTimeout(resolve, 0));
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

async function testStartRefreshesPackageStatusAfterProfileLoads() {
  const { runtime } = createRuntimeHarness();
  const packageStatuses = [];
  globalThis.window = {
    location: {
      href: "http://127.0.0.1:8786/live2d-prototype/"
    }
  };
  globalThis.requestAnimationFrame = () => 0;
  globalThis.cancelAnimationFrame = () => {};
  globalThis.fetch = async (url) => {
    const requestUrl = String(url);
    if (requestUrl.endsWith("profile.json")) {
      return {
        ok: true,
        async json() {
          return {
            displayName: "Candidate",
            mappings: {
              actions: {
                idle: { group: "Idle", index: 0 }
              }
            }
          };
        }
      };
    }
    return {
      ok: true,
      status: 200,
      statusText: "OK",
      async json() {
        return {
          Version: 3,
          FileReferences: {
            Moc: "Model.moc3",
            Textures: ["texture.png"],
            Motions: {
              Idle: [{ File: "idle.motion3.json" }]
            }
          }
        };
      }
    };
  };
  runtime.setStatusListeners({
    onModelPackageStatus: (status) => packageStatuses.push(status)
  });

  runtime.setRendererMode("placeholder");
  runtime.start();
  await flushAsyncWork();

  assert.ok(packageStatuses.length >= 2);
}

testRuntimeRunsModelExperimentTimeline();
await testStartRefreshesPackageStatusAfterProfileLoads();
console.log("runtime-app tests passed");
