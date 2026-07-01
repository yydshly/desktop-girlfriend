import assert from "node:assert/strict";
import {
  calculateAnimatedLive2DParameters,
  calculateLive2DPlacement,
  calculatePointerFollowOffset,
  calculatePointerReactionEffect,
  getReturnToIdleDelayMs,
  Live2DRenderer,
  mapCommandToModelMotion,
  shouldAutoRotateIdleMotion,
  smoothPointer
} from "./adapters/live2d-renderer.js";
import { mapStateToLive2DCommands } from "./live2d-parameter-mapper.js";

function createCanvasProbe() {
  return {
    width: 900,
    height: 1200,
    contextRequests: 0,
    getContext() {
      this.contextRequests += 1;
      throw new Error("2D context should not be requested while Live2D is loading");
    }
  };
}

function testPointerDoesNotClaimCanvasWhileLoadingLive2D() {
  const canvas = createCanvasProbe();
  const renderer = new Live2DRenderer(canvas);
  renderer.loadState = "loading-model";

  renderer.setPointer(0.2, -0.1);

  assert.equal(canvas.contextRequests, 0);
}

function testStateDoesNotClaimCanvasWhileLoadingLive2D() {
  const canvas = createCanvasProbe();
  const renderer = new Live2DRenderer(canvas);
  renderer.loadState = "loading-sdk";

  renderer.applyState({ emotion: "happy", mouth: 0.4 });

  assert.equal(canvas.contextRequests, 0);
}

testPointerDoesNotClaimCanvasWhileLoadingLive2D();
testStateDoesNotClaimCanvasWhileLoadingLive2D();

function testDisabledTextureFallbackDoesNotClaimCanvasOnError() {
  const canvas = createCanvasProbe();
  const renderer = new Live2DRenderer(canvas, { allowTextureFallback: false });
  renderer.loadState = "error";
  renderer.previewImage = { width: 1024, height: 1024 };

  renderer.draw();

  assert.equal(canvas.contextRequests, 0);
  assert.equal(renderer.shouldDrawFallback(), false);
}

testDisabledTextureFallbackDoesNotClaimCanvasOnError();

function testPlacementFillsStageMoreAssertively() {
  const placement = calculateLive2DPlacement(
    { width: 900, height: 1200 },
    { width: 300, height: 1000 }
  );

  assert.equal(placement.scale, 1.296);
  assert.equal(placement.x, 450);
  assert.equal(placement.y, 660);
}

testPlacementFillsStageMoreAssertively();

function testPlacementAcceptsProfileTuning() {
  const placement = calculateLive2DPlacement(
    { width: 900, height: 1200 },
    { width: 300, height: 1000 },
    {
      scaleMultiplier: 1.1,
      xOffsetRatio: -0.05,
      yRatio: 0.58
    }
  );

  assert.equal(placement.scale, 1.426);
  assert.equal(placement.x, 405);
  assert.equal(placement.y, 696);
}

testPlacementAcceptsProfileTuning();

function testPointerFollowOffsetKeepsContinuousMouseMotionSubtle() {
  const offset = calculatePointerFollowOffset(
    { width: 900, height: 1200 },
    { x: 0.8, y: -0.5 }
  );

  assert.equal(offset.x, 5.4);
  assert.equal(offset.y, -3);
  assert.equal(offset.strength, 0.943);
}

function testPointerFollowOffsetCanBeDisabled() {
  const offset = calculatePointerFollowOffset(
    { width: 900, height: 1200 },
    { x: 0.8, y: -0.5 },
    { pointerFollow: false }
  );

  assert.deepEqual(offset, { x: 0, y: 0, strength: 0 });
}

function testPointerReactionEffectCreatesClickPulse() {
  const effect = calculatePointerReactionEffect(
    { startedAt: 1000, x: 0.5, y: -0.25 },
    1280
  );

  assert.equal(effect.active, true);
  assert.equal(effect.envelope, 1);
  assert.equal(effect.offsetX, 12);
  assert.equal(effect.offsetY, -13.5);
  assert.equal(effect.scaleMultiplier, 1.028);
}

function testPointerReactionEffectExpires() {
  const effect = calculatePointerReactionEffect(
    { startedAt: 1000, x: 0.5, y: -0.25 },
    1700
  );

  assert.deepEqual(effect, {
    active: false,
    envelope: 0,
    x: 0,
    y: 0,
    offsetX: 0,
    offsetY: 0,
    scaleMultiplier: 1
  });
}

