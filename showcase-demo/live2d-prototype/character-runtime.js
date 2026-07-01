import { normalizeEmotionState } from "./emotion-state.js";
import { resolveAttentionState } from "./attention-system.js";
import { planBehaviorFromEmotionState } from "./behavior-planner.js";
import { adaptBehaviorToModelCommands } from "./model-adapter.js";

export function buildCharacterRuntimeState({
  previousState = {},
  mappedState = {},
  emotionState = null,
  pointerState = {},
  profile = {},
  updatedAt = new Date().toISOString()
} = {}) {
  const nextEmotionState = emotionState || normalizeEmotionState(mappedState);
  const attentionState = resolveAttentionState({
    emotionState: nextEmotionState,
    pointerState
  });
  const behavior = planBehaviorFromEmotionState(nextEmotionState, attentionState);
  const modelCommands = adaptBehaviorToModelCommands(behavior, profile);
  return {
    ...previousState,
    ...mappedState,
    emotionState: nextEmotionState,
    attentionState,
    behavior,
    modelCommands,
    updatedAt
  };
}
