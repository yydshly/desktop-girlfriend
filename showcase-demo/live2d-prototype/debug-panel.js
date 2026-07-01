import { renderBridgeStatus } from "./bridge-status.js";
import { detectLive2DSdk, formatSdkStatus } from "./live2d-sdk-loader.js";
import {
  parseMotionBindingsText,
  serializeMotionBindings
} from "./motion-bindings.js";

export function mountLive2DDebugPanel({
  document,
  window,
  runtime,
  mode = "showcase"
}) {
  if (mode === "desktop") {
    return null;
  }

  const elements = queryDebugElements(document);
  if (!elements.rendererSelect) {
    return null;
  }

  elements.rendererSelect.value = runtime.getRendererMode();
  elements.modelUrl.value = runtime.getModelUrl();
  runtime.setStatusListeners({
    onRendererStatus: () => renderRendererStatus(elements, runtime, window),
    onBridgeStatus: (status) => renderBridgeStatusPanel(elements, status),
    onModelPackageStatus: (packageInfo) => renderModelPackageStatus(elements, packageInfo),
    onMotionBindingStatus: (message = "") => renderMotionBindingStatus(elements, runtime, message)
  });

  elements.rendererSelect.addEventListener("change", () => {
    runtime.setRendererMode(elements.rendererSelect.value);
  });

  elements.setModelUrl.addEventListener("click", () => {
    runtime.setModelUrl(elements.modelUrl.value.trim());
  });

  document.querySelectorAll("[data-state]").forEach((button) => {
    button.addEventListener("click", () => runtime.applyState(button.dataset.state));
  });

  document.querySelectorAll("[data-sequence]").forEach((button) => {
    button.addEventListener("click", () => runtime.playSequence(button.dataset.sequence));
  });

  document.querySelectorAll("[data-motion-group]").forEach((button) => {
    button.addEventListener("click", () => {
      runtime.playMotionProbe(button.dataset.motionGroup, button.dataset.motionIndex);
    });
  });

  elements.bindActiveMotion.addEventListener("click", () => {
    runtime.bindActiveMotion(elements.motionBindingState.value);
  });

  elements.applyMotionBindings.addEventListener("click", () => {
    try {
      runtime.applyMotionBindings(parseMotionBindingsText(elements.motionBindingEditor.value));
      renderMotionBindingStatus(elements, runtime, "Applied JSON bindings.");
    } catch (error) {
      renderMotionBindingStatus(elements, runtime, `Invalid JSON: ${error.message}`);
    }
  });

  elements.clearMotionBindings.addEventListener("click", () => {
    runtime.clearMotionBindings();
    renderMotionBindingStatus(elements, runtime, "Cleared bindings.");
  });

  elements.runModelExperiment.addEventListener("click", () => {
    const timeline = runtime.runModelExperiment();
    renderModelExperimentStatus(elements, timeline);
  });

  elements.connectBridge.addEventListener("click", () => {
    runtime.connectBridge(elements.bridgeUrl.value);
  });

  elements.disconnectBridge.addEventListener("click", () => {
    runtime.disconnectBridge();
  });

  renderRendererStatus(elements, runtime, window);
  renderMotionBindingStatus(elements, runtime);
  return elements;
}

function queryDebugElements(document) {
  return {
    rendererMode: document.querySelector("#rendererMode"),
    rendererSelect: document.querySelector("#rendererSelect"),
    modelUrl: document.querySelector("#modelUrl"),
    modelStatus: document.querySelector("#modelStatus"),
    modelPackageStatus: document.querySelector("#modelPackageStatus"),
    modelTexturePreview: document.querySelector("#modelTexturePreview"),
    sdkStatus: document.querySelector("#sdkStatus"),
    summaryRenderer: document.querySelector("#summaryRenderer"),
    summaryModel: document.querySelector("#summaryModel"),
    summaryMotion: document.querySelector("#summaryMotion"),
    summaryExpression: document.querySelector("#summaryExpression"),
    summaryCapabilities: document.querySelector("#summaryCapabilities"),
    summarySdk: document.querySelector("#summarySdk"),
    setModelUrl: document.querySelector("#setModelUrl"),
    motionBindingState: document.querySelector("#motionBindingState"),
    bindActiveMotion: document.querySelector("#bindActiveMotion"),
    applyMotionBindings: document.querySelector("#applyMotionBindings"),
    clearMotionBindings: document.querySelector("#clearMotionBindings"),
    motionBindingEditor: document.querySelector("#motionBindingEditor"),
    motionBindingStatus: document.querySelector("#motionBindingStatus"),
    runModelExperiment: document.querySelector("#runModelExperiment"),
    modelExperimentStatus: document.querySelector("#modelExperimentStatus"),
    bridgeUrl: document.querySelector("#bridgeUrl"),
    connectBridge: document.querySelector("#connectBridge"),
    disconnectBridge: document.querySelector("#disconnectBridge"),
    bridgeStatus: document.querySelector("#bridgeStatus")
  };
}

