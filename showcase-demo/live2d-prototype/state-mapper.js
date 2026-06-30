const STATE_PRESETS = {
  idle: { emotion: "neutral", mouth: 0, gaze: "cursor", motion: "idle", intensity: 0.25 },
  happy: { emotion: "happy", mouth: 0.28, gaze: "cursor", motion: "happy", intensity: 0.72 },
  think: { emotion: "thinking", mouth: 0.05, gaze: "down-left", motion: "think", intensity: 0.48 },
  sad: { emotion: "sad", mouth: 0.08, gaze: "down", motion: "sad", intensity: 0.56 },
  comfort: { emotion: "soft", mouth: 0.18, gaze: "cursor", motion: "comfort", intensity: 0.68 },
  speak: { emotion: "engaged", mouth: 0.65, gaze: "cursor", motion: "reply", intensity: 0.76 }
};

const SEQUENCE_TO_STATE = {
  greet: "happy",
  listen: "think",
  reply: "speak",
  comfort: "comfort"
};

export function mapAvatarState(payload = {}) {
  const preset = STATE_PRESETS[payload.state] || STATE_PRESETS.idle;
  return {
    ...preset,
    ...payload,
    source: "avatar.state"
  };
}

export function mapAvatarSequence(payload = {}) {
  const stateName = SEQUENCE_TO_STATE[payload.name] || "idle";
  return {
    ...STATE_PRESETS[stateName],
    sequence: payload.name || "idle",
    source: "avatar.sequence"
  };
}

export function mapDialogueTurn(payload = {}) {
  const intent = payload.intent || "reply";
  const stateName = SEQUENCE_TO_STATE[intent] || (intent === "idle" ? "idle" : "speak");
  return {
    ...STATE_PRESETS[stateName],
    turn: {
      turnId: payload.turn_id || "",
      userText: payload.user_text || "",
      responseText: payload.response_text || "",
      ttsState: payload.tts_state || "none"
    },
    source: "dialogue.turn"
  };
}

export function mapBridgeMessage(message = {}) {
  if (message.type === "avatar.state") {
    return mapAvatarState(message.payload);
  }
  if (message.type === "avatar.sequence") {
    return mapAvatarSequence(message.payload);
  }
  if (message.type === "dialogue.turn") {
    return mapDialogueTurn(message.payload);
  }
  return {
    ...STATE_PRESETS.idle,
    source: message.type || "unknown"
  };
}
