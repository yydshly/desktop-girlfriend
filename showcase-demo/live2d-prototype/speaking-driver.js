export function resolveSpeakingState({
  emotionState = {},
  now = 0
} = {}) {
  const ttsState = normalizeTtsState(emotionState.turn?.ttsState);
  const fallbackExpired = isDialogueFallbackExpired(emotionState.turn, ttsState, now);
  const effectiveTtsState = fallbackExpired ? "ended" : ttsState;
  const activity = String(emotionState.activity || "").trim();
  const state = String(emotionState.state || "").trim();
  const hasTtsPresence = effectiveTtsState !== "none";
  const pending = effectiveTtsState === "started";
  const closing = effectiveTtsState === "ended" || effectiveTtsState === "interrupted" || effectiveTtsState === "error";
  const activeTts = effectiveTtsState === "playing" || effectiveTtsState === "speaking";
  const endedTts = closing;
  const active = activeTts || (!hasTtsPresence && (activity === "speak" || state === "speaking"));
  const source = hasTtsPresence ? "tts" : (active ? "state" : "idle");
  const baseMouth = active ? clamp01(emotionState.mouth ?? 0.65) : clamp01(emotionState.mouth ?? 0);
  const mouth = active ? calculateMouthEnvelope(baseMouth, now) : (pending ? 0.04 : 0);
  return {
    active,
    pending,
    closing,
    fallbackExpired,
    source,
    mouth,
    baseMouth,
    rhythm: active ? "simulated" : (pending ? "pending" : "none"),
    ttsState: effectiveTtsState,
    ttsSource: readTtsSource(emotionState.turn?.source),
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
  if (state === "error" || state === "failed" || state === "failure") {
    return "error";
  }
  return "none";
}

function readTtsSource(value) {
  const source = String(value || "").trim();
  return source || "unknown";
}

function isDialogueFallbackExpired(turn = {}, ttsState = "none", now = 0) {
  if (ttsState !== "speaking") {
    return false;
  }
  if (String(turn.source || "").trim() === "tts_controller") {
    return false;
  }
  const receivedAt = Number(turn.receivedAt);
  if (!Number.isFinite(receivedAt)) {
    return false;
  }
  const timeoutMs = Number.isFinite(Number(turn.fallbackTimeoutMs))
    ? Number(turn.fallbackTimeoutMs)
    : 5200;
  return Number(now) - receivedAt >= timeoutMs;
}