function testPlacementAppliesPointerFollowOffset() {
  const renderer = new Live2DRenderer(createCanvasProbe());
  renderer.pointer = { x: 0.8, y: -0.5 };
  renderer.live2dModel = {
    width: 300,
    height: 1000,
    scale: {
      value: 0,
      set(value) {
        this.value = value;
      }
    },
    position: {
      value: { x: 0, y: 0 },
      set(x, y) {
        this.value = { x, y };
      }
    }
  };

  const placement = renderer.applyLive2DPlacement();

  assert.equal(renderer.live2dModel.position.value.x, 455.4);
  assert.equal(renderer.live2dModel.position.value.y, 657);
  assert.deepEqual(placement.followOffset, { x: 5.4, y: -3, strength: 0.943 });
}

function testPlacementUsesUnscaledModelSizeAcrossRepeatedFrames() {
  const renderer = new Live2DRenderer(createCanvasProbe());
  const model = {
    naturalWidth: 300,
    naturalHeight: 1000,
    scaleValue: 1,
    get width() {
      return this.naturalWidth * this.scaleValue;
    },
    get height() {
      return this.naturalHeight * this.scaleValue;
    },
    scale: {
      x: 1,
      y: 1,
      set(value) {
        model.scaleValue = value;
        this.x = value;
        this.y = value;
      }
    },
    position: {
      set() {}
    }
  };
  renderer.live2dModel = model;

  const first = renderer.applyLive2DPlacement();
  const second = renderer.applyLive2DPlacement();

  assert.equal(first.scale, 1.296);
  assert.equal(second.scale, 1.296);
}

testPointerFollowOffsetKeepsContinuousMouseMotionSubtle();
testPointerFollowOffsetCanBeDisabled();
testPointerReactionEffectCreatesClickPulse();
testPointerReactionEffectExpires();
testPlacementAppliesPointerFollowOffset();
testPlacementUsesUnscaledModelSizeAcrossRepeatedFrames();

function testSequenceTriggersTapBodyMotion() {
  const renderer = new Live2DRenderer(createCanvasProbe());
  const calls = [];
  renderer.live2dModel = {
    motion(group, index) {
      calls.push({ group, index });
    },
    internalModel: {
      coreModel: {
        setParameterValueById() {}
      }
    }
  };

  renderer.applyState({ sequence: "greet", motion: "happy", emotion: "happy" });

  assert.deepEqual(calls, [{ group: "TapBody", index: 0 }]);
}

function testModelAdapterCommandOverridesLegacyMotionMapping() {
  const renderer = new Live2DRenderer(createCanvasProbe());
  const calls = [];
  renderer.live2dModel = {
    motion(group, index) {
      calls.push({ group, index });
    },
    internalModel: {
      coreModel: {
        setParameterValueById() {}
      }
    }
  };

  renderer.applyState({
    motion: "happy",
    emotion: "happy",
    modelCommands: {
      motion: {
        group: "Idle",
        index: 4,
        action: "comfort"
      }
    }
  });

  assert.deepEqual(calls, [{ group: "Idle", index: 4 }]);
  assert.deepEqual(renderer.activeMotion, {
    group: "Idle",
    index: 4,
    source: "model-adapter:comfort"
  });
}

function testIdleStateTriggersIdleMotion() {
  const renderer = new Live2DRenderer(createCanvasProbe());
  const calls = [];
  renderer.live2dModel = {
    motion(group, index) {
      calls.push({ group, index });
    },
    internalModel: {
      coreModel: {
        setParameterValueById() {}
      }
    }
  };

  renderer.applyState({ motion: "idle", emotion: "neutral" });

  assert.deepEqual(calls, [{ group: "Idle", index: 0 }]);
}

function testStateAppliesLive2DExpression() {
  const renderer = new Live2DRenderer(createCanvasProbe());
  const expressions = [];
  renderer.model = { expressionNames: ["happy"] };
  renderer.live2dModel = {
    expression(name) {
      expressions.push(name);
    },
    motion() {},
    internalModel: {
      coreModel: {
        setParameterValueById() {}
      }
    }
  };

  renderer.applyState({ motion: "happy", emotion: "happy" });

  assert.deepEqual(expressions, ["happy"]);
  assert.equal(renderer.activeExpression, "happy");
}

function testModelAdapterExpressionOverridesLegacyExpressionMapping() {
  const renderer = new Live2DRenderer(createCanvasProbe());
  const expressions = [];
  renderer.model = { expressionNames: ["smile"] };
  renderer.live2dModel = {
    expression(name) {
      expressions.push(name);
    },
    motion() {},
    internalModel: {
      coreModel: {
        setParameterValueById() {}
      }
    }
  };

  renderer.applyState({
    emotion: "happy",
    modelCommands: {
      expression: {
        name: "smile",
        semantic: "engaged"
      }
    }
  });

  assert.deepEqual(expressions, ["smile"]);
  assert.equal(renderer.activeExpression, "smile");
}

