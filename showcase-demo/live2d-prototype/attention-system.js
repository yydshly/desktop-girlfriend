const DEFAULT_ATTENTION = Object.freeze({
  target: "idle-scan",
  source: "idle",
  gaze: "idle-scan",
  bodyFollow: "minimal",
  intensity: 0.22
});

export function resolveAttentionState({
  emotionState = {},
  pointerState = {}
} = {}) {
  if (isPointerActive(pointerState)) {
    return {
      target: "cursor",
      source: "pointer",
      gaze: "cursor",
      bodyFollow: "soft",
      intensity: 0.45
    };
  }

  const state = String(emotionState.state || "").trim();
  const activity = String(emotionState.activity || "").trim();
  const emotion = String(emotionState.emotion || "").trim();

  if (state === "speaking" || activity === "speak") {
    return {
      target: pointerState.available === false ? "user" : "cursor",
      source: "speaking",
      gaze: pointerState.available === false ? "user" : "cursor",
      bodyFollow: "soft",
      intensity: 0.55
    };
  }

  if (state === "thinking" || activity === "think" || emotion === "thinking") {
    return {
      target: "down-left",
      source: "thinking",
      gaze: "down-left",
      bodyFollow: "minimal",
      intensity: 0.34
    };
  }

  if (state === "sad" || state === "error" || emotion === "sad") {
    return {
      target: "away",
      source: "fallback",
      gaze: "down",
      bodyFollow: "none",
      intensity: 0.2
    };
  }

  if (state === "listening" || activity === "listen") {
    return {
      target: pointerState.available === false ? "user" : "cursor",
      source: "fallback",
      gaze: pointerState.available === false ? "user" : "cursor",
      bodyFollow: "soft",
      intensity: 0.36
    };
  }

  return { ...DEFAULT_ATTENTION };
}

function isPointerActive(pointerState = {}) {
  if (pointerState.available === false) {
    return false;
  }
  return Boolean(pointerState.active);
}
