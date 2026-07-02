export function resolveEmotionalSurfaceState({
  emotionState = {},
  speakingState = {},
  now = 0
} = {}) {
  const visualizer = resolveVoiceVisualizerState({ speakingState, now });
  return {
    visualIntent: visualizer.visible ? "speaking" : resolveVisualIntent(emotionState),
    visualizer
  };
}

export function resolveVoiceVisualizerState({ speakingState = {}, now = 0 } = {}) {
  const visible = Boolean(speakingState.active);
  const intensity = visible ? clamp01((speakingState.mouth ?? 0) * 1.2 + 0.16) : 0;
  return {
    visible,
    state: visible ? "playing" : "hidden",
    intensity: roundToThree(intensity),
    bars: visible ? buildBars(now, intensity) : []
  };
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

function buildBars(now = 0, intensity = 0) {
  return Array.from({ length: 5 }, (_, index) => {
    const phase = Number(now) / 120 + index * 0.82;
    const wave = 0.5 + Math.sin(phase) * 0.5;
    return roundToThree(Math.max(0.12, Math.min(1, 0.16 + intensity * (0.38 + wave * 0.62))));
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
