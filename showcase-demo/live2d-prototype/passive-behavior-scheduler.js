const PASSIVE_MOTIONS = new Set(["idle", "think", "thinking", "sad"]);

export const HOVER_DWELL_MS = 1400;
export const HOVER_REACTION_COOLDOWN_MS = 5200;
export const HOVER_REACTION_DURATION_MS = 640;
export const HOVER_REACTION_RADIUS = 0.58;
export const AMBIENT_GESTURE_INTERVAL_MS = 7200;
export const DEFAULT_AMBIENT_GESTURES = Object.freeze([
  Object.freeze({ x: 0.28, y: -0.24, durationMs: 860 }),
  Object.freeze({ x: -0.22, y: 0.08, durationMs: 920 }),
  Object.freeze({ x: 0.12, y: -0.34, durationMs: 820 })
]);

export function canRunPassiveBehavior(command = {}) {
  return PASSIVE_MOTIONS.has(command.motion || "");
}

export function updateHoverDwellSchedule({
  now,
  pointer = { x: 0, y: 0 },
  command = {},
  hasPointerInput = false,
  activeReaction = false,
  hoverDwellStartedAt = 0,
  nextHoverReactionAt = 0,
  dwellMs = HOVER_DWELL_MS,
  cooldownMs = HOVER_REACTION_COOLDOWN_MS,
  durationMs = HOVER_REACTION_DURATION_MS,
  radius = HOVER_REACTION_RADIUS
} = {}) {
  if (!hasPointerInput || !canRunPassiveBehavior(command)) {
    return {
      hoverDwellStartedAt: 0,
      nextHoverReactionAt,
      reaction: null
    };
  }

  if (now < nextHoverReactionAt) {
    return {
      hoverDwellStartedAt,
      nextHoverReactionAt,
      reaction: null
    };
  }

  if (!isPointerNearAvatarCenter(pointer, radius)) {
    return {
      hoverDwellStartedAt: 0,
      nextHoverReactionAt,
      reaction: null
    };
  }

  if (activeReaction) {
    return {
      hoverDwellStartedAt,
      nextHoverReactionAt,
      reaction: null
    };
  }

  if (!hoverDwellStartedAt) {
    return {
      hoverDwellStartedAt: now,
      nextHoverReactionAt,
      reaction: null
    };
  }

  if (now - hoverDwellStartedAt < dwellMs) {
    return {
      hoverDwellStartedAt,
      nextHoverReactionAt,
      reaction: null
    };
  }

  return {
    hoverDwellStartedAt: 0,
    nextHoverReactionAt: now + cooldownMs,
    reaction: {
      startedAt: now,
      durationMs,
      x: clampUnit(Number(pointer.x ?? 0) * 0.45),
      y: clampUnit(Number(pointer.y ?? 0) * 0.35 - 0.12)
    }
  };
}

export function updateAmbientGestureSchedule({
  now,
  command = {},
  activeReaction = false,
  nextAmbientGestureAt = 0,
  ambientGestureIndex = 0,
  intervalMs = AMBIENT_GESTURE_INTERVAL_MS,
  gestures = DEFAULT_AMBIENT_GESTURES
} = {}) {
  const safeIntervalMs = readPositiveNumber(intervalMs, AMBIENT_GESTURE_INTERVAL_MS);
  if (!canRunPassiveBehavior(command)) {
    return {
      nextAmbientGestureAt: now + safeIntervalMs,
      ambientGestureIndex,
      reaction: null,
      eventDetail: null
    };
  }

  if (activeReaction || now < nextAmbientGestureAt) {
    return {
      nextAmbientGestureAt,
      ambientGestureIndex,
      reaction: null,
      eventDetail: null
    };
  }

  const safeGestures = Array.isArray(gestures) && gestures.length
    ? gestures
    : DEFAULT_AMBIENT_GESTURES;
  const gestureIndex = ambientGestureIndex % safeGestures.length;
  const gesture = safeGestures[gestureIndex] || DEFAULT_AMBIENT_GESTURES[0];
  return {
    nextAmbientGestureAt: now + safeIntervalMs,
    ambientGestureIndex: ambientGestureIndex + 1,
    reaction: {
      startedAt: now,
      durationMs: readPositiveNumber(gesture.durationMs, 860),
      x: clampUnit(Number(gesture.x ?? 0)),
      y: clampUnit(Number(gesture.y ?? 0))
    },
    eventDetail: {
      index: ambientGestureIndex,
      x: clampUnit(Number(gesture.x ?? 0)),
      y: clampUnit(Number(gesture.y ?? 0))
    }
  };
}

export function updatePassiveBehaviorSchedule({
  now,
  pointer = { x: 0, y: 0 },
  command = {},
  hasPointerInput = false,
  activeReaction = false,
  hoverDwellStartedAt = 0,
  nextHoverReactionAt = 0,
  nextAmbientGestureAt = 0,
  ambientGestureIndex = 0,
  ambientIntervalMs = AMBIENT_GESTURE_INTERVAL_MS
} = {}) {
  const hover = updateHoverDwellSchedule({
    now,
    pointer,
    command,
    hasPointerInput,
    activeReaction,
    hoverDwellStartedAt,
    nextHoverReactionAt
  });

  if (hover.reaction) {
    return {
      hoverDwellStartedAt: hover.hoverDwellStartedAt,
      nextHoverReactionAt: hover.nextHoverReactionAt,
      nextAmbientGestureAt,
      ambientGestureIndex,
      reaction: hover.reaction,
      eventType: "pointer.hover-dwell",
      eventDetail: {
        x: hover.reaction.x,
        y: hover.reaction.y
      }
    };
  }

  const ambient = updateAmbientGestureSchedule({
    now,
    command,
    activeReaction,
    nextAmbientGestureAt,
    ambientGestureIndex,
    intervalMs: ambientIntervalMs
  });

  return {
    hoverDwellStartedAt: hover.hoverDwellStartedAt,
    nextHoverReactionAt: hover.nextHoverReactionAt,
    nextAmbientGestureAt: ambient.nextAmbientGestureAt,
    ambientGestureIndex: ambient.ambientGestureIndex,
    reaction: ambient.reaction,
    eventType: ambient.reaction ? "ambient.gesture" : "",
    eventDetail: ambient.eventDetail
  };
}

export function isPointerNearAvatarCenter(pointer = { x: 0, y: 0 }, radius = HOVER_REACTION_RADIUS) {
  const x = Number(pointer.x ?? 0);
  const y = Number(pointer.y ?? 0);
  if (!Number.isFinite(x) || !Number.isFinite(y)) {
    return false;
  }
  return Math.hypot(x, y) <= radius;
}

function clampUnit(value) {
  if (!Number.isFinite(value)) {
    return 0;
  }
  return Math.max(-1, Math.min(1, value));
}

function readPositiveNumber(value, fallback) {
  const number = Number(value);
  return Number.isFinite(number) && number > 0 ? number : fallback;
}
