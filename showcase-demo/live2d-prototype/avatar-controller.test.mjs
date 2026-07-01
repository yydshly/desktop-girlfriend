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
    playMotionProbe(group, index) {
      this.motionProbe = { group, index };
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

function testControllerUsesVisualIntentForStageClass() {
  const renderer = createRendererProbe();
  const readout = createTextElement();
  const bubble = createTextElement();
  const stage = createStageElement();
  const controller = new AvatarController(renderer, readout, bubble, stage);

  controller.applyMappedState({
    motion: "reply",
    visualIntent: "speaking"
  });

  assert.equal(stage.className, "avatar-stage is-state-speaking");
}

function testControllerStoresEmotionAndBehaviorForMappedState() {
  const renderer = createRendererProbe();
  const readout = createTextElement();
  const controller = new AvatarController(renderer, readout);

  controller.handleBridgeMessage({
    type: "avatar.state",
    payload: {
      state: "speaking"
    }
  });

  const applied = renderer.appliedStates.at(-1);
  assert.deepEqual(applied.emotionState, {
    state: "speaking",
    emotion: "engaged",
    intensity: 0.76,
    activity: "speak",
    gaze: "cursor",
    mouth: 0.65,
    source: "avatar.state"
  });
  assert.deepEqual(applied.behavior, {
    action: "speak",
    expression: "engaged",
    intensity: 0.76,
    gaze: "cursor",
    mouth: 0.65
  });
}

function testControllerStoresModelCommandsWhenProfileProviderExists() {
  const renderer = createRendererProbe();
  const readout = createTextElement();
  const controller = new AvatarController(renderer, readout, null, null, {
    getModelProfile: () => ({
      mappings: {
        actions: {
          speak: { group: "TapBody", index: 0 },
          idle: { group: "Idle", index: 0 }
        },
        expressions: {
          engaged: "smile"
        }
      }
    })
  });

  controller.handleBridgeMessage({
    type: "avatar.state",
    payload: {
      state: "speaking"
    }
  });

  assert.deepEqual(renderer.appliedStates.at(-1).modelCommands, {
    motion: {
      group: "TapBody",
      index: 0,
      action: "speak"
    },
    expression: {
      name: "smile",
      semantic: "engaged"
    },
    parameters: {
      gaze: "cursor",
      mouth: 0.65,
      intensity: 0.76
    }
  });
}

function testControllerPlaysMotionProbe() {
  const renderer = createRendererProbe();
  const readout = createTextElement();
  const controller = new AvatarController(renderer, readout);

  controller.playMotionProbe("Idle", 3);

  assert.deepEqual(renderer.motionProbe, { group: "Idle", index: 3 });
  assert.equal(controller.currentState.motion, "probe");
  assert.equal(controller.currentState.source, "manual.motion-probe");
}

testControllerRendersSpeechBubbleFromDialogueTurn();
testControllerHidesBubbleForIdleStateWithoutBubble();
testControllerMarksStageWithVisualStateClass();
testControllerUsesVisualIntentForStageClass();
testControllerStoresEmotionAndBehaviorForMappedState();
testControllerStoresModelCommandsWhenProfileProviderExists();
testControllerPlaysMotionProbe();
console.log("avatar-controller tests passed");
