import { normalizeAvatarState } from "./avatar-protocol.js";
import { normalizeCharacterAction } from "./character-contract.js";

const EMOTION_PRESETS = Object.freeze({
  idle: {
    state: "idle",
    emotion: "neutral",
    intensity: 0.25,
    activity: "idle",
    gaze: "cursor",
    mouth: 0
  },
  listening: {
    state: "listening",
    emotion: "thinking",
    intensity: 0.42,
    activity: "listen",
    gaze: "cursor",
    mouth: 0.03
  },
  thinking: {
    state: "thinking",
    emotion: "thinking",
    intensity: 0.48,
    activity: "think",
    gaze: "down-left",
    mouth: 0.05
  },
  speaking: {
    state: "speaking",
    emotion: "engaged",
    intensity: 0.76,
    activity: "speak",
    gaze: "cursor",
    mouth: 0.65
  },
  happy: {
    state: "happy",
    emotion: "happy",
    intensity: 0.72,
    activity: "happy",
    gaze: "cursor",
    mouth: 0.28
  },
  sad: {
    state: "sad",
    emotion: "sad",
    intensity: 0.56,
    activity: "sad",
    gaze: "down",
    mouth: 0.08
  },
  comfort: {
    state: "comfort",
    emotion: "soft",
    intensity: 0.68,
    activity: "comfort",
    gaze: "cursor",
    mouth: 0.18
  },
  error: {
    state: "error",
    emotion: "sad",
    intensity: 0.58,
    activity: "sad",
    gaze: "down",
    mouth: 0.08
  }
});

const SEQUENCE_TO_STATE = Object.freeze({
  greet: "happy",
  listen: "listening",
  reply: "speaking",
  comfort: "comfort"
});

const SEQUENCE_TO_ACTIVITY = Object.freeze({
  greet: "greet",
  listen: "listen",
  reply: "speak",
  comfort: "comfort"
});

export function normalizeEmotionState(state = {}) {
  const stateName = normalizeAvatarState(state.state);
  const preset = EMOTION_PRESETS[stateName] || EMOTION_PRESETS.idle;
  return {
    state: stateName,
    emotion: typeof state.emotion === "string" && state.emotion.trim()
      ? state.emotion.trim()
      : preset.emotion,
    intensity: clamp01(state.intensity ?? preset.intensity),
    activity: normalizeCharacterAction(state.activity || preset.activity),
    gaze: typeof state.gaze === "string" && state.gaze.trim()
      ? state.gaze.trim()
      : preset.gaze,
    mouth: clamp01(state.mouth ?? preset.mouth)
  };
}

export function mapAvatarStateToEmotionState(payload = {}) {
  return normalizeEmotionState({
    ...payload,
    state: normalizeAvatarState(payload.state)
  });
}

export function mapAvatarSequenceToEmotionState(payload = {}) {
  const sequence = String(payload.name || "idle");
  const stateName = SEQUENCE_TO_STATE[sequence] || "idle";
  return normalizeEmotionState({
    ...EMOTION_PRESETS[stateName],
    activity: SEQUENCE_TO_ACTIVITY[sequence] || "idle"
  });
}

export function mapDialogueTurnToEmotionState(payload = {}) {
  const intent = payload.intent || "reply";
  const stateName = SEQUENCE_TO_STATE[intent] || normalizeAvatarState(intent, "speaking");
  const ttsState = payload.tts_state || "none";
  return {
    ...normalizeEmotionState({
      ...EMOTION_PRESETS[stateName],
      activity: ttsState === "speaking" ? "speak" : EMOTION_PRESETS[stateName].activity,
      mouth: ttsState === "speaking" ? EMOTION_PRESETS.speaking.mouth : EMOTION_PRESETS[stateName].mouth
    }),
    turn: {
      turnId: payload.turn_id || "",
      userText: payload.user_text || "",
      responseText: payload.response_text || "",
      ttsState
    }
  };
}

export function mapTtsPlaybackToEmotionState(payload = {}) {
  const ttsState = normalizeTtsState(payload.tts_state);
  const stateName = stateForTtsPlayback(ttsState);
  return {
    ...normalizeEmotionState({
      ...EMOTION_PRESETS[stateName],
      activity: stateName === "speaking" ? "speak" : EMOTION_PRESETS[stateName].activity,
      mouth: stateName === "speaking" ? EMOTION_PRESETS.speaking.mouth : EMOTION_PRESETS[stateName].mouth
    }),
    turn: {
      turnId: payload.request_id || payload.turn_id || "",
      source: payload.source || "tts",
      ttsState
    }
  };
}

export function mapBridgeMessageToEmotionState(message = {}) {
  if (message.type === "avatar.state") {
    return {
      ...mapAvatarStateToEmotionState(message.payload),
      source: "avatar.state"
    };
  }
  if (message.type === "avatar.sequence") {
    return {
      ...mapAvatarSequenceToEmotionState(message.payload),
      source: "avatar.sequence"
    };
  }
  if (message.type === "dialogue.turn") {
    return {
      ...mapDialogueTurnToEmotionState(message.payload),
      source: "dialogue.turn"
    };
  }
  if (message.type === "tts.playback") {
    return {
      ...mapTtsPlaybackToEmotionState(message.payload),
      source: "tts.playback"
    };
  }
  return {
    ...normalizeEmotionState(),
    source: message.type || "unknown"
  };
}

function stateForTtsPlayback(ttsState) {
  if (ttsState === "started" || ttsState === "playing" || ttsState === "speaking") {
    return "speaking";
  }
  if (ttsState === "error") {
    return "error";
  }
  return "idle";
}

function normalizeTtsState(value) {
  const state = String(value || "").trim().toLowerCase();
  if (state === "start") {
    return "started";
  }
  if (state === "started" || state === "playing" || state === "speaking") {
    return state;
  }
  if (state === "end" || state === "done" || state === "stopped") {
    return "ended";
  }
  if (state === "ended" || state === "interrupted" || state === "error") {
    return state;
  }
  return "none";
}

function clamp01(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return 0;
  }
  return Math.min(1, Math.max(0, number));
}
