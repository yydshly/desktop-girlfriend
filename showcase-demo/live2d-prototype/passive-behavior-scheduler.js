const PASSIVE_MOTIONS = new Set(["idle", "think", "thinking", "sad"]);

export const HOVER_DWELL_MS = 1400;
export const HOVER_REACTION_COOLDOWN_MS = 5200;
export const HOVER_REACTION_DURATION_MS = 640;
export const HOVER_REACTION_RADIUS = 0.58;

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
