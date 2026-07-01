import { buildCharacterRuntimeState } from "./character-runtime.js";
import { resolveLive2DParameterAliases } from "./live2d-parameter-mapper.js";

const DEFAULT_STEP_DURATION_MS = 3200;
const RUNTIME_VALIDATION_SEQUENCE_STATES = Object.freeze([
  "idle",
  "listen",
  "think",
  "speak",
  "happy",
  "comfort",
  "idle"
]);

export function getDefaultModelExperimentStates() {
  return getRuntimeValidationSequenceStates();
}

export function getRuntimeValidationSequenceStates() {
  return [...RUNTIME_VALIDATION_SEQUENCE_STATES];
}

export function buildModelExperimentTimeline(profile = {}, options = {}) {
  const states = Array.isArray(options.states) && options.states.length
    ? options.states
    : RUNTIME_VALIDATION_SEQUENCE_STATES;
  const durationMs = readDurationMs(options.durationMs);

  return states.map((state, index) => {
    const resolvedParameterAliases = resolveLive2DParameterAliases(profile.parameters || {});
    const runtimeState = buildCharacterRuntimeState({
      mappedState: {
        state,
        source: "runtime-validation",
        validationStep: index
      },
      pointerState: options.pointerState || {},
      profile,
      now: stepNow(options.now, index, durationMs),
      updatedAt: options.updatedAt || "runtime-validation"
    });
    return {
      index,
      semanticState: String(state),
      state: runtimeState.emotionState.state,
      atMs: index * durationMs,
      durationMs,
      emotionState: runtimeState.emotionState,
      attentionState: runtimeState.attentionState,
      speakingState: runtimeState.speakingState,
      behavior: runtimeState.behavior,
      modelCommands: runtimeState.modelCommands,
      activeLive2D: normalizeActiveLive2D(options.rendererStatus),
      resolvedParameters: resolvedParameterAliases.aliases,
      validation: validateRuntimeStep(
        runtimeState,
        profile,
        options.modelCapabilities,
        resolvedParameterAliases.warnings
      )
    };
  });
}

function validateRuntimeStep(runtimeState = {}, profile = {}, modelCapabilities = null, parameterWarnings = []) {
  const warnings = [...parameterWarnings];
  const blockers = [];
  const actions = profile?.mappings?.actions || {};
  const expressions = profile?.mappings?.expressions || {};
  const action = runtimeState.behavior?.action || "idle";
  const expression = runtimeState.behavior?.expression || "neutral";
  const motion = runtimeState.modelCommands?.motion || {};
  const adapterExpression = runtimeState.modelCommands?.expression || {};

  if (!actions[action]) {
    warnings.push(`action ${action} is unmapped`);
  }
  if (!expressions[expression]) {
    warnings.push(`expression ${expression} is unmapped`);
  }

  if (modelCapabilities?.motionGroupCounts && motion.group) {
    const count = Number(modelCapabilities.motionGroupCounts[motion.group] ?? 0);
    if (!count || Number(motion.index) >= count) {
      blockers.push(`motion ${motion.group}[${motion.index}] unavailable`);
    }
  }
  if (Array.isArray(modelCapabilities?.expressionNames) && adapterExpression.name) {
    if (!modelCapabilities.expressionNames.includes(adapterExpression.name)) {
      blockers.push(`expression ${adapterExpression.name} unavailable`);
    }
  }

  return {
    layer: blockers.length || warnings.length ? "profile/model" : "ok",
    blockers,
    warnings
  };
}

function normalizeActiveLive2D(rendererStatus = null) {
  return {
    motion: rendererStatus?.activeMotion?.group
      ? {
        group: rendererStatus.activeMotion.group,
        index: rendererStatus.activeMotion.index,
        source: rendererStatus.activeMotion.source || ""
      }
      : null,
    expression: rendererStatus?.activeExpression || ""
  };
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
