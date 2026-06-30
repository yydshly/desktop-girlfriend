import { mapAvatarSequence, mapAvatarState, mapBridgeMessage } from "./state-mapper.js";

export class AvatarController {
  constructor(renderer, readoutElement) {
    this.renderer = renderer;
    this.readoutElement = readoutElement;
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

  applyStateName(state) {
    this.applyMappedState(mapAvatarState({ state }));
  }

  playSequence(name) {
    this.applyMappedState(mapAvatarSequence({ name }));
  }

  handleBridgeMessage(message) {
    this.applyMappedState(mapBridgeMessage(message));
  }

  setPointerFromEvent(event, element) {
    const rect = element.getBoundingClientRect();
    const x = ((event.clientX - rect.left) / rect.width - 0.5) * 2;
    const y = ((event.clientY - rect.top) / rect.height - 0.5) * 2;
    this.renderer.setPointer(x, y);
  }

  applyMappedState(nextState) {
    this.currentState = {
      ...this.currentState,
      ...nextState,
      updatedAt: new Date().toISOString()
    };
    this.renderer.applyState(this.currentState);
    this.renderReadout();
  }

  renderReadout() {
    this.readoutElement.textContent = JSON.stringify(this.currentState, null, 2);
  }
}
