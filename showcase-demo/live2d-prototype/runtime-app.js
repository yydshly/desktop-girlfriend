import { AvatarController } from "./avatar-controller.js";
import { createBridgeClient } from "./bridge-client.js";
import { createBridgeStatus, updateBridgeStatus } from "./bridge-status.js";
import { loadModelProfile, sanitizeDesktopPlacement } from "./model-profile.js";
import { resolveModelUrlFromRoute } from "./live2d-model-route.js";
import { inspectModelPackage } from "./model-package-inspector.js";
import { buildModelExperimentTimeline } from "./model-experiment-runner.js";
import {
  parseMotionBindingsText,
  serializeMotionBindings
} from "./motion-bindings.js";
import { createAvatarRenderer, getRendererLabel } from "./renderer-factory.js";

const MOTION_BINDINGS_STORAGE_KEY_PREFIX = "desktop-girlfriend.live2d.motionBindings.v1:";
const INTERACTION_TUNING_STORAGE_KEY_PREFIX = "desktop-girlfriend.live2d.interactionTuning.v1:";

export function createLive2DRuntime({
  document,
  window,
  routeParams = new URLSearchParams(),
  mode = "showcase"
}) {
  let canvas = document.querySelector("#avatarCanvas");
  const stage = document.querySelector("#avatarStage");
  const readout = document.querySelector("#stateReadout");
  const avatarBubble = document.querySelector("#avatarBubble");
  const isDesktopMode = mode === "desktop";
  const defaultModelUrl = document.querySelector("#modelUrl")?.value
    || "./assets/models/sample/Hiyori/Hiyori.model3.json";

  let configuredModelUrl = resolveModelUrlFromRoute(routeParams, defaultModelUrl);
  let activeRendererMode = "live2d";
  let modelProfile = { displayName: "", motionBindings: {} };
  let profileDesktopPlacement = {};
  let interactionTuningOverride = loadInteractionTuningOverride();
  let motionBindings = loadMotionBindingOverrides();
  let currentBridgeStatus = createBridgeStatus("ws://127.0.0.1:8879");
  let lastRendererStatus = {
    loadState: "idle",
    loadError: "",
    hasLive2DModel: false
  };
  let listeners = {
    onRendererStatus: () => {},
    onBridgeStatus: () => {},
    onModelPackageStatus: () => {},
    onMotionBindingStatus: () => {}
  };

  function createRenderer() {
    return createAvatarRenderer(activeRendererMode, canvas, {
      modelUrl: configuredModelUrl,
      allowTextureFallback: !isDesktopMode,
      motionBindings: getEffectiveMotionBindings(),
      placementProfile: modelProfile.desktopPlacement || {},
      onStatusChange: (status) => {
        lastRendererStatus = status;
        listeners.onRendererStatus(status);
      }
    });
  }

  const controller = new AvatarController(
    createRenderer(),
    readout,
    avatarBubble,
    stage,
    {
      getModelProfile: () => modelProfile
    }
  );

  const bridgeClient = createBridgeClient({
    onEvent: updateBridgeStatusPanel,
    onMessage: (message) => controller.handleBridgeMessage(message)
  });

  function start() {
    controller.start();
    stage.addEventListener("pointermove", (event) => {
      controller.setPointerFromEvent(event, stage);
    });
    stage.addEventListener("pointerdown", (event) => {
      controller.reactToPointerFromEvent(event, stage);
    });
    updateModelPackageStatus();
    listeners.onRendererStatus(lastRendererStatus);
    listeners.onMotionBindingStatus();
    loadProfileForCurrentModel();
    if (isDesktopMode) {
      connectBridge("ws://127.0.0.1:8879", { reconnect: true });
      wireDesktopShortcuts();
    }
  }

  function setStatusListeners(nextListeners = {}) {
    listeners = {
      ...listeners,
      ...nextListeners
    };
  }

  function resetAvatarCanvas() {
    const nextCanvas = canvas.cloneNode(false);
    nextCanvas.width = canvas.width;
    nextCanvas.height = canvas.height;
    canvas.replaceWith(nextCanvas);
    canvas = nextCanvas;
  }

  function restartRenderer() {
    lastRendererStatus = { loadState: "idle", loadError: "", hasLive2DModel: false };
    resetAvatarCanvas();
    controller.setRenderer(createRenderer());
    listeners.onRendererStatus(lastRendererStatus);
    updateModelPackageStatus();
  }

  function setRendererMode(mode) {
    activeRendererMode = mode;
    restartRenderer();
  }

  function setModelUrl(url) {
    configuredModelUrl = url;
    modelProfile = { displayName: "", motionBindings: {} };
    profileDesktopPlacement = {};
    interactionTuningOverride = loadInteractionTuningOverride();
    motionBindings = loadMotionBindingOverrides();
    restartRenderer();
    loadProfileForCurrentModel();
  }

  function applyState(state) {
    controller.applyStateName(state);
  }

  function playSequence(name) {
    controller.playSequence(name);
  }

  function playMotionProbe(group, index) {
    controller.playMotionProbe(group, index);
  }

  function runModelExperiment(options = {}) {
    const timeline = buildModelExperimentTimeline(modelProfile, options);
    timeline.forEach((step) => {
      controller.applyMappedState(
        {
          state: step.state,
          emotion: step.emotionState.emotion,
          intensity: step.emotionState.intensity,
          gaze: step.emotionState.gaze,
          mouth: step.emotionState.mouth,
          motion: step.behavior.action,
          source: "model-experiment",
          experimentStep: step.index
        },
        step.emotionState
      );
    });
    return timeline;
  }

  function bindActiveMotion(state) {
    const motion = lastRendererStatus.activeMotion;
    if (!motion?.group) {
      return;
    }
    motionBindings = {
      ...motionBindings,
      [state]: {
        group: motion.group,
        index: motion.index
      }
    };
    saveMotionBindings(motionBindings);
    controller.renderer.setMotionBindings?.(getEffectiveMotionBindings());
    listeners.onMotionBindingStatus();
  }

  function applyMotionBindings(bindings) {
    motionBindings = bindings;
    saveMotionBindings(motionBindings);
    controller.renderer.setMotionBindings?.(getEffectiveMotionBindings());
    listeners.onMotionBindingStatus();
  }

  function clearMotionBindings() {
    motionBindings = {};
    saveMotionBindings(motionBindings);
    controller.renderer.setMotionBindings?.(getEffectiveMotionBindings());
    listeners.onMotionBindingStatus();
  }

  function connectBridge(url, options = {}) {
    bridgeClient.connect(url, options);
  }

  function disconnectBridge() {
    bridgeClient.disconnect();
  }

  async function updateModelPackageStatus() {
    try {
      const packageInfo = await inspectModelPackage(configuredModelUrl);
      listeners.onModelPackageStatus(packageInfo);
    } catch (error) {
      listeners.onModelPackageStatus({
        error: error.message,
        modelUrl: configuredModelUrl
      });
    }
  }

  function updateBridgeStatusPanel(event) {
    currentBridgeStatus = updateBridgeStatus(currentBridgeStatus, event);
    listeners.onBridgeStatus(currentBridgeStatus);
  }

  function loadMotionBindingOverrides() {
    try {
      return parseMotionBindingsText(window.localStorage.getItem(motionBindingsStorageKey()) || "{}");
    } catch {
      return {};
    }
  }

  function saveMotionBindings(bindings) {
    window.localStorage.setItem(motionBindingsStorageKey(), serializeMotionBindings(bindings));
  }

  function getEffectiveMotionBindings() {
    return {
      ...modelProfile.motionBindings,
      ...motionBindings
    };
  }

  function getInteractionTuning() {
    return { ...(modelProfile.desktopPlacement || {}) };
  }

  function applyInteractionTuning(tuning = {}) {
    interactionTuningOverride = sanitizeDesktopPlacement({
      ...interactionTuningOverride,
      ...tuning
    });
    saveInteractionTuningOverride(interactionTuningOverride);
    modelProfile = {
      ...modelProfile,
      desktopPlacement: {
        ...profileDesktopPlacement,
        ...interactionTuningOverride
      }
    };
    controller.renderer.setPlacementProfile?.(modelProfile.desktopPlacement || {});
    return getInteractionTuning();
  }

  function resetInteractionTuning() {
    interactionTuningOverride = {};
    clearInteractionTuningOverride();
    modelProfile = {
      ...modelProfile,
      desktopPlacement: { ...profileDesktopPlacement }
    };
    controller.renderer.setPlacementProfile?.(modelProfile.desktopPlacement || {});
    return getInteractionTuning();
  }

  async function loadProfileForCurrentModel() {
    modelProfile = await loadModelProfile(configuredModelUrl);
    profileDesktopPlacement = { ...(modelProfile.desktopPlacement || {}) };
    interactionTuningOverride = loadInteractionTuningOverride();
    modelProfile = {
      ...modelProfile,
      desktopPlacement: {
        ...profileDesktopPlacement,
        ...interactionTuningOverride
      }
    };
    controller.renderer.setMotionBindings?.(getEffectiveMotionBindings());
    controller.renderer.setPlacementProfile?.(modelProfile.desktopPlacement || {});
    listeners.onMotionBindingStatus();
    updateModelPackageStatus();
  }

  function motionBindingsStorageKey() {
    return `${MOTION_BINDINGS_STORAGE_KEY_PREFIX}${configuredModelUrl}`;
  }

  function interactionTuningStorageKey() {
    return `${INTERACTION_TUNING_STORAGE_KEY_PREFIX}${configuredModelUrl}`;
  }

  function loadInteractionTuningOverride() {
    try {
      return sanitizeDesktopPlacement(JSON.parse(window.localStorage.getItem(interactionTuningStorageKey()) || "{}"));
    } catch {
      return {};
    }
  }

  function saveInteractionTuningOverride(tuning) {
    window.localStorage.setItem(interactionTuningStorageKey(), JSON.stringify(tuning));
  }

  function clearInteractionTuningOverride() {
    window.localStorage.removeItem?.(interactionTuningStorageKey());
  }

  function wireDesktopShortcuts() {
    window.addEventListener("keydown", (event) => {
      const key = event.key.toLowerCase();
      const actionByKey = {
        "1": () => applyState("idle"),
        "2": () => applyState("happy"),
        "3": () => applyState("thinking"),
        "4": () => applyState("sad"),
        "5": () => applyState("comfort"),
        "6": () => applyState("speaking"),
        g: () => playSequence("greet"),
        l: () => playSequence("listen"),
        r: () => playSequence("reply"),
        c: () => playSequence("comfort")
      };
      const action = actionByKey[key];
      if (!action) {
        return;
      }
      event.preventDefault();
      action();
    });
  }

  return {
    start,
    setStatusListeners,
    setRendererMode,
    setModelUrl,
    applyState,
    playSequence,
    playMotionProbe,
    runModelExperiment,
    bindActiveMotion,
    applyMotionBindings,
    clearMotionBindings,
    getInteractionTuning,
    applyInteractionTuning,
    resetInteractionTuning,
    connectBridge,
    disconnectBridge,
    handleBridgeMessage: (message) => controller.handleBridgeMessage(message),
    getModelUrl: () => configuredModelUrl,
    getRendererMode: () => activeRendererMode,
    getRendererLabel: () => getRendererLabel(activeRendererMode),
    getLastRendererStatus: () => lastRendererStatus,
    getMotionBindings: () => motionBindings,
    getModelProfile: () => modelProfile,
    getBridgeStatus: () => currentBridgeStatus,
    isDesktopMode: () => isDesktopMode,
    inspectModel: () => inspectModelPackage(configuredModelUrl)
  };
}
