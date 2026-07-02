import { mapAvatarSequence, mapAvatarState, mapBridgeMessage } from "./state-mapper.js";
import { mapBridgeMessageToEmotionState } from "./emotion-state.js";
import { buildCharacterRuntimeState } from "./character-runtime.js";

const DIALOGUE_FALLBACK_TIMEOUT_MS = 5200;

export class AvatarController {
  constructor(renderer, readoutElement, bubbleElement = null, stageElement = null, options = {}) {
    this.renderer = renderer;
    this.readoutElement = readoutElement;
    this.bubbleElement = bubbleElement;
    this.stageElement = stageElement;
    this.voiceVisualizerElement = options.voiceVisualizerElement || null;
    this.getModelProfile = options.getModelProfile || (() => ({}));
    this.getNow = options.getNow || getRuntimeNow;
    this.bubbleTimer = 0;
    this.surfaceFrame = 0;
    this.pointerState = {
      available: false,
      active: false,
      x: 0,
      y: 0
    };
    this.currentState = {
      emotion: "neutral",
      mouth: 0,
      gaze: "cursor",
      motion: "idle",
      intensity: 0.25,
      source: "boot"
    };
  }

  start() {
    this.renderer.start();
    this.renderReadout();
    this.startSurfaceTick();
  }

  setRenderer(renderer) {
    this.renderer.stop();
    this.renderer = renderer;
    this.renderer.start();
    this.renderer.applyState(this.currentState);
    this.renderReadout();
    this.renderVoiceVisualizer();
  }

  applyStateName(state) {
    this.applyMappedState(mapAvatarState({ state }));
  }

  playSequence(name) {
    this.applyMappedState(mapAvatarSequence({ name }));
  }

  playMotionProbe(group, index) {
    this.currentState = {
      ...this.currentState,
      motion: "probe",
      source: "manual.motion-probe",
      updatedAt: new Date().toISOString()
    };
    this.renderer.playMotionProbe?.(group, index);
    this.renderReadout();
  }

  getCurrentState() {
    return this.currentState;
  }

  handleBridgeMessage(message) {
    this.applyMappedState(
      mapBridgeMessage(message),
      mapBridgeMessageToEmotionState(message)
    );
  }

  setPointerFromEvent(event, element) {
    const rect = element.getBoundingClientRect();
    const x = ((event.clientX - rect.left) / rect.width - 0.5) * 2;
    const y = ((event.clientY - rect.top) / rect.height - 0.5) * 2;
    this.pointerState = {
      available: true,
      active: true,
      x,
      y
    };
    this.renderer.setPointer(x, y);
  }

  reactToPointerFromEvent(event, element) {
    const rect = element.getBoundingClientRect();
    const x = ((event.clientX - rect.left) / rect.width - 0.5) * 2;
    const y = ((event.clientY - rect.top) / rect.height - 0.5) * 2;
    this.pointerState = {
      available: true,
      active: true,
      x,
      y
    };
    this.renderer.setPointer(x, y);
    this.renderer.triggerPointerReaction?.(x, y);
  }

  applyMappedState(nextState, emotionState = null) {
    const now = this.getNow();
    this.currentState = buildCharacterRuntimeState({
      previousState: this.currentState,
      mappedState: nextState,
      emotionState: this.prepareEmotionStateForRuntime(emotionState, now),
      pointerState: this.pointerState,
      profile: this.getModelProfile(),
      now
    });
    this.renderer.applyState(this.currentState);
    this.renderReadout();
    this.renderBubble();
    this.renderStageState();
    this.renderVoiceVisualizer();
  }

  tick() {
    if (!this.currentState?.emotionState) {
      return;
    }
    if (!this.shouldRefreshSurface()) {
      return;
    }
    this.currentState = buildCharacterRuntimeState({
      previousState: this.currentState,
      mappedState: this.currentState,
      emotionState: this.currentState.emotionState,
      pointerState: this.pointerState,
      profile: this.getModelProfile(),
      now: this.getNow()
    });
    this.renderer.applyState(this.currentState);
    this.renderReadout();
    this.renderStageState();
    this.renderVoiceVisualizer();
  }

