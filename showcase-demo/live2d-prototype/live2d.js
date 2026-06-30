import { AvatarController } from "./avatar-controller.js";
import { detectLive2DSdk, formatSdkStatus } from "./live2d-sdk-loader.js";
import { inspectModelPackage } from "./model-package-inspector.js";
import { createAvatarRenderer, getRendererLabel } from "./renderer-factory.js";

let canvas = document.querySelector("#avatarCanvas");
const stage = document.querySelector("#avatarStage");
const readout = document.querySelector("#stateReadout");
const rendererMode = document.querySelector("#rendererMode");
const rendererSelect = document.querySelector("#rendererSelect");
const modelUrl = document.querySelector("#modelUrl");
const modelStatus = document.querySelector("#modelStatus");
const modelPackageStatus = document.querySelector("#modelPackageStatus");
const modelTexturePreview = document.querySelector("#modelTexturePreview");
const sdkStatus = document.querySelector("#sdkStatus");
const summaryRenderer = document.querySelector("#summaryRenderer");
const summaryModel = document.querySelector("#summaryModel");
const summaryMotion = document.querySelector("#summaryMotion");
const summarySdk = document.querySelector("#summarySdk");
const setModelUrl = document.querySelector("#setModelUrl");
const bridgeUrl = document.querySelector("#bridgeUrl");
const connectBridge = document.querySelector("#connectBridge");
const disconnectBridge = document.querySelector("#disconnectBridge");

const routeParams = new URLSearchParams(window.location.search);
const isDesktopMode = routeParams.get("desktop") === "1";
document.documentElement.dataset.mode = isDesktopMode ? "desktop" : "showcase";

rendererSelect.value = "live2d";

let configuredModelUrl = modelUrl.value;
let activeRendererMode = rendererSelect.value;
let socket = null;
let lastRendererStatus = {
  loadState: "idle",
  loadError: "",
  hasLive2DModel: false
};

function createRenderer() {
  return createAvatarRenderer(activeRendererMode, canvas, {
    modelUrl: configuredModelUrl,
    onStatusChange: (status) => {
      lastRendererStatus = status;
      updateRendererStatus();
    }
  });
}

function resetAvatarCanvas() {
  const nextCanvas = canvas.cloneNode(false);
  nextCanvas.width = canvas.width;
  nextCanvas.height = canvas.height;
  canvas.replaceWith(nextCanvas);
  canvas = nextCanvas;
}

const controller = new AvatarController(
  createRenderer(),
  readout
);

function updateRendererStatus() {
  const sdk = detectLive2DSdk(window);
  rendererMode.textContent = getRendererLabel(activeRendererMode);
  sdkStatus.textContent = JSON.stringify(sdk, null, 2);
  summaryRenderer.textContent = getRendererLabel(activeRendererMode);
  summaryModel.textContent = lastRendererStatus.hasLive2DModel ? "live" : lastRendererStatus.loadState;
  summaryMotion.textContent = lastRendererStatus.activeMotion?.group
    ? `${lastRendererStatus.activeMotion.group}[${lastRendererStatus.activeMotion.index}]`
    : "none";
  summarySdk.textContent = sdk.ready ? "ready" : `missing ${sdk.missing.length}`;
  if (activeRendererMode === "live2d") {
    modelStatus.textContent = [
      `Live2D renderer: ${configuredModelUrl}.`,
      `renderer state: ${lastRendererStatus.loadState}.`,
      lastRendererStatus.activeMotion?.group
        ? `active motion: ${lastRendererStatus.activeMotion.group}[${lastRendererStatus.activeMotion.index}].`
        : "",
      formatSdkStatus(sdk),
      lastRendererStatus.loadError ? `detail: ${lastRendererStatus.loadError}` : ""
    ].filter(Boolean).join(" ");
    return;
  }
  modelStatus.textContent = `Placeholder renderer is active. The model path is recorded as ${configuredModelUrl}. ${formatSdkStatus(sdk)}`;
}

async function updateModelPackageStatus() {
  try {
    const packageInfo = await inspectModelPackage(configuredModelUrl);
    modelPackageStatus.textContent = JSON.stringify(packageInfo, null, 2);
    modelTexturePreview.src = packageInfo.firstTextureUrl;
    modelTexturePreview.hidden = !packageInfo.firstTextureUrl;
  } catch (error) {
    modelPackageStatus.textContent = JSON.stringify({
      error: error.message,
      modelUrl: configuredModelUrl
    }, null, 2);
    modelTexturePreview.removeAttribute("src");
    modelTexturePreview.hidden = true;
  }
}

controller.start();
updateRendererStatus();
updateModelPackageStatus();

rendererSelect.addEventListener("change", () => {
  activeRendererMode = rendererSelect.value;
  lastRendererStatus = { loadState: "idle", loadError: "", hasLive2DModel: false };
  resetAvatarCanvas();
  controller.setRenderer(createRenderer());
  updateRendererStatus();
  updateModelPackageStatus();
});

document.querySelectorAll("[data-state]").forEach((button) => {
  button.addEventListener("click", () => controller.applyStateName(button.dataset.state));
});

document.querySelectorAll("[data-sequence]").forEach((button) => {
  button.addEventListener("click", () => controller.playSequence(button.dataset.sequence));
});

stage.addEventListener("pointermove", (event) => {
  controller.setPointerFromEvent(event, stage);
});

setModelUrl.addEventListener("click", () => {
  configuredModelUrl = modelUrl.value.trim();
  lastRendererStatus = { loadState: "idle", loadError: "", hasLive2DModel: false };
  resetAvatarCanvas();
  controller.setRenderer(createRenderer());
  updateRendererStatus();
  updateModelPackageStatus();
});

connectBridge.addEventListener("click", () => {
  if (socket) {
    socket.close();
  }
  socket = new WebSocket(bridgeUrl.value);
  socket.addEventListener("message", (event) => {
    controller.handleBridgeMessage(JSON.parse(event.data));
  });
  socket.addEventListener("close", () => {
    socket = null;
  });
});

disconnectBridge.addEventListener("click", () => {
  if (socket) {
    socket.close();
  }
});

window.live2dPrototype = {
  applyState: (state) => controller.applyStateName(state),
  playSequence: (name) => controller.playSequence(name),
  handleBridgeMessage: (message) => controller.handleBridgeMessage(message),
  isDesktopMode: () => isDesktopMode,
  getModelUrl: () => configuredModelUrl,
  getRendererMode: () => activeRendererMode,
  detectSdk: () => detectLive2DSdk(window),
  inspectModel: () => inspectModelPackage(configuredModelUrl)
};