function testModelAdapterParametersOverrideLegacyStateParameters() {
  const renderer = new Live2DRenderer(createCanvasProbe());
  const parameters = {};
  renderer.live2dModel = {
    expression() {},
    motion() {},
    internalModel: {
      coreModel: {
        setParameterValueById(id, value) {
          parameters[id] = value;
        }
      }
    }
  };

  renderer.applyState({
    emotion: "neutral",
    mouth: 0,
    intensity: 0,
    modelCommands: {
      parameters: {
        mouth: 0.72,
        intensity: 0.8,
        gaze: "cursor"
      }
    }
  });

  assert.equal(parameters.ParamMouthOpenY, 0.72);
  assert.equal(parameters.ParamBreath, 0.9);
}

function testStateSkipsUnavailableLive2DExpression() {
  const renderer = new Live2DRenderer(createCanvasProbe());
  const expressions = [];
  renderer.model = { expressionNames: ["smile"] };
  renderer.live2dModel = {
    expression(name) {
      expressions.push(name);
    },
    motion() {},
    internalModel: {
      coreModel: {
        setParameterValueById() {}
      }
    }
  };

  renderer.applyState({ motion: "happy", emotion: "happy" });

  assert.deepEqual(expressions, []);
  assert.equal(renderer.activeExpression, "");
}

function testStateDoesNotRepeatSameLive2DExpression() {
  const renderer = new Live2DRenderer(createCanvasProbe());
  const expressions = [];
  renderer.model = { expressionNames: ["happy"] };
  renderer.live2dModel = {
    expression(name) {
      expressions.push(name);
    },
    motion() {},
    internalModel: {
      coreModel: {
        setParameterValueById() {}
      }
    }
  };

  renderer.applyState({ motion: "happy", emotion: "happy" });
  renderer.applyState({ motion: "happy", emotion: "happy" });

  assert.deepEqual(expressions, ["happy"]);
}

function testStatusReportsModelCapabilities() {
  const statuses = [];
  const renderer = new Live2DRenderer(createCanvasProbe(), {
    onStatusChange: (status) => statuses.push(status)
  });
  renderer.model = {
    expressionCount: 2,
    expressionNames: ["happy", "sad"],
    motionCount: 3,
    motionGroupCounts: { Idle: 2, TapBody: 1 }
  };

  renderer.emitStatus();

  assert.deepEqual(statuses.at(-1).modelCapabilities, {
    expressionCount: 2,
    expressionNames: ["happy", "sad"],
    motionCount: 3,
    motionGroupCounts: { Idle: 2, TapBody: 1 }
  });
}

function testStatusReportsCommandDiagnostics() {
  const statuses = [];
  const renderer = new Live2DRenderer(createCanvasProbe(), {
    onStatusChange: (status) => statuses.push(status)
  });
  renderer.model = {
    expressionNames: ["happy"],
    motionGroupCounts: { Idle: 9, TapBody: 1 }
  };
  renderer.live2dModel = {
    expression() {},
    motion() {},
    internalModel: {
      coreModel: {
        setParameterValueById() {}
      }
    }
  };

  renderer.applyState({ motion: "happy", emotion: "happy" });

  assert.deepEqual(statuses.at(-1).commandDiagnostics, {
    requestedMotion: "happy",
    requestedExpression: "happy",
    resolvedMotion: { group: "TapBody", index: 0, source: "happy" },
    resolvedExpression: "happy",
    expressionSupport: "available"
  });
}

function testStatusReportsModelAdapterCommands() {
  const statuses = [];
  const renderer = new Live2DRenderer(createCanvasProbe(), {
    onStatusChange: (status) => statuses.push(status)
  });
  renderer.live2dModel = {
    expression() {},
    motion() {},
    internalModel: {
      coreModel: {
        setParameterValueById() {}
      }
    }
  };

  renderer.applyState({
    emotion: "happy",
    modelCommands: {
      motion: { group: "TapBody", index: 0, action: "happy" },
      expression: { name: "smile", semantic: "engaged" },
      parameters: { mouth: 0.64, intensity: 0.7, gaze: "cursor" }
    }
  });

  assert.deepEqual(statuses.at(-1).modelAdapterCommands, {
    motion: { group: "TapBody", index: 0, action: "happy" },
    expression: { name: "smile", semantic: "engaged" },
    parameters: { gaze: "cursor", mouth: 0.64, intensity: 0.7 }
  });
}

