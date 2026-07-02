import { normalizeEmotionState } from "./emotion-state.js";
import { resolveAttentionState } from "./attention-system.js";
import { resolveSpeakingState } from "./speaking-driver.js";
import { planBehaviorFromEmotionState } from "./behavior-planner.js";
import { adaptBehaviorToModelCommands } from "./model-adapter.js";
import { resolveEmotionalSurfaceState } from "./surface-feedback.js";

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
  const surface = resolveEmotionalSurfaceState({
    emotionState: nextEmotionState,
    speakingState,
    now
  });
  return {
    ...previousState,
    ...mappedState,
    emotionState: nextEmotionState,
    attentionState,
    speakingState,
    surface,
    visualIntent: resolveRuntimeVisualIntent(mappedState, surface, speakingState),
    behavior,
    modelCommands,
    updatedAt
  };
}

function resolveRuntimeVisualIntent(mappedState = {}, surface = {}, speakingState = {}) {
  if (speakingState.active || speakingState.pending || speakingState.closing || speakingState.fallbackExpired) {
    return surface.visualIntent;
  }
  return mappedState.visualIntent || surface.visualIntent;
}
