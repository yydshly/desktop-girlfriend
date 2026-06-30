import assert from "node:assert/strict";
import {
  calculateAnimatedLive2DParameters,
  calculateLive2DPlacement,
  Live2DRenderer,
  shouldAutoRotateIdleMotion
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

testSequenceTriggersTapBodyMotion();
testIdleStateTriggersIdleMotion();

function testSpeakingStateAnimatesMouthOpen() {
  const parameters = calculateAnimatedLive2DParameters(
    { ParamMouthOpenY: 0.1, ParamAngleX: 2 },
    { motion: "reply", expression: "speaking" },
    1000
  );

  assert.ok(parameters.ParamMouthOpenY > 0.1);
  assert.equal(parameters.ParamAngleX, 2);
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

function testReplyMotionDoesNotAutoRotateIdle() {
  assert.equal(shouldAutoRotateIdleMotion({ motion: "reply" }), false);
  assert.equal(shouldAutoRotateIdleMotion({ motion: "idle" }), true);
}

testIdleMotionAutoRotates();
testReplyMotionDoesNotAutoRotateIdle();
console.log("live2d-renderer tests passed");
