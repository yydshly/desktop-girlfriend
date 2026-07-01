import { normalizeEmotionState } from "./emotion-state.js";
import { resolveAttentionState } from "./attention-system.js";
import { resolveSpeakingState } from "./speaking-driver.js";
import { planBehaviorFromEmotionState } from "./behavior-planner.js";
import { adaptBehaviorToModelCommands } from "./model-adapter.js";

export function buildCharacterRuntimeState({
  previousState = {},
  mappedState = {},
  emotionState = null,
  pointerState = {},
  profile = {},
  now = 0,
  updatedAt = new Date().toISOString()
} = {}) {
  const nextEmotionState = emotionState || normalizeEmotionState(mappedState);
  const speakingState = resolveSpeakingState({
    emotionState: nextEmotionState,
    now
  });
  const attentionState = resolveAttentionState({
    emotionState: nextEmotionState,
    pointerState,
    speakingState
  });
  const behavior = planBehaviorFromEmotionState(nextEmotionState, attentionState, speakingState);
  const modelCommands = adaptBehaviorToModelCommands(behavior, profile);
  return {
    ...previousState,
    ...mappedState,
    emotionState: nextEmotionState,
    attentionState,
    speakingState,
    behavior,
    modelCommands,
    updatedAt
  };
}
