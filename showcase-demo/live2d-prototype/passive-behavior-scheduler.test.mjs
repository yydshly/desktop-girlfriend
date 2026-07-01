import assert from "node:assert/strict";
import {
  canRunPassiveBehavior,
  isPointerNearAvatarCenter,
  updateHoverDwellSchedule
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

testPassiveBehaviorAllowsQuietStates();
testPassiveBehaviorBlocksExpressiveStates();
testPointerNearAvatarCenterUsesRadius();
testHoverDwellStartsTimerBeforeReaction();
testHoverDwellCreatesReactionAfterDwell();
testHoverDwellWaitsForCooldown();
testHoverDwellResetsOutsidePassiveState();
console.log("passive-behavior-scheduler tests passed");
