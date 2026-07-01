import assert from "node:assert/strict";
import {
  canRunPassiveBehavior,
  isPointerNearAvatarCenter,
  updateAmbientGestureSchedule,
  updateHoverDwellSchedule,
  updatePassiveBehaviorSchedule
} from "./passive-behavior-scheduler.js";

function testPassiveBehaviorAllowsQuietStates() {
  assert.equal(canRunPassiveBehavior({ motion: "idle" }), true);
  assert.equal(canRunPassiveBehavior({ motion: "think" }), true);
  assert.equal(canRunPassiveBehavior({ motion: "thinking" }), true);
  assert.equal(canRunPassiveBehavior({ motion: "sad" }), true);
}

function testPassiveBehaviorBlocksExpressiveStates() {
  assert.equal(canRunPassiveBehavior({ motion: "reply" }), false);
  assert.equal(canRunPassiveBehavior({ motion: "speak" }), false);
  assert.equal(canRunPassiveBehavior({ motion: "happy" }), false);
}

function testPointerNearAvatarCenterUsesRadius() {
  assert.equal(isPointerNearAvatarCenter({ x: 0.2, y: -0.2 }), true);
  assert.equal(isPointerNearAvatarCenter({ x: 0.7, y: 0 }), false);
  assert.equal(isPointerNearAvatarCenter({ x: "bad", y: 0 }), false);
}

function testHoverDwellStartsTimerBeforeReaction() {
  const result = updateHoverDwellSchedule({
    now: 1000,
    pointer: { x: 0.2, y: -0.1 },
    command: { motion: "idle" },
    hasPointerInput: true
  });

  assert.equal(result.hoverDwellStartedAt, 1000);
  assert.equal(result.reaction, null);
}

function testHoverDwellCreatesReactionAfterDwell() {
  const result = updateHoverDwellSchedule({
    now: 2401,
    pointer: { x: 0.2, y: -0.1 },
    command: { motion: "idle" },
    hasPointerInput: true,
    hoverDwellStartedAt: 1000
  });

  assert.deepEqual(result, {
    hoverDwellStartedAt: 0,
    nextHoverReactionAt: 7601,
    reaction: {
      startedAt: 2401,
      durationMs: 640,
      x: 0.09000000000000001,
      y: -0.155
    }
  });
}

function testHoverDwellWaitsForCooldown() {
  const result = updateHoverDwellSchedule({
    now: 2000,
    pointer: { x: 0.2, y: -0.1 },
    command: { motion: "idle" },
    hasPointerInput: true,
    hoverDwellStartedAt: 1000,
    nextHoverReactionAt: 3000
  });

  assert.equal(result.hoverDwellStartedAt, 1000);
  assert.equal(result.nextHoverReactionAt, 3000);
  assert.equal(result.reaction, null);
}

function testHoverDwellResetsOutsidePassiveState() {
  const result = updateHoverDwellSchedule({
    now: 2000,
    pointer: { x: 0.2, y: -0.1 },
    command: { motion: "reply" },
    hasPointerInput: true,
    hoverDwellStartedAt: 1000
  });

  assert.equal(result.hoverDwellStartedAt, 0);
  assert.equal(result.reaction, null);
}

function testAmbientGestureStartsDuringPassiveState() {
  const result = updateAmbientGestureSchedule({
    now: 7201,
    command: { motion: "idle" },
    nextAmbientGestureAt: 7200,
    ambientGestureIndex: 0,
    intervalMs: 7200
  });

  assert.deepEqual(result, {
    nextAmbientGestureAt: 14401,
    ambientGestureIndex: 1,
    reaction: {
      startedAt: 7201,
      durationMs: 860,
      x: 0.28,
      y: -0.24
    },
    eventDetail: {
      index: 0,
      x: 0.28,
      y: -0.24
    }
  });
}

function testAmbientGestureResetsOutsidePassiveState() {
  const result = updateAmbientGestureSchedule({
    now: 7201,
    command: { motion: "reply" },
    nextAmbientGestureAt: 7200,
    ambientGestureIndex: 2,
    intervalMs: 7200
  });

  assert.deepEqual(result, {
    nextAmbientGestureAt: 14401,
    ambientGestureIndex: 2,
    reaction: null,
    eventDetail: null
  });
}

function testAmbientGestureDoesNotOverrideActiveReaction() {
  const result = updateAmbientGestureSchedule({
    now: 7201,
    command: { motion: "idle" },
    activeReaction: true,
    nextAmbientGestureAt: 7200,
    ambientGestureIndex: 2,
    intervalMs: 7200
  });

  assert.deepEqual(result, {
    nextAmbientGestureAt: 7200,
    ambientGestureIndex: 2,
    reaction: null,
    eventDetail: null
  });
}

function testAmbientGestureUsesDefaultIntervalFallback() {
  const result = updateAmbientGestureSchedule({
    now: 7201,
    command: { motion: "idle" },
    nextAmbientGestureAt: 7200,
    intervalMs: -1
  });

  assert.equal(result.nextAmbientGestureAt, 14401);
}

function testPassiveSchedulePrioritizesHoverOverAmbient() {
  const result = updatePassiveBehaviorSchedule({
    now: 7201,
    pointer: { x: 0.2, y: -0.1 },
    command: { motion: "idle" },
    hasPointerInput: true,
    hoverDwellStartedAt: 5000,
    nextAmbientGestureAt: 7200,
    ambientGestureIndex: 0
  });

  assert.equal(result.eventType, "pointer.hover-dwell");
  assert.equal(result.nextAmbientGestureAt, 7200);
  assert.equal(result.ambientGestureIndex, 0);
  assert.deepEqual(result.eventDetail, { x: 0.09000000000000001, y: -0.155 });
}

function testPassiveScheduleFallsThroughToAmbient() {
  const result = updatePassiveBehaviorSchedule({
    now: 7201,
    pointer: { x: 0.9, y: 0 },
    command: { motion: "idle" },
    hasPointerInput: true,
    hoverDwellStartedAt: 5000,
    nextAmbientGestureAt: 7200,
    ambientGestureIndex: 0
  });

  assert.equal(result.eventType, "ambient.gesture");
  assert.equal(result.hoverDwellStartedAt, 0);
  assert.equal(result.nextAmbientGestureAt, 14401);
  assert.equal(result.ambientGestureIndex, 1);
}

testPassiveBehaviorAllowsQuietStates();
testPassiveBehaviorBlocksExpressiveStates();
testPointerNearAvatarCenterUsesRadius();
testHoverDwellStartsTimerBeforeReaction();
testHoverDwellCreatesReactionAfterDwell();
testHoverDwellWaitsForCooldown();
testHoverDwellResetsOutsidePassiveState();
testAmbientGestureStartsDuringPassiveState();
testAmbientGestureResetsOutsidePassiveState();
testAmbientGestureDoesNotOverrideActiveReaction();
testAmbientGestureUsesDefaultIntervalFallback();
testPassiveSchedulePrioritizesHoverOverAmbient();
testPassiveScheduleFallsThroughToAmbient();
console.log("passive-behavior-scheduler tests passed");
