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

const STATE_BUBBLES = {
  think: { text: "让我想想...", tone: "thinking", ttlMs: 3200 },
  speak: { text: "我在说。", tone: "reply", ttlMs: 3600 },
  sad: { text: "好像出了点问题。", tone: "sad", ttlMs: 4200 },
  comfort: { text: "我在这里。", tone: "comfort", ttlMs: 3800 }
};

export function mapAvatarState(payload = {}) {
  const preset = STATE_PRESETS[payload.state] || STATE_PRESETS.idle;
  return {
    ...preset,
    ...payload,
    bubble: STATE_BUBBLES[payload.state],
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
    bubble: {
      text: compactBubbleText(payload.response_text || ""),
      tone: "reply",
      ttlMs: 5200
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

function compactBubbleText(text, maxLength = 42) {
  const compact = String(text || "").trim().replace(/\s+/g, " ");
  if (compact.length <= maxLength) {
    return compact;
  }
  return `${compact.slice(0, maxLength - 1)}…`;
}
