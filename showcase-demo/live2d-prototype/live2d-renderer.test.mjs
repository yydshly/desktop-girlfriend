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

function testStateDoesNotRepeatSameLive2DExpression() {
  const renderer = new Live2DRenderer(createCanvasProbe());
  const expressions = [];
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

testSequenceTriggersTapBodyMotion();
testAbstractMotionUsesAvailableModelMotionGroups();
testIdleStateTriggersIdleMotion();
testStateAppliesLive2DExpression();
testStateDoesNotRepeatSameLive2DExpression();

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

testSpeakingStateAnimatesMouthOpen();
testSpeakingStateAddsSubtleBodyMotion();
testVisualIntentSpeakingAnimatesMouthOpen();
testIdleStateDoesNotAnimateMouthOpen();

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