function testStatusReportsUnsupportedExpressionDiagnostic() {
  const statuses = [];
  const renderer = new Live2DRenderer(createCanvasProbe(), {
    onStatusChange: (status) => statuses.push(status)
  });
  renderer.model = {
    expressionNames: ["smile"],
    motionGroupCounts: { Idle: 9 }
  };
  renderer.live2dModel = {
    expression() {},
    motion() {},
    internalModel: {
      coreModel: {
        setParameterValueById() {}
      }
    }
  };

  renderer.applyState({ motion: "sad", emotion: "sad" });

  assert.equal(statuses.at(-1).commandDiagnostics.requestedExpression, "sad");
  assert.equal(statuses.at(-1).commandDiagnostics.resolvedExpression, "");
  assert.equal(statuses.at(-1).commandDiagnostics.expressionSupport, "missing");
}

function testMotionProbePlaysRequestedModelMotion() {
  const statuses = [];
  const calls = [];
  const renderer = new Live2DRenderer(createCanvasProbe(), {
    onStatusChange: (status) => statuses.push(status)
  });
  renderer.live2dModel = {
    motion(group, index) {
      calls.push({ group, index });
    }
  };

  renderer.playMotionProbe("Idle", 4);

  assert.deepEqual(calls, [{ group: "Idle", index: 4 }]);
  assert.deepEqual(renderer.activeMotion, {
    group: "Idle",
    index: 4,
    source: "manual.motion-probe"
  });
  assert.deepEqual(statuses.at(-1).activeMotion, renderer.activeMotion);
}

function testAbstractMotionUsesAvailableModelMotionGroups() {
  assert.deepEqual(
    mapCommandToModelMotion({ motion: "reply" }, { TapBody: 1, Idle: 3 }),
    { group: "TapBody", index: 0, source: "reply" }
  );
  assert.deepEqual(
    mapCommandToModelMotion({ motion: "reply" }, { Idle: 3 }),
    { group: "Idle", index: 0, source: "reply" }
  );
}

function testAbstractMotionUsesDistinctIdleVariants() {
  assert.deepEqual(
    mapCommandToModelMotion({ motion: "think" }, { Idle: 9 }),
    { group: "Idle", index: 1, source: "think" }
  );
  assert.deepEqual(
    mapCommandToModelMotion({ motion: "sad" }, { Idle: 9 }),
    { group: "Idle", index: 2, source: "sad" }
  );
  assert.deepEqual(
    mapCommandToModelMotion({ motion: "listen" }, { Idle: 9 }),
    { group: "Idle", index: 3, source: "listen" }
  );
}

function testAbstractMotionClampsIdleVariantToModelMotionCount() {
  assert.deepEqual(
    mapCommandToModelMotion({ motion: "comfort" }, { Idle: 2 }),
    { group: "Idle", index: 0, source: "comfort" }
  );
}

function testAbstractMotionUsesConfiguredBinding() {
  assert.deepEqual(
    mapCommandToModelMotion(
      { motion: "happy" },
      { Idle: 9, TapBody: 1 },
      { happy: { group: "Idle", index: 5 } }
    ),
    { group: "Idle", index: 5, source: "happy-binding" }
  );
}

function testAbstractMotionIgnoresUnavailableConfiguredBinding() {
  assert.deepEqual(
    mapCommandToModelMotion(
      { motion: "happy" },
      { Idle: 2 },
      { happy: { group: "Idle", index: 5 } }
    ),
    { group: "Idle", index: 0, source: "happy" }
  );
}

function testRendererUsesRuntimeMotionBindings() {
  const renderer = new Live2DRenderer(createCanvasProbe());
  const calls = [];
  renderer.model = { motionGroupCounts: { Idle: 9, TapBody: 1 } };
  renderer.live2dModel = {
    motion(group, index) {
      calls.push({ group, index });
    },
    internalModel: {
      coreModel: {
        setParameterValueById() {}
      }
    }
  };

  renderer.setMotionBindings({ happy: { group: "Idle", index: 5 } });
  renderer.applyState({ motion: "happy", emotion: "happy" });

  assert.deepEqual(calls, [{ group: "Idle", index: 5 }]);
}

