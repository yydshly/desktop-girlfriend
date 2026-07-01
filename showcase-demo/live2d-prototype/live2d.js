import { AvatarController } from "./avatar-controller.js";
import { createBridgeStatus, renderBridgeStatus, updateBridgeStatus } from "./bridge-status.js";
import { detectLive2DSdk, formatSdkStatus } from "./live2d-sdk-loader.js";
import { resolveModelUrlFromRoute } from "./live2d-model-route.js";
import { inspectModelPackage } from "./model-package-inspector.js";
import { createAvatarRenderer, getRendererLabel } from "./renderer-factory.js";

let canvas = document.querySelector("#avatarCanvas");
const stage = document.querySelector("#avatarStage");
const readout = document.querySelector("#stateReadout");
const avatarBubble = document.querySelector("#avatarBubble");
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
const summaryExpression = document.querySelector("#summaryExpression");
const summaryCapabilities = document.querySelector("#summaryCapabilities");
const summarySdk = document.querySelector("#summarySdk");
const setModelUrl = document.querySelector("#setModelUrl");
const bridgeUrl = document.querySelector("#bridgeUrl");
const connectBridge = document.querySelector("#connectBridge");
const disconnectBridge = document.querySelector("#disconnectBridge");
const bridgeStatus = document.querySelector("#bridgeStatus");

const routeParams = new URLSearchParams(window.location.search);
const isDesktopMode = routeParams.get("desktop") === "1";
document.documentElement.dataset.mode = isDesktopMode ? "desktop" : "showcase";

rendererSelect.value = "live2d";

let configuredModelUrl = resolveModelUrlFromRoute(routeParams, modelUrl.value);
modelUrl.value = configuredModelUrl;
let activeRendererMode = rendererSelect.value;
let socket = null;
let bridgeReconnectTimer = null;
let bridgeReconnectEnabled = false;
let bridgeConnectionId = 0;
let currentBridgeStatus = createBridgeStatus(bridgeUrl.value);
let lastRendererStatus = {
  loadState: "idle",
  loadError: "",
  hasLive2DModel: false
};

function createRenderer() {
  return createAvatarRenderer(activeRendererMode, canvas, {
    modelUrl: configuredModelUrl,
    allowTextureFallback: !isDesktopMode,
    onStatusChange: (status) => {
      lastRendererStatus = status;
      updateRendererStatus();
    }
  });
}

