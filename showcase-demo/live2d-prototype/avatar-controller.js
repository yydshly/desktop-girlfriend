import { mapAvatarSequence, mapAvatarState, mapBridgeMessage } from "./state-mapper.js";
import { mapBridgeMessageToEmotionState } from "./emotion-state.js";
import { buildCharacterRuntimeState } from "./character-runtime.js";

export class AvatarController {
  constructor(renderer, readoutElement, bubbleElement = null, stageElement = null, options = {}) {
    this.renderer = renderer;
    this.readoutElement = readoutElement;
    this.bubbleElement = bubbleElement;
    this.stageElement = stageElement;
    this.getModelProfile = options.getModelProfile || (() => ({}));
    this.getNow = options.getNow || getRuntimeNow;
    this.bubbleTimer = 0;
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
  }

  setRenderer(renderer) {
    this.renderer.stop();
    this.renderer = renderer;
    this.renderer.start();
    this.renderer.applyState(this.currentState);
    this.renderReadout();
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
    this.currentState = buildCharacterRuntimeState({
      previousState: this.currentState,
      mappedState: nextState,
      emotionState,
      pointerState: this.pointerState,
      profile: this.getModelProfile(),
      now: this.getNow()
    });
    this.renderer.applyState(this.currentState);
    this.renderReadout();
    this.renderBubble();
    this.renderStageState();
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
    this.stageElement.className = ["avatar-stage", stateClass].join(" ");
  }
}

function getRuntimeNow() {
  if (typeof globalThis.performance?.now === "function") {
    return globalThis.performance.now();
  }
  return Date.now();
}