testSequenceTriggersTapBodyMotion();
testModelAdapterCommandOverridesLegacyMotionMapping();
testAbstractMotionUsesAvailableModelMotionGroups();
testAbstractMotionUsesDistinctIdleVariants();
testAbstractMotionClampsIdleVariantToModelMotionCount();
testAbstractMotionUsesConfiguredBinding();
testAbstractMotionIgnoresUnavailableConfiguredBinding();
testRendererUsesRuntimeMotionBindings();
testIdleStateTriggersIdleMotion();
testStateAppliesLive2DExpression();
testModelAdapterExpressionOverridesLegacyExpressionMapping();
testModelAdapterParametersOverrideLegacyStateParameters();
testStateSkipsUnavailableLive2DExpression();
testStateDoesNotRepeatSameLive2DExpression();
testStatusReportsModelCapabilities();
testStatusReportsCommandDiagnostics();
testStatusReportsModelAdapterCommands();
testStatusReportsUnsupportedExpressionDiagnostic();
testMotionProbePlaysRequestedModelMotion();

function testSpeakingStateAnimatesMouthOpen() {
  const parameters = calculateAnimatedLive2DParameters(
    { ParamMouthOpenY: 0.1, ParamAngleX: 2 },
    { motion: "reply", expression: "speaking" },
    1000
  );

  assert.ok(parameters.ParamMouthOpenY > 0.1);
  assert.notEqual(parameters.ParamAngleX, 2);
}

function testSpeakingStateAddsSubtleBodyMotion() {
  const parameters = calculateAnimatedLive2DParameters(
    { ParamMouthOpenY: 0.1, ParamAngleX: 0, ParamBodyAngleX: 0 },
    { motion: "reply", expression: "speaking" },
    900
  );

  assert.notEqual(parameters.ParamAngleX, 0);
  assert.notEqual(parameters.ParamBodyAngleX, 0);
}

function testVisualIntentSpeakingAnimatesMouthOpen() {
  const parameters = calculateAnimatedLive2DParameters(
    { ParamMouthOpenY: 0.1, ParamAngleX: 0 },
    { motion: "customTalk", visualIntent: "speaking" },
    100
  );

  assert.ok(parameters.ParamMouthOpenY > 0.1);
  assert.notEqual(parameters.ParamAngleX, 0);
}

function testModelAdapterSpeakActionAnimatesMouthOpen() {
  const parameters = calculateAnimatedLive2DParameters(
    { ParamMouthOpenY: 0.1, ParamAngleX: 0 },
    {
      modelCommands: {
        motion: { action: "speak" },
        expression: { semantic: "engaged" },
        parameters: { mouth: 0.65 }
      }
    },
    1000
  );

  assert.ok(parameters.ParamMouthOpenY > 0.1);
  assert.notEqual(parameters.ParamAngleX, 0);
}

function testIdleStateDoesNotAnimateMouthOpen() {
  const parameters = calculateAnimatedLive2DParameters(
    { ParamMouthOpenY: 0.1 },
    { motion: "idle", expression: "neutral" },
    1000
  );

  assert.equal(parameters.ParamMouthOpenY, 0.1);
}

function testIdleStateAddsBreathingMotion() {
  const parameters = calculateAnimatedLive2DParameters(
    { ParamBreath: 0.55, ParamAngleZ: 0, ParamBodyAngleX: 0 },
    { motion: "idle", expression: "neutral" },
    1000
  );

  assert.notEqual(parameters.ParamBreath, 0.55);
  assert.notEqual(parameters.ParamAngleZ, 0);
  assert.notEqual(parameters.ParamBodyAngleX, 0);
}

function testIdleStateAddsEyeAndHeadMicroMotion() {
  const parameters = calculateAnimatedLive2DParameters(
    {
      ParamAngleY: 0,
      ParamEyeBallX: 0,
      ParamEyeBallY: 0,
      ParamBodyAngleY: 0
    },
    { motion: "idle", expression: "neutral" },
    1400
  );

  assert.notEqual(parameters.ParamAngleY, 0);
  assert.notEqual(parameters.ParamEyeBallX, 0);
  assert.notEqual(parameters.ParamEyeBallY, 0);
  assert.notEqual(parameters.ParamBodyAngleY, 0);
}

function testThinkingStateAddsFocusedMicroMotion() {
  const parameters = calculateAnimatedLive2DParameters(
    { ParamAngleY: 0, ParamEyeBallY: 0, ParamBodyAngleX: 0 },
    { motion: "think", expression: "thinking" },
    1000
  );

  assert.notEqual(parameters.ParamAngleY, 0);
  assert.notEqual(parameters.ParamEyeBallY, 0);
  assert.notEqual(parameters.ParamBodyAngleX, 0);
}

