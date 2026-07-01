import { planBehaviorFromEmotionState } from "./behavior-planner.js";
import { normalizeEmotionState } from "./emotion-state.js";
import { adaptBehaviorToModelCommands } from "./model-adapter.js";
import { resolveAttentionState } from "./attention-system.js";

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
    const behavior = planBehaviorFromEmotionState(emotionState, attentionState);
    return {
      index,
      state: emotionState.state,
      atMs: index * durationMs,
      durationMs,
      emotionState,
      attentionState,
      behavior,
      modelCommands: adaptBehaviorToModelCommands(behavior, profile)
    };
  });
}

function readDurationMs(value) {
  const number = Number(value ?? DEFAULT_STEP_DURATION_MS);
  if (!Number.isFinite(number) || number <= 0) {
    return DEFAULT_STEP_DURATION_MS;
  }
  return Math.floor(number);
}
