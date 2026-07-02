import {
  normalizeCharacterAction,
  normalizeCharacterExpression
} from "./character-contract.js";

const EXPRESSION_BY_EMOTION = Object.freeze({
  neutral: "neutral",
  happy: "happy",
  sad: "sad",
  thinking: "thinking",
  soft: "soft",
  engaged: "engaged"
});

const IDLE_BEHAVIOR = Object.freeze({
  action: "idle",
  expression: "neutral",
  intensity: 0.25,
  gaze: "cursor",
  mouth: 0
});

const RETURN_TO_IDLE_MS = 4200;

export function planBehaviorFromEmotionState(
  emotionState = {},
  attentionState = null,
  speakingState = null
) {
  const expression = normalizeCharacterExpression(
    EXPRESSION_BY_EMOTION[emotionState.emotion] || emotionState.emotion || "neutral"
  );
  const gaze = resolveBehaviorGaze(emotionState, attentionState);
  return {
    action: normalizeCharacterAction(emotionState.activity || "idle"),
    expression,
    intensity: clamp01(emotionState.intensity ?? IDLE_BEHAVIOR.intensity),
    gaze,
    mouth: clamp01(speakingState?.mouth ?? emotionState.mouth ?? IDLE_BEHAVIOR.mouth),
    mouthForm: clampSignedUnit(speakingState?.mouthForm ?? emotionState.mouthForm ?? 0),
    ...(speakingState ? { speaking: speakingState } : {}),
    ...(attentionState ? { attention: attentionState } : {})
  };
}

export function planBehaviorTimeline(emotionState = {}) {
  const behavior = planBehaviorFromEmotionState(emotionState);
  const timeline = [
    {
      atMs: 0,
      behavior
    }
  ];
  if (behavior.action !== "idle") {
    timeline.push({
      atMs: RETURN_TO_IDLE_MS,
      behavior: { ...IDLE_BEHAVIOR }
    });
  }
  return timeline;
}

function clamp01(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return 0;
  }
  return Math.min(1, Math.max(0, number));
}

function clampSignedUnit(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return 0;
  }
  return Math.min(1, Math.max(-1, number));
}

function resolveBehaviorGaze(emotionState = {}, attentionState = null) {
  if (typeof attentionState?.gaze === "string" && attentionState.gaze.trim()) {
    return attentionState.gaze.trim();
  }
  if (typeof emotionState.gaze === "string" && emotionState.gaze.trim()) {
    return emotionState.gaze.trim();
  }
  return IDLE_BEHAVIOR.gaze;
}