function renderRendererStatus(elements, runtime, window) {
  const status = runtime.getLastRendererStatus();
  const sdk = detectLive2DSdk(window);
  elements.rendererMode.textContent = runtime.getRendererLabel();
  elements.sdkStatus.textContent = JSON.stringify(sdk, null, 2);
  elements.summaryRenderer.textContent = runtime.getRendererLabel();
  elements.summaryModel.textContent = status.hasLive2DModel ? "live" : status.loadState;
  elements.summaryMotion.textContent = status.activeMotion?.group
    ? `${status.activeMotion.group}[${status.activeMotion.index}]`
    : "none";
  elements.summaryExpression.textContent = status.activeExpression || "none";
  elements.summaryCapabilities.textContent = formatCapabilitySummary(status.modelCapabilities);
  elements.summarySdk.textContent = sdk.ready ? "ready" : `missing ${sdk.missing.length}`;

  if (runtime.getRendererMode() === "live2d") {
    elements.modelStatus.textContent = [
      `Live2D renderer: ${runtime.getModelUrl()}.`,
      `renderer state: ${status.loadState}.`,
      status.modelCapabilities
        ? `capabilities: ${formatCapabilitySummary(status.modelCapabilities)}.`
        : "",
      status.commandDiagnostics
        ? `command: ${formatCommandDiagnostics(status.commandDiagnostics)}.`
        : "",
      status.modelAdapterCommands
        ? `adapter: ${formatAdapterCommands(status.modelAdapterCommands)}.`
        : "",
      status.activeMotion?.group
        ? `active motion: ${status.activeMotion.group}[${status.activeMotion.index}].`
        : "",
      formatSdkStatus(sdk),
      status.loadError ? `detail: ${status.loadError}` : ""
    ].filter(Boolean).join(" ");
    return;
  }
  elements.modelStatus.textContent = `Placeholder renderer is active. The model path is recorded as ${runtime.getModelUrl()}. ${formatSdkStatus(sdk)}`;
}

function renderBridgeStatusPanel(elements, status) {
  elements.bridgeStatus.textContent = renderBridgeStatus(status);
}

function renderModelPackageStatus(elements, packageInfo) {
  elements.modelPackageStatus.textContent = JSON.stringify(packageInfo, null, 2);
  if (packageInfo.firstTextureUrl) {
    elements.modelTexturePreview.src = packageInfo.firstTextureUrl;
    elements.modelTexturePreview.hidden = false;
    return;
  }
  elements.modelTexturePreview.removeAttribute("src");
  elements.modelTexturePreview.hidden = true;
}

function renderMotionBindingStatus(elements, runtime, message = "") {
  elements.motionBindingEditor.value = serializeMotionBindings(runtime.getMotionBindings());
  const profile = runtime.getModelProfile();
  const profileText = profile.displayName
    ? `Profile: ${profile.displayName}.`
    : "Profile: none.";
  elements.motionBindingStatus.textContent = message || `${profileText} Use Motion Probe, then bind the active motion to a state.`;
}

function renderModelExperimentStatus(elements, timeline = []) {
  elements.modelExperimentStatus.textContent = timeline.map(formatExperimentStep).join("\n");
}

function formatExperimentStep(step) {
  const motion = step.modelCommands?.motion?.group
    ? `${step.modelCommands.motion.group}[${step.modelCommands.motion.index}]`
    : "none";
  const expression = step.modelCommands?.expression?.name || "none";
  const parameters = step.modelCommands?.parameters || {};
  return [
    `${step.index}. ${step.state} -> ${motion}`,
    `expression ${expression}`,
    `mouth ${parameters.mouth ?? 0}`,
    `intensity ${parameters.intensity ?? 0}`,
    `gaze ${parameters.gaze || "cursor"}`
  ].join("; ");
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

function formatAdapterCommands(commands) {
  const motion = commands.motion?.group
    ? `${commands.motion.action || "action"} -> ${commands.motion.group}[${commands.motion.index}]`
    : "motion none";
  const expression = commands.expression?.name
    ? `${commands.expression.semantic || "expression"} -> ${commands.expression.name}`
    : "expression none";
  const parameters = commands.parameters
    ? `mouth ${commands.parameters.mouth}; intensity ${commands.parameters.intensity}; gaze ${commands.parameters.gaze}`
    : "parameters none";
  return `${motion}; ${expression}; ${parameters}`;
}
