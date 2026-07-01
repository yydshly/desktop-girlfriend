import { sanitizeParameterAliases } from "./model-profile.js";

const PARAMETER_IDS = {
  angleX: "ParamAngleX",
  angleY: "ParamAngleY",
  angleZ: "ParamAngleZ",
  bodyAngleX: "ParamBodyAngleX",
  eyeLOpen: "ParamEyeLOpen",
  eyeROpen: "ParamEyeROpen",
  eyeBallX: "ParamEyeBallX",
  eyeBallY: "ParamEyeBallY",
  mouthOpenY: "ParamMouthOpenY",
  mouthForm: "ParamMouthForm",
  breath: "ParamBreath"
};

const EMOTION_PRESETS = {
  neutral: { mouthForm: 0, eyeOpen: 1, angleZ: 0, expression: "neutral" },
  happy: { mouthForm: 0.75, eyeOpen: 0.88, angleZ: -2, expression: "happy" },
  thinking: { mouthForm: -0.12, eyeOpen: 0.82, angleZ: 3, expression: "thinking" },
  sad: { mouthForm: -0.45, eyeOpen: 0.72, angleZ: 0, expression: "sad" },
  soft: { mouthForm: 0.35, eyeOpen: 0.9, angleZ: -1, expression: "comfort" },
  engaged: { mouthForm: 0.25, eyeOpen: 1, angleZ: 0, expression: "speaking" }
};

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function rounded(value) {
  return Number(value.toFixed(3));
}

export function mapStateToLive2DCommands(state = {}, pointer = { x: 0, y: 0 }, interactionProfile = {}) {
  const parameterAliases = resolveLive2DParameterAliases(interactionProfile.parameters || {});
  const emotion = EMOTION_PRESETS[state.emotion] || EMOTION_PRESETS.neutral;
  const intensity = clamp(Number(state.intensity ?? 0.25), 0, 1);
  const pointerX = clamp(Number(pointer.x ?? 0), -1, 1);
  const pointerY = clamp(Number(pointer.y ?? 0), -1, 1);
  const pointerStrength = rounded(clamp(Math.hypot(pointerX, pointerY), 0, 1));
  const followIntensity = 0.7 + intensity * 0.45;
  const headMultiplier = readMultiplier(interactionProfile.headTrackingMultiplier, 1);
  const eyeMultiplier = readMultiplier(interactionProfile.eyeTrackingMultiplier, 1);
  const bodyMultiplier = readMultiplier(interactionProfile.bodyTrackingMultiplier, 1);
  const mouth = clamp(Number(state.mouth ?? 0), 0, 1);

  const parameters = {};
  writeResolvedParameter(parameters, parameterAliases.aliases.headX, pointerX * 44 * followIntensity * headMultiplier);
  writeResolvedParameter(parameters, parameterAliases.aliases.headY, pointerY * -38 * followIntensity * headMultiplier);
  writeResolvedParameter(parameters, parameterAliases.aliases.headZ, emotion.angleZ * intensity);
  writeResolvedParameter(parameters, parameterAliases.aliases.bodyX, pointerX * 17 * followIntensity * bodyMultiplier);
  writeResolvedParameter(parameters, parameterAliases.aliases.bodyY, pointerY * -10 * followIntensity * bodyMultiplier);
  writeResolvedParameter(parameters, parameterAliases.aliases.eyeLOpen, emotion.eyeOpen);
  writeResolvedParameter(parameters, parameterAliases.aliases.eyeROpen, emotion.eyeOpen);
  writeResolvedParameter(parameters, parameterAliases.aliases.eyeX, clamp(pointerX * 1.25 * eyeMultiplier, -1, 1));
  writeResolvedParameter(parameters, parameterAliases.aliases.eyeY, clamp(pointerY * -1.5 * eyeMultiplier, -1, 1));
  writeResolvedParameter(parameters, parameterAliases.aliases.mouthOpen, mouth);
  writeResolvedParameter(parameters, parameterAliases.aliases.mouthForm, emotion.mouthForm);
  writeResolvedParameter(parameters, parameterAliases.aliases.breath, 0.5 + intensity * 0.5);

  return {
    parameters,
    parameterDiagnostics: parameterAliases.aliases,
    parameterWarnings: parameterAliases.warnings,
    expression: emotion.expression,
    motion: state.sequence || state.motion || "idle",
    pointer: {
      x: pointerX,
      y: pointerY,
      strength: pointerStrength
    },
    source: state.source || "unknown"
  };
}

export function getLive2DParameterIds() {
  return { ...PARAMETER_IDS };
}

export function resolveLive2DParameterAliases(parameters = {}) {
  const aliases = sanitizeParameterAliases(parameters);
  const warnings = [];
  for (const [semantic, alias] of Object.entries(parameters || {})) {
    const id = typeof alias === "string" ? alias : alias?.id;
    if (Object.hasOwn(aliases, semantic) && (typeof id !== "string" || !id.trim())) {
      warnings.push(`parameter ${semantic} has no id; using default ${aliases[semantic].id}`);
    }
  }
  return { aliases, warnings };
}

function writeResolvedParameter(parameters, alias, value) {
  if (!alias?.id) {
    return;
  }
  const scaled = Number(value) * Number(alias.scale ?? 1);
  const inverted = alias.invert ? -scaled : scaled;
  parameters[alias.id] = rounded(clamp(inverted, Number(alias.min), Number(alias.max)));
}

function readMultiplier(value, fallback) {
  const number = Number(value);
  return Number.isFinite(number) ? number : fallback;
}
