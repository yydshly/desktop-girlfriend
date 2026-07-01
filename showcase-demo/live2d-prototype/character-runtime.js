import { normalizeEmotionState } from "./emotion-state.js";
import { planBehaviorFromEmotionState } from "./behavior-planner.js";
import { adaptBehaviorToModelCommands } from "./model-adapter.js";

export function buildCharacterRuntimeState({
  previousState = {},
  mappedState = {},
  emotionState = null,
  profile = {},
  updatedAt = new Date().toISOString()
} = {}) {
  const nextEmotionState = emotionState || normalizeEmotionState(mappedState);
  const behavior = planBehaviorFromEmotionState(nextEmotionState);
  const modelCommands = adaptBehaviorToModelCommands(behavior, profile);
  return {
    ...previousState,
    ...mappedState,
    emotionState: nextEmotionState,
    behavior,
    modelCommands,
    updatedAt
  };
}
