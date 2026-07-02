export function resolveSpeakingState({
  emotionState = {},
  now = 0
} = {}) {
  const ttsState = normalizeTtsState(emotionState.turn?.ttsState);
  const activity = String(emotionState.activity || "").trim();
  const state = String(emotionState.state || "").trim();
  const hasTtsPresence = ttsState !== "none";
  const activeTts = ttsState === "started" || ttsState === "playing" || ttsState === "speaking";
  const endedTts = ttsState === "ended" || ttsState === "interrupted";
  const active = activeTts || (!endedTts && (activity === "speak" || state === "speaking"));
  const source = hasTtsPresence ? "tts" : (active ? "state" : "idle");
  const baseMouth = active ? clamp01(emotionState.mouth ?? 0.65) : clamp01(emotionState.mouth ?? 0);
  const mouth = active ? calculateMouthEnvelope(baseMouth, now) : 0;
  return {
    active,
    source,
    mouth,
    baseMouth,
    rhythm: active ? "simulated" : "none",
    ttsState,
    mouthForm: active ? calculateMouthForm(now, mouth) : 0
  };
}

export function calculateMouthEnvelope(baseMouth = 0.65, now = 0) {
  const base = clamp01(baseMouth);
  const pulse = 0.82 + Math.sin(Number(now) / 90) * 0.12 + Math.sin(Number(now) / 43) * 0.06;
  return roundToThree(Math.max(0.12, Math.min(1, base * pulse)));
}

export function calculateMouthForm(now = 0, mouth = 0) {
  const wave = Math.sin(Number(now) / 130);
  const openness = clamp01(mouth);
  return roundToThree(Math.max(-1, Math.min(1, wave * 0.28 + openness * 0.18)));
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

function normalizeTtsState(value) {
  const state = String(value || "").trim().toLowerCase();
  if (state === "started" || state === "start") {
    return "started";
  }
  if (state === "playing" || state === "speaking") {
    return state;
  }
  if (state === "ended" || state === "end" || state === "done" || state === "stopped") {
    return "ended";
  }
  if (state === "interrupted" || state === "interrupt" || state === "cancelled" || state === "canceled") {
    return "interrupted";
  }
  return "none";
}