function updateBridgeStatusPanel(event) {
  currentBridgeStatus = updateBridgeStatus(currentBridgeStatus, event);
  if (bridgeStatus) {
    bridgeStatus.textContent = renderBridgeStatus(currentBridgeStatus);
  }
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
  readout,
  avatarBubble,
  stage
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
  summaryExpression.textContent = lastRendererStatus.activeExpression || "none";
  summaryCapabilities.textContent = formatCapabilitySummary(lastRendererStatus.modelCapabilities);
  summarySdk.textContent = sdk.ready ? "ready" : `missing ${sdk.missing.length}`;
  if (activeRendererMode === "live2d") {
    modelStatus.textContent = [
      `Live2D renderer: ${configuredModelUrl}.`,
      `renderer state: ${lastRendererStatus.loadState}.`,
      lastRendererStatus.modelCapabilities
        ? `capabilities: ${formatCapabilitySummary(lastRendererStatus.modelCapabilities)}.`
        : "",
      lastRendererStatus.commandDiagnostics
        ? `command: ${formatCommandDiagnostics(lastRendererStatus.commandDiagnostics)}.`
        : "",
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

function formatCapabilitySummary(capabilities = null) {
  if (!capabilities) {
    return "pending";
  }
  const motionGroups = Object.entries(capabilities.motionGroupCounts || {})
    .map(([group, count]) => `${group}:${count}`)
    .join(", ");
  const expressionNames = Array.isArray(capabilities.expressionNames)
    ? capabilities.expressionNames.join(", ")
    : "";
  const motionText = motionGroups || `${capabilities.motionCount || 0} motions`;
  const expressionText = expressionNames || `${capabilities.expressionCount || 0} expressions`;
  return `${motionText} / ${expressionText}`;
}

function formatCommandDiagnostics(diagnostics) {
  const motion = diagnostics.resolvedMotion?.group
    ? `${diagnostics.requestedMotion || "none"} -> ${diagnostics.resolvedMotion.group}[${diagnostics.resolvedMotion.index}]`
    : `${diagnostics.requestedMotion || "none"} -> none`;
  const expression = diagnostics.requestedExpression
    ? `${diagnostics.requestedExpression} ${diagnostics.expressionSupport}`
    : "no expression";
  return `${motion}; expression ${expression}`;
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

document.querySelectorAll("[data-motion-group]").forEach((button) => {
  button.addEventListener("click", () => {
    controller.playMotionProbe(button.dataset.motionGroup, button.dataset.motionIndex);
  });
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
  connectBridgeSocket(bridgeUrl.value);
});

disconnectBridge.addEventListener("click", () => {
  bridgeReconnectEnabled = false;
  window.clearTimeout(bridgeReconnectTimer);
  if (socket) {
    socket.close();
  }
});

function connectBridgeSocket(url, { reconnect = false } = {}) {
  bridgeReconnectEnabled = reconnect;
  updateBridgeStatusPanel({ kind: "connecting", url });
  const connectionId = bridgeConnectionId + 1;
  bridgeConnectionId = connectionId;
  window.clearTimeout(bridgeReconnectTimer);
  if (socket) {
    socket.close();
  }
  socket = new WebSocket(url);
  socket.addEventListener("open", () => {
    updateBridgeStatusPanel({ kind: "open" });
  });
  socket.addEventListener("message", (event) => {
    const message = JSON.parse(event.data);
    updateBridgeStatusPanel({ kind: "message", message });
    controller.handleBridgeMessage(message);
  });
  socket.addEventListener("error", () => {
    updateBridgeStatusPanel({ kind: "error", error: "WebSocket error" });
  });
  socket.addEventListener("close", () => {
    updateBridgeStatusPanel({ kind: "close" });
    if (connectionId !== bridgeConnectionId) {
      return;
    }
    socket = null;
    if (!bridgeReconnectEnabled) {
      return;
    }
    window.clearTimeout(bridgeReconnectTimer);
    bridgeReconnectTimer = window.setTimeout(() => {
      connectBridgeSocket(url, { reconnect: true });
    }, 1200);
  });
}

if (isDesktopMode) {
  connectBridgeSocket(bridgeUrl.value, { reconnect: true });
}

if (isDesktopMode) {
  window.addEventListener("keydown", (event) => {
    const key = event.key.toLowerCase();
    const actionByKey = {
      "1": () => controller.applyStateName("idle"),
      "2": () => controller.applyStateName("happy"),
      "3": () => controller.applyStateName("think"),
      "4": () => controller.applyStateName("sad"),
      "5": () => controller.applyStateName("comfort"),
      "6": () => controller.applyStateName("speak"),
      g: () => controller.playSequence("greet"),
      l: () => controller.playSequence("listen"),
      r: () => controller.playSequence("reply"),
      c: () => controller.playSequence("comfort")
    };
    const action = actionByKey[key];
    if (!action) {
      return;
    }
    event.preventDefault();
    action();
  });
}

window.live2dPrototype = {
  applyState: (state) => controller.applyStateName(state),
  playSequence: (name) => controller.playSequence(name),
  playMotionProbe: (group, index) => controller.playMotionProbe(group, index),
  handleBridgeMessage: (message) => controller.handleBridgeMessage(message),
  isDesktopMode: () => isDesktopMode,
  getModelUrl: () => configuredModelUrl,
  getRendererMode: () => activeRendererMode,
  detectSdk: () => detectLive2DSdk(window),
  inspectModel: () => inspectModelPackage(configuredModelUrl)
};
