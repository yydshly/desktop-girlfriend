export function resolveEmotionalSurfaceState({
  emotionState = {},
  speakingState = {},
  now = 0
} = {}) {
  const visualizer = resolveVoiceVisualizerState({ speakingState, now });
  const visualIntent = resolveSurfaceIntent(emotionState, speakingState, visualizer);
  return {
    visualIntent,
    visualizer
  };
}

export function resolveVoiceVisualizerState({ speakingState = {}, now = 0 } = {}) {
  const active = Boolean(speakingState.active);
  const pending = Boolean(speakingState.pending);
  const closing = Boolean(speakingState.closing);
  const visible = active || pending || closing;
  const state = active ? "playing" : (pending ? "pending" : (closing ? "fading" : "hidden"));
  const intensity = active
    ? clamp01((speakingState.mouth ?? 0) * 1.2 + 0.16)
    : (pending ? 0.18 : 0);
  return {
    visible,
    active,
    state,
    intensity: roundToThree(intensity),
    bars: visible ? buildBars(now, intensity, state) : []
  };
}

function resolveSurfaceIntent(emotionState = {}, speakingState = {}, visualizer = {}) {
  if (speakingState.pending) {
    return "preparing";
  }
  if (speakingState.active || visualizer.state === "playing") {
    return "speaking";
  }
  if (speakingState.fallbackExpired || speakingState.closing) {
    return speakingState.ttsState === "error" ? "error" : resolvePostSpeakingIntent(emotionState);
  }
  return resolveVisualIntent(emotionState);
}

function resolvePostSpeakingIntent(emotionState = {}) {
  const state = String(emotionState.state || "").trim().toLowerCase();
  if (state === "error") {
    return "error";
  }
  return "idle";
}

function resolveVisualIntent(emotionState = {}) {
  const state = String(emotionState.state || emotionState.activity || emotionState.emotion || "idle")
    .trim()
    .toLowerCase();
  if (state === "listen") {
    return "listening";
  }
  if (state === "think") {
    return "thinking";
  }
  if (state === "reply" || state === "speak") {
    return "speaking";
  }
  if (["listening", "thinking", "speaking", "comfort", "happy", "error", "idle", "sad"].includes(state)) {
    return state;
  }
  return "idle";
}

function buildBars(now = 0, intensity = 0, state = "playing") {
  return Array.from({ length: 5 }, (_, index) => {
    const phase = Number(now) / 120 + index * 0.82;
    const wave = 0.5 + Math.sin(phase) * 0.5;
    const floor = state === "fading" ? 0 : 0.12;
    return roundToThree(Math.max(floor, Math.min(1, 0.16 + intensity * (0.38 + wave * 0.62))));
  });
}

function clamp01(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return 0;
  }
  return Math.min(1, Math.max(0, number));
}

function roundToThree(value) {
  return Number(value.toFixed(3));
}
