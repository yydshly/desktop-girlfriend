import { AvatarController } from "./avatar-controller.js";
import { PlaceholderRenderer } from "./adapters/placeholder-renderer.js";

const canvas = document.querySelector("#avatarCanvas");
const stage = document.querySelector("#avatarStage");
const readout = document.querySelector("#stateReadout");
const bridgeUrl = document.querySelector("#bridgeUrl");
const connectBridge = document.querySelector("#connectBridge");
const disconnectBridge = document.querySelector("#disconnectBridge");

const renderer = new PlaceholderRenderer(canvas);
const controller = new AvatarController(renderer, readout);
let socket = null;

controller.start();

document.querySelectorAll("[data-state]").forEach((button) => {
  button.addEventListener("click", () => controller.applyStateName(button.dataset.state));
});

document.querySelectorAll("[data-sequence]").forEach((button) => {
  button.addEventListener("click", () => controller.playSequence(button.dataset.sequence));
});

stage.addEventListener("pointermove", (event) => {
  controller.setPointerFromEvent(event, stage);
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
  handleBridgeMessage: (message) => controller.handleBridgeMessage(message)
};
