import assert from "node:assert/strict";
import { calculateLive2DPlacement, Live2DRenderer } from "./adapters/live2d-renderer.js";

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
console.log("live2d-renderer tests passed");
