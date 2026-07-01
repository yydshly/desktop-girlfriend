export const CANONICAL_AVATAR_STATES = Object.freeze([
  "idle",
  "listening",
  "thinking",
  "speaking",
  "happy",
  "sad",
  "comfort",
  "error"
]);

const STATE_ALIASES = Object.freeze({
  listen: "listening",
  think: "thinking",
  reply: "speaking",
  speak: "speaking",
  low: "sad",
  upset: "sad"
});

const CANONICAL_STATE_SET = new Set(CANONICAL_AVATAR_STATES);

export function normalizeAvatarState(state, fallback = "idle") {
  const value = String(state || "").trim();
  const normalized = STATE_ALIASES[value] || value;
  if (CANONICAL_STATE_SET.has(normalized)) {
    return normalized;
  }
  return fallback;
}

export function isCanonicalAvatarState(state) {
  return CANONICAL_STATE_SET.has(state);
}