testSpeakingStateAnimatesMouthOpen();
testSpeakingStateAddsSubtleBodyMotion();
testVisualIntentSpeakingAnimatesMouthOpen();
testModelAdapterSpeakActionAnimatesMouthOpen();
testIdleStateDoesNotAnimateMouthOpen();
testIdleStateAddsBreathingMotion();
testIdleStateAddsEyeAndHeadMicroMotion();
testThinkingStateAddsFocusedMicroMotion();

function testIdleMotionAutoRotates() {
  const renderer = new Live2DRenderer(createCanvasProbe());
  const calls = [];
  renderer.live2dModel = {
    motion(group, index) {
      calls.push({ group, index });
    },
    internalModel: {
      coreModel: {
        setParameterValueById() {}
      }
    }
  };
  renderer.lastCommands = { motion: "idle", parameters: {} };

  renderer.advanceIdleMotion(7000);

  assert.deepEqual(calls, [{ group: "Idle", index: 1 }]);
}

function testIdleMotionAutoRotateUsesModelMotionCount() {
  const renderer = new Live2DRenderer(createCanvasProbe());
  const calls = [];
  renderer.live2dModel = {
    motion(group, index) {
      calls.push({ group, index });
    },
    internalModel: {
      coreModel: {
        setParameterValueById() {}
      }
    }
  };
  renderer.model = { motionGroupCounts: { Idle: 2 } };
  renderer.idleMotionIndex = 1;
  renderer.lastCommands = { motion: "idle", parameters: {} };

  renderer.advanceIdleMotion(7000);

  assert.deepEqual(calls, [{ group: "Idle", index: 0 }]);
}

function testReplyMotionDoesNotAutoRotateIdle() {
  assert.equal(shouldAutoRotateIdleMotion({ motion: "reply" }), false);
  assert.equal(shouldAutoRotateIdleMotion({ motion: "idle" }), true);
}

function testAmbientGestureStartsDuringIdle() {
  const renderer = new Live2DRenderer(createCanvasProbe());
  renderer.lastCommands = { motion: "idle", parameters: {} };
  renderer.nextAmbientGestureAt = 7200;

  renderer.advanceAmbientGesture(7201);

  assert.equal(renderer.pointerReaction.startedAt, 7201);
  assert.equal(renderer.pointerReaction.x, 0.28);
  assert.equal(renderer.pointerReaction.y, -0.24);
}

function testAmbientGestureDoesNotInterruptReply() {
  const renderer = new Live2DRenderer(createCanvasProbe());
  renderer.lastCommands = { motion: "reply", parameters: {} };
  renderer.nextAmbientGestureAt = 7200;

  renderer.advanceAmbientGesture(7201);

  assert.equal(renderer.pointerReaction.startedAt, 0);
  assert.equal(renderer.nextAmbientGestureAt, 14401);
}

function testAmbientGestureDoesNotOverrideActiveTapReaction() {
  const renderer = new Live2DRenderer(createCanvasProbe());
  renderer.lastCommands = { motion: "idle", parameters: {} };
  renderer.nextAmbientGestureAt = 7200;
  renderer.pointerReaction = { startedAt: 7000, x: 0.6, y: -0.4 };

  renderer.advanceAmbientGesture(7201);

  assert.deepEqual(renderer.pointerReaction, { startedAt: 7000, x: 0.6, y: -0.4 });
}

function testHoverDwellReactionStartsNearAvatarCenter() {
  const renderer = new Live2DRenderer(createCanvasProbe());
  renderer.lastCommands = { motion: "idle", parameters: {} };
  renderer.pointer = { x: 0.22, y: -0.1 };
  renderer.hasPointerInput = true;

  renderer.advanceHoverDwell(1000);
  renderer.advanceHoverDwell(2401);

  assert.equal(renderer.pointerReaction.startedAt, 2401);
  assert.equal(renderer.pointerReaction.durationMs, 640);
  assert.equal(renderer.nextHoverReactionAt, 7601);
  assert.ok(renderer.pointerReaction.x > 0);
  assert.ok(renderer.pointerReaction.y < 0);
}

function testHoverDwellIgnoresLargePointerDistance() {
  const renderer = new Live2DRenderer(createCanvasProbe());
  renderer.lastCommands = { motion: "idle", parameters: {} };
  renderer.pointer = { x: 0.9, y: 0 };
  renderer.hasPointerInput = true;

  renderer.advanceHoverDwell(1000);
  renderer.advanceHoverDwell(3000);

  assert.equal(renderer.pointerReaction.startedAt, 0);
  assert.equal(renderer.hoverDwellStartedAt, 0);
}

