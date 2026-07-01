import { planBehaviorFromEmotionState } from "./behavior-planner.js";
import { normalizeEmotionState } from "./emotion-state.js";
import { adaptBehaviorToModelCommands } from "./model-adapter.js";
import { resolveAttentionState } from "./attention-system.js";
import { resolveSpeakingState } from "./speaking-driver.js";

const DEFAULT_STEP_DURATION_MS = 3200;
const DEFAULT_EXPERIMENT_STATES = Object.freeze([
  "idle",
  "listening",
  "thinking",
  "speaking",
  "happy",
  "comfort",
  "idle"
]);

export function getDefaultModelExperimentStates() {
  return [...DEFAULT_EXPERIMENT_STATES];
}

export function buildModelExperimentTimeline(profile = {}, options = {}) {
  const states = Array.isArray(options.states) && options.states.length
    ? options.states
    : DEFAULT_EXPERIMENT_STATES;
  const durationMs = readDurationMs(options.durationMs);

  return states.map((state, index) => {
    const emotionState = normalizeEmotionState({ state });
    const attentionState = resolveAttentionState({
      emotionState,
      pointerState: options.pointerState || {}
    });
    const speakingState = resolveSpeakingState({
      emotionState,
      now: stepNow(options.now, index, durationMs)
    });
    const behavior = planBehaviorFromEmotionState(emotionState, attentionState, speakingState);
    return {
      index,
      state: emotionState.state,
      atMs: index * durationMs,
      durationMs,
      emotionState,
      attentionState,
      speakingState,
      behavior,
      modelCommands: adaptBehaviorToModelCommands(behavior, profile)
    };
  });
}

function stepNow(now, index, durationMs) {
  const number = Number(now);
  if (Number.isFinite(number)) {
    return number + index * durationMs;
  }
  return index * durationMs;
}

function readDurationMs(value) {
  const number = Number(value ?? DEFAULT_STEP_DURATION_MS);
  if (!Number.isFinite(number) || number <= 0) {
    return DEFAULT_STEP_DURATION_MS;
  }
  return Math.floor(number);
}