  shouldRefreshSurface() {
    return Boolean(
      this.currentState.speakingState?.active
      || this.currentState.speakingState?.pending
    );
  }

  prepareEmotionStateForRuntime(emotionState = null, now = this.getNow()) {
    if (!emotionState?.turn?.ttsState) {
      return emotionState;
    }
    return {
      ...emotionState,
      turn: {
        ...emotionState.turn,
        receivedAt: Number.isFinite(Number(emotionState.turn.receivedAt))
          ? Number(emotionState.turn.receivedAt)
          : now,
        fallbackTimeoutMs: Number.isFinite(Number(emotionState.turn.fallbackTimeoutMs))
          ? Number(emotionState.turn.fallbackTimeoutMs)
          : DIALOGUE_FALLBACK_TIMEOUT_MS
      }
    };
  }

  renderReadout() {
    this.readoutElement.textContent = JSON.stringify(this.currentState, null, 2);
  }

  renderBubble() {
    if (!this.bubbleElement) {
      return;
    }

    const bubble = this.currentState.bubble;
    if (this.bubbleTimer) {
      globalThis.clearTimeout(this.bubbleTimer);
      this.bubbleTimer = 0;
    }
    if (!bubble?.text) {
      this.bubbleElement.textContent = "";
      this.bubbleElement.hidden = true;
      this.bubbleElement.className = "speech-bubble";
      return;
    }

    this.bubbleElement.textContent = bubble.text;
    this.bubbleElement.hidden = false;
    this.bubbleElement.className = `speech-bubble is-visible tone-${bubble.tone || "neutral"}`;
    if (bubble.ttlMs > 0) {
      this.bubbleTimer = globalThis.setTimeout(() => {
        this.bubbleElement.textContent = "";
        this.bubbleElement.hidden = true;
        this.bubbleElement.className = "speech-bubble";
        this.bubbleTimer = 0;
      }, bubble.ttlMs);
      this.bubbleTimer.unref?.();
    }
  }

  renderStageState() {
    if (!this.stageElement) {
      return;
    }

    const stateClass = `is-state-${this.currentState.visualIntent || this.currentState.motion || this.currentState.emotion || "idle"}`;
    const voiceClass = this.currentState.surface?.visualizer?.visible ? "is-voice-active" : "";
    this.stageElement.className = ["avatar-stage", stateClass, voiceClass].filter(Boolean).join(" ");
  }

  renderVoiceVisualizer() {
    if (!this.voiceVisualizerElement) {
      return;
    }

    const visualizer = this.currentState.surface?.visualizer || {
      visible: false,
      state: "hidden",
      intensity: 0,
      bars: []
    };
    this.voiceVisualizerElement.hidden = !visualizer.visible;
    this.voiceVisualizerElement.className = [
      "voice-visualizer",
      visualizer.active ? "is-visible" : "",
      `state-${visualizer.state || "hidden"}`
    ].filter(Boolean).join(" ");
    this.voiceVisualizerElement.dataset.state = visualizer.state || "hidden";
    this.voiceVisualizerElement.dataset.intensity = String(visualizer.intensity ?? 0);
    const bars = Array.from(this.voiceVisualizerElement.querySelectorAll?.(".voice-bar") || []);
    bars.forEach((bar, index) => {
      const level = visualizer.bars?.[index] ?? 0;
      bar.dataset.level = String(level);
      bar.style.transform = `scaleY(${Math.max(0.12, Number(level) || 0.12)})`;
      bar.style.opacity = String(Math.max(0.2, Math.min(1, Number(level) || 0.2)));
    });
  }

  startSurfaceTick() {
    if (typeof globalThis.requestAnimationFrame !== "function") {
      return;
    }
    if (this.surfaceFrame) {
      return;
    }

    const loop = () => {
      this.tick();
      this.surfaceFrame = globalThis.requestAnimationFrame(loop);
    };
    this.surfaceFrame = globalThis.requestAnimationFrame(loop);
  }
}

function getRuntimeNow() {
  if (typeof globalThis.performance?.now === "function") {
    return globalThis.performance.now();
  }
  return Date.now();
}
