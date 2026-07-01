import assert from "node:assert/strict";
import { AvatarController } from "./avatar-controller.js";

function createTextElement() {
  return {
    textContent: "",
    hidden: false,
    className: ""
  };
}

function createStageElement() {
  return {
    className: "avatar-stage"
  };
}

function createRendererProbe() {
  return {
    appliedStates: [],
    start() {},
    stop() {},
    applyState(state) {
      this.appliedStates.push(state);
    },
    setPointer() {}
  };
}

function testControllerRendersSpeechBubbleFromDialogueTurn() {
  const renderer = createRendererProbe();
  const readout = createTextElement();
  const bubble = createTextElement();
  const controller = new AvatarController(renderer, readout, bubble);

  controller.handleBridgeMessage({
    type: "dialogue.turn",
    payload: {
      turn_id: "turn-1",
      response_text: "我听见啦。",
      tts_state: "speaking"
    }
  });

  assert.equal(bubble.textContent, "我听见啦。");
  assert.equal(bubble.hidden, false);
  assert.equal(bubble.className, "speech-bubble is-visible tone-reply");
}

function testControllerHidesBubbleForIdleStateWithoutBubble() {
  const renderer = createRendererProbe();
  const readout = createTextElement();
  const bubble = createTextElement();
  const controller = new AvatarController(renderer, readout, bubble);

  controller.applyStateName("idle");

  assert.equal(bubble.textContent, "");
  assert.equal(bubble.hidden, true);
  assert.equal(bubble.className, "speech-bubble");
}

function testControllerMarksStageWithVisualStateClass() {
  const renderer = createRendererProbe();
  const readout = createTextElement();
  const bubble = createTextElement();
  const stage = createStageElement();
  const controller = new AvatarController(renderer, readout, bubble, stage);

  controller.applyStateName("happy");

  assert.equal(stage.className, "avatar-stage is-state-happy");
}

testControllerRendersSpeechBubbleFromDialogueTurn();
testControllerHidesBubbleForIdleStateWithoutBubble();
testControllerMarksStageWithVisualStateClass();
console.log("avatar-controller tests passed");
