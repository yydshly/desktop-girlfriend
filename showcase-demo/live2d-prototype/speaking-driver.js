export function resolveSpeakingState({
  emotionState = {},
  now = 0
} = {}) {
  const ttsState = String(emotionState.turn?.ttsState || "").trim();
  const activity = String(emotionState.activity || "").trim();
  const state = String(emotionState.state || "").trim();
  const active = ttsState === "speaking" || activity === "speak" || state === "speaking";
  const source = active
    ? (ttsState === "speaking" ? "tts" : "state")
    : "idle";
  const baseMouth = active ? clamp01(emotionState.mouth ?? 0.65) : clamp01(emotionState.mouth ?? 0);
  return {
    active,
    source,
    mouth: active ? calculateMouthEnvelope(baseMouth, now) : baseMouth,
    baseMouth,
    rhythm: active ? "simulated" : "none"
  };
}

export function calculateMouthEnvelope(baseMouth = 0.65, now = 0) {
  const base = clamp01(baseMouth);
  const pulse = 0.82 + Math.sin(Number(now) / 90) * 0.12 + Math.sin(Number(now) / 43) * 0.06;
  return roundToThree(Math.max(0.12, Math.min(1, base * pulse)));
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
