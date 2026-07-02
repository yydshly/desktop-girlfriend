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
    className: "avatar-stage",
    getBoundingClientRect() {
      return {
        left: 10,
        top: 20,
        width: 200,
        height: 100
      };
    }
  };
}

function createVisualizerElement() {
  const bars = Array.from({ length: 5 }, () => ({
    style: {},
    dataset: {}
  }));
  return {
    hidden: false,
    className: "",
    dataset: {},
    style: {},
    querySelectorAll(selector) {
      return selector === ".voice-bar" ? bars : [];
    },
    bars
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
    setPointer(x, y) {
      this.pointer = { x, y };
    },
    triggerPointerReaction(x, y) {
      this.pointerReaction = { x, y };
    }
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
  const controller = new AvatarController(renderer, readout, null, null, {
    getNow: () => 0
  });

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
    gaze: "user",
    mouth: 0.533,
    mouthForm: 0.096,
    speaking: {
      active: true,
      pending: false,
      closing: false,
      fallbackExpired: false,
      source: "state",
      mouth: 0.533,
      baseMouth: 0.65,
      rhythm: "simulated",
      ttsState: "none",
      ttsSource: "unknown",
      mouthForm: 0.096
    },
    attention: {
      target: "user",
      source: "state",
      gaze: "user",
      bodyFollow: "soft",
      intensity: 0.55
    }
  });
}

function testControllerPassesRuntimeNowToSpeakingDriver() {
  const renderer = createRendererProbe();
  const readout = createTextElement();
  const controller = new AvatarController(renderer, readout, null, null, {
    getNow: () => 900
  });

  controller.applyStateName("speaking");

  assert.equal(renderer.appliedStates.at(-1).speakingState.mouth, 0.525);
}