function testHoverDwellDoesNotStartBeforePointerInput() {
  const renderer = new Live2DRenderer(createCanvasProbe());
  renderer.lastCommands = { motion: "idle", parameters: {} };
  renderer.pointer = { x: 0.1, y: -0.1 };

  renderer.advanceHoverDwell(1000);
  renderer.advanceHoverDwell(3000);

  assert.equal(renderer.pointerReaction.startedAt, 0);
}

function testHoverDwellDoesNotInterruptReply() {
  const renderer = new Live2DRenderer(createCanvasProbe());
  renderer.lastCommands = { motion: "reply", parameters: {} };
  renderer.pointer = { x: 0.1, y: -0.1 };
  renderer.hasPointerInput = true;

  renderer.advanceHoverDwell(1000);
  renderer.advanceHoverDwell(3000);

  assert.equal(renderer.pointerReaction.startedAt, 0);
  assert.equal(renderer.hoverDwellStartedAt, 0);
}

function testHoverDwellDoesNotOverrideActiveTapReaction() {
  const renderer = new Live2DRenderer(createCanvasProbe());
  renderer.lastCommands = { motion: "idle", parameters: {} };
  renderer.pointer = { x: 0.1, y: -0.1 };
  renderer.hasPointerInput = true;
  renderer.pointerReaction = { startedAt: 1800, durationMs: 1200, x: 0.6, y: -0.4 };

  renderer.advanceHoverDwell(1000);
  renderer.advanceHoverDwell(2500);

  assert.deepEqual(renderer.pointerReaction, { startedAt: 1800, durationMs: 1200, x: 0.6, y: -0.4 });
}

function testBehaviorEventsAreExposedInRendererStatus() {
  const statuses = [];
  const renderer = new Live2DRenderer(createCanvasProbe(), {
    onStatusChange: (status) => statuses.push(status)
  });

  renderer.recordBehaviorEvent("pointer.hover-dwell", { x: 0.1, y: -0.2 }, 1234);
  renderer.emitStatus();

  assert.deepEqual(statuses.at(-1).behaviorEvents, [
    { type: "pointer.hover-dwell", at: 1234, detail: { x: 0.1, y: -0.2 } }
  ]);
}

function testBehaviorEventLogKeepsRecentEvents() {
  const renderer = new Live2DRenderer(createCanvasProbe());

  for (let index = 0; index < 14; index += 1) {
    renderer.recordBehaviorEvent("motion.play", { index }, 1000 + index);
  }

  assert.equal(renderer.behaviorEvents.length, 12);
  assert.equal(renderer.behaviorEvents[0].detail.index, 13);
  assert.equal(renderer.behaviorEvents.at(-1).detail.index, 2);
}

testIdleMotionAutoRotates();
testIdleMotionAutoRotateUsesModelMotionCount();
testReplyMotionDoesNotAutoRotateIdle();
testAmbientGestureStartsDuringIdle();
testAmbientGestureDoesNotInterruptReply();
testAmbientGestureDoesNotOverrideActiveTapReaction();
testHoverDwellReactionStartsNearAvatarCenter();
testHoverDwellIgnoresLargePointerDistance();
testHoverDwellDoesNotStartBeforePointerInput();
testHoverDwellDoesNotInterruptReply();
testHoverDwellDoesNotOverrideActiveTapReaction();
testBehaviorEventsAreExposedInRendererStatus();
testBehaviorEventLogKeepsRecentEvents();

function testPointerSmoothingMovesTowardTarget() {
  const next = smoothPointer({ x: 0, y: 0 }, { x: 1, y: -1 }, 0.25);

  assert.deepEqual(next, { x: 0.25, y: -0.25 });
}

function testPointerSmoothingSnapsTinyDeltas() {
  const next = smoothPointer({ x: 0.999, y: -0.999 }, { x: 1, y: -1 }, 0.25);

  assert.deepEqual(next, { x: 1, y: -1 });
}

function testMappedPointerCarriesGazeMetadata() {
  const command = mapStateToLive2DCommands(
    { emotion: "neutral", intensity: 0.8 },
    { x: 0.6, y: -0.4 }
  );

  assert.deepEqual(command.pointer, { x: 0.6, y: -0.4, strength: 0.721 });
}

function testMappedPointerPrioritizesHeadAndEyeTracking() {
  const command = mapStateToLive2DCommands(
    { emotion: "neutral", intensity: 0.25 },
    { x: 0.8, y: -0.5 }
  );

  assert.ok(command.parameters.ParamAngleX >= 28);
  assert.ok(command.parameters.ParamAngleY >= 15);
  assert.ok(command.parameters.ParamBodyAngleX >= 11);
  assert.equal(command.parameters.ParamEyeBallX, 1);
  assert.equal(command.parameters.ParamEyeBallY, 0.75);
}

