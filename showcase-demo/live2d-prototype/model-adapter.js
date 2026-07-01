import { planBehaviorFromEmotionState } from "./behavior-planner.js";
import {
  normalizeCharacterAction,
  normalizeCharacterExpression
} from "./character-contract.js";

const DEFAULT_MOTION = Object.freeze({
  group: "Idle",
  index: 0,
  action: "idle"
});

export function adaptEmotionStateToModelCommands(emotionState = {}, profile = {}) {
  return adaptBehaviorToModelCommands(
    planBehaviorFromEmotionState(emotionState),
    profile
  );
}

export function adaptBehaviorToModelCommands(behavior = {}, profile = {}) {
  const action = normalizeCharacterAction(behavior.action || "idle");
  const expression = normalizeCharacterExpression(behavior.expression || "neutral");
  return {
    motion: resolveMotion(action, profile),
    expression: resolveExpression(expression, profile),
    parameters: {
      gaze: typeof behavior.gaze === "string" && behavior.gaze.trim()
        ? behavior.gaze.trim()
        : "cursor",
      mouth: clamp01(behavior.mouth ?? 0),
      intensity: clamp01(behavior.intensity ?? 0.25),
      speaking: normalizeSpeakingParameter(behavior.speaking)
    }
  };
}

function resolveMotion(action, profile) {
  const mappings = profile?.mappings?.actions || {};
  const binding = mappings[action] || mappings.idle;
  if (!binding) {
    return { ...DEFAULT_MOTION };
  }
  const group = String(binding.group || "").trim();
  const index = Math.max(0, Math.floor(Number(binding.index ?? 0)));
  if (!group) {
    return { ...DEFAULT_MOTION };
  }
  return {
    group,
    index,
    action: mappings[action] ? action : "idle"
  };
}

function resolveExpression(expression, profile) {
  const mappings = profile?.mappings?.expressions || {};
  const name = mappings[expression];
  if (typeof name !== "string" || !name.trim()) {
    return {
      name: "",
      semantic: expression
    };
  }
  return {
    name: name.trim(),
    semantic: expression
  };
}

function clamp01(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return 0;
  }
  return Math.min(1, Math.max(0, number));
}

function normalizeSpeakingParameter(speaking = null) {
  return {
    active: Boolean(speaking?.active),
    source: typeof speaking?.source === "string" && speaking.source.trim()
      ? speaking.source.trim()
      : "idle",
    rhythm: typeof speaking?.rhythm === "string" && speaking.rhythm.trim()
      ? speaking.rhythm.trim()
      : "none"
  };
}
