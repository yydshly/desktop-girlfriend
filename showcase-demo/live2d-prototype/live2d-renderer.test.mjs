import assert from "node:assert/strict";
import {
  calculateAnimatedLive2DParameters,
  calculateLive2DPlacement,
  getReturnToIdleDelayMs,
  Live2DRenderer,
  mapCommandToModelMotion,
  shouldAutoRotateIdleMotion,
  smoothPointer
} from "./adapters/live2d-renderer.js";

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
testIdleStateDoesNotAnimateMouthOpen();
testIdleStateAddsBreathingMotion();
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

testIdleMotionAutoRotates();
testIdleMotionAutoRotateUsesModelMotionCount();
testReplyMotionDoesNotAutoRotateIdle();

function testPointerSmoothingMovesTowardTarget() {
  const next = smoothPointer({ x: 0, y: 0 }, { x: 1, y: -1 }, 0.25);

  assert.deepEqual(next, { x: 0.25, y: -0.25 });
}

function testPointerSmoothingSnapsTinyDeltas() {
  const next = smoothPointer({ x: 0.999, y: -0.999 }, { x: 1, y: -1 }, 0.25);

  assert.deepEqual(next, { x: 1, y: -1 });
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
testExpressiveMotionSchedulesReturnToIdle();
testAdvanceReturnToIdlePlaysIdleMotion();
console.log("live2d-renderer tests passed");