function testMappedPointerUsesInteractionProfileMultipliers() {
  const command = mapStateToLive2DCommands(
    { emotion: "neutral", intensity: 0.25 },
    { x: 0.8, y: -0.5 },
    {
      headTrackingMultiplier: 0.5,
      eyeTrackingMultiplier: 0.5,
      bodyTrackingMultiplier: 0.25
    }
  );

  assert.ok(command.parameters.ParamAngleX < 20);
  assert.ok(command.parameters.ParamBodyAngleX < 4);
  assert.equal(command.parameters.ParamEyeBallX, 0.5);
  assert.equal(command.parameters.ParamEyeBallY, 0.375);
}

function testStrongPointerGazeDampsIdleEyeDrift() {
  const withoutPointer = calculateAnimatedLive2DParameters(
    { ParamEyeBallX: 0.8, ParamEyeBallY: -0.8 },
    { motion: "idle", expression: "neutral" },
    1400
  );
  const withPointer = calculateAnimatedLive2DParameters(
    { ParamEyeBallX: 0.8, ParamEyeBallY: -0.8 },
    { motion: "idle", expression: "neutral", pointer: { x: 0.8, y: -0.8, strength: 1 } },
    1400
  );

  assert.ok(Math.abs(withPointer.ParamEyeBallX - 0.8) < Math.abs(withoutPointer.ParamEyeBallX - 0.8));
  assert.ok(Math.abs(withPointer.ParamEyeBallY + 0.8) < Math.abs(withoutPointer.ParamEyeBallY + 0.8));
}

function testPointerGazeClampsEyeParameters() {
  const parameters = calculateAnimatedLive2DParameters(
    { ParamEyeBallX: 1, ParamEyeBallY: -1 },
    { motion: "idle", expression: "neutral", pointer: { x: 1, y: -1, strength: 1 } },
    1400
  );

  assert.equal(parameters.ParamEyeBallX, 1);
  assert.ok(parameters.ParamEyeBallY >= -1);
}

function testPointerReactionAddsBodyAndHeadMotion() {
  const parameters = calculateAnimatedLive2DParameters(
    { ParamAngleX: 0, ParamAngleY: 0, ParamAngleZ: 0, ParamBodyAngleX: 0, ParamBodyAngleY: 0 },
    {
      motion: "idle",
      expression: "neutral",
      pointerReaction: {
        active: true,
        envelope: 1,
        x: 0.5,
        y: -0.25
      }
    },
    1000
  );

  assert.ok(parameters.ParamAngleX > 0);
  assert.ok(parameters.ParamAngleY > 0);
  assert.ok(parameters.ParamAngleZ < 0);
  assert.ok(parameters.ParamBodyAngleX > 0);
  assert.ok(parameters.ParamBodyAngleY > 0);
}

function testExpressiveMotionSchedulesReturnToIdle() {
  assert.equal(getReturnToIdleDelayMs({ motion: "reply" }), 4200);
  assert.equal(getReturnToIdleDelayMs({ motion: "comfort" }), 4200);
  assert.equal(getReturnToIdleDelayMs({ motion: "idle" }), 0);
}

function testAdvanceReturnToIdlePlaysIdleMotion() {
  const renderer = new Live2DRenderer(createCanvasProbe());
  const calls = [];
  renderer.live2dModel = {
    motion(group, index) {
      calls.push({ group, index });
    },
    internalModel: {
      coreModel: {
        setParameterValueById() {}
      }
    }
  };
  renderer.returnToIdleAt = 100;
  renderer.lastCommands = { motion: "reply", parameters: {} };

  renderer.advanceReturnToIdle(101);

  assert.deepEqual(calls, [{ group: "Idle", index: 0 }]);
  assert.equal(renderer.currentState.motion, "idle");
  assert.equal(renderer.returnToIdleAt, 0);
}

testPointerSmoothingMovesTowardTarget();
testPointerSmoothingSnapsTinyDeltas();
testMappedPointerCarriesGazeMetadata();
testMappedPointerPrioritizesHeadAndEyeTracking();
testMappedPointerUsesInteractionProfileMultipliers();
testStrongPointerGazeDampsIdleEyeDrift();
testPointerGazeClampsEyeParameters();
testPointerReactionAddsBodyAndHeadMotion();
testExpressiveMotionSchedulesReturnToIdle();
testAdvanceReturnToIdlePlaysIdleMotion();
console.log("live2d-renderer tests passed");