function testControllerStoresModelCommandsWhenProfileProviderExists() {
  const renderer = createRendererProbe();
  const readout = createTextElement();
  const controller = new AvatarController(renderer, readout, null, null, {
    getNow: () => 0,
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
      gaze: "user",
      mouth: 0.533,
      mouthForm: 0.096,
      intensity: 0.76,
      speaking: {
        active: true,
        pending: false,
        closing: false,
        fallbackExpired: false,
        source: "state",
        rhythm: "simulated",
        ttsState: "none",
        ttsSource: "unknown",
        mouth: 0.533,
        baseMouth: 0.65,
        mouthForm: 0.096
      }
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

function testControllerTriggersPointerReactionFromEvent() {
  const renderer = createRendererProbe();
  const readout = createTextElement();
  const stage = createStageElement();
  const controller = new AvatarController(renderer, readout, null, stage);

  controller.reactToPointerFromEvent(
    { clientX: 160, clientY: 45 },
    stage
  );

  assert.deepEqual(renderer.pointer, { x: 0.5, y: -0.5 });
  assert.deepEqual(renderer.pointerReaction, { x: 0.5, y: -0.5 });
}

function testControllerPassesPointerStateToRuntimeAttention() {
  const renderer = createRendererProbe();
  const readout = createTextElement();
  const stage = createStageElement();
  const controller = new AvatarController(renderer, readout, null, stage);

  controller.setPointerFromEvent(
    { clientX: 160, clientY: 45 },
    stage
  );
  controller.applyStateName("thinking");

  const applied = renderer.appliedStates.at(-1);
  assert.deepEqual(applied.attentionState, {
    target: "cursor",
    source: "pointer",
    gaze: "cursor",
    bodyFollow: "soft",
    intensity: 0.45
  });
  assert.equal(applied.behavior.gaze, "cursor");
}

function testControllerRendersVoiceVisualizerForTtsPlaying() {
  const renderer = createRendererProbe();
  const readout = createTextElement();
  const bubble = createTextElement();
  const stage = createStageElement();
  const visualizer = createVisualizerElement();
  const controller = new AvatarController(renderer, readout, bubble, stage, {
    getNow: () => 180,
    voiceVisualizerElement: visualizer
  });

  controller.handleBridgeMessage({
    type: "dialogue.turn",
    payload: {
      response_text: "hello",
      tts_state: "playing"
    }
  });

  assert.equal(visualizer.hidden, false);
  assert.equal(visualizer.className, "voice-visualizer is-visible state-playing");
  assert.equal(stage.className, "avatar-stage is-state-speaking is-voice-active");
  assert.ok(visualizer.bars.every((bar) => Number(bar.dataset.level) > 0));
}

function testControllerTickRefreshesSpeakingMouthFromRuntime() {
  const renderer = createRendererProbe();
  const readout = createTextElement();
  let now = 120;
  const controller = new AvatarController(renderer, readout, null, null, {
    getNow: () => now
  });

  controller.handleBridgeMessage({
    type: "dialogue.turn",
    payload: {
      response_text: "hello",
      tts_state: "playing"
    }
  });
  const firstMouth = renderer.appliedStates.at(-1).modelCommands.parameters.mouth;
  now = 260;
  controller.tick();

  assert.notEqual(renderer.appliedStates.at(-1).modelCommands.parameters.mouth, firstMouth);
  assert.equal(renderer.appliedStates.at(-1).speakingState.ttsState, "playing");
}

function testControllerConsumesRealTtsPlaybackEnded() {
  const renderer = createRendererProbe();
  const readout = createTextElement();
  const visualizer = createVisualizerElement();
  const controller = new AvatarController(renderer, readout, null, null, {
    getNow: () => 300,
    voiceVisualizerElement: visualizer
  });

  controller.handleBridgeMessage({
    type: "tts.playback",
    payload: {
      request_id: "req-1",
      tts_state: "playing",
      source: "tts_controller"
    }
  });
  assert.equal(renderer.appliedStates.at(-1).speakingState.active, true);
  assert.equal(visualizer.hidden, false);

  controller.handleBridgeMessage({
    type: "tts.playback",
    payload: {
      request_id: "req-1",
      tts_state: "ended",
      source: "tts_controller"
    }
  });

  const applied = renderer.appliedStates.at(-1);
  assert.equal(applied.speakingState.active, false);
  assert.equal(applied.speakingState.closing, true);
  assert.equal(applied.speakingState.source, "tts");
  assert.equal(applied.speakingState.ttsState, "ended");
  assert.equal(applied.modelCommands.parameters.mouth, 0);
  assert.equal(applied.modelCommands.parameters.mouthForm, 0);
  assert.equal(visualizer.hidden, false);
  assert.equal(visualizer.className, "voice-visualizer state-fading");
}

function testControllerTreatsTtsStartedAsPreparingNotPlaying() {
  const renderer = createRendererProbe();
  const readout = createTextElement();
  const stage = createStageElement();
  const visualizer = createVisualizerElement();
  const controller = new AvatarController(renderer, readout, null, stage, {
    getNow: () => 120,
    voiceVisualizerElement: visualizer
  });

  controller.handleBridgeMessage({
    type: "tts.playback",
    payload: {
      request_id: "req-1",
      tts_state: "started",
      source: "tts_controller"
    }
  });

  const applied = renderer.appliedStates.at(-1);
  assert.equal(applied.speakingState.active, false);
  assert.equal(applied.speakingState.pending, true);
  assert.equal(applied.modelCommands.parameters.mouth, 0.04);
  assert.equal(applied.modelCommands.parameters.mouthForm, 0);
  assert.equal(stage.className, "avatar-stage is-state-preparing is-voice-active");
  assert.equal(visualizer.className, "voice-visualizer state-pending");
}

function testControllerExpiresDialogueTurnSpeakingFallback() {
  const renderer = createRendererProbe();
  const readout = createTextElement();
  const stage = createStageElement();
  const visualizer = createVisualizerElement();
  let now = 0;
  const controller = new AvatarController(renderer, readout, null, stage, {
    getNow: () => now,
    voiceVisualizerElement: visualizer
  });

  controller.handleBridgeMessage({
    type: "dialogue.turn",
    payload: {
      response_text: "hello",
      tts_state: "speaking"
    }
  });
  assert.equal(renderer.appliedStates.at(-1).speakingState.active, true);

  now = 6200;
  controller.tick();

  const applied = renderer.appliedStates.at(-1);
  assert.equal(applied.speakingState.active, false);
  assert.equal(applied.speakingState.fallbackExpired, true);
  assert.equal(applied.modelCommands.parameters.mouth, 0);
  assert.equal(applied.modelCommands.parameters.mouthForm, 0);
  assert.equal(stage.className, "avatar-stage is-state-idle is-voice-active");
  assert.equal(visualizer.className, "voice-visualizer state-fading");
}

function testControllerUsesSameTimestampForRuntimeAndFallbackStart() {
  const renderer = createRendererProbe();
  const readout = createTextElement();
  const times = [100, 999];
  const controller = new AvatarController(renderer, readout, null, null, {
    getNow: () => times.shift() ?? 999
  });

  controller.handleBridgeMessage({
    type: "dialogue.turn",
    payload: {
      response_text: "hello",
      tts_state: "speaking"
    }
  });

  assert.equal(renderer.appliedStates.at(-1).emotionState.turn.receivedAt, 100);
}

testControllerRendersSpeechBubbleFromDialogueTurn();
testControllerHidesBubbleForIdleStateWithoutBubble();
testControllerMarksStageWithVisualStateClass();
testControllerUsesVisualIntentForStageClass();
testControllerStoresEmotionAndBehaviorForMappedState();
testControllerPassesRuntimeNowToSpeakingDriver();
testControllerStoresModelCommandsWhenProfileProviderExists();
testControllerPlaysMotionProbe();
testControllerTriggersPointerReactionFromEvent();
testControllerPassesPointerStateToRuntimeAttention();
testControllerRendersVoiceVisualizerForTtsPlaying();
testControllerTickRefreshesSpeakingMouthFromRuntime();
testControllerConsumesRealTtsPlaybackEnded();
testControllerTreatsTtsStartedAsPreparingNotPlaying();
testControllerExpiresDialogueTurnSpeakingFallback();
testControllerUsesSameTimestampForRuntimeAndFallbackStart();
console.log("avatar-controller tests passed");
