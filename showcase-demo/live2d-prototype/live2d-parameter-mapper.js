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

export function mapStateToLive2DCommands(state = {}, pointer = { x: 0, y: 0 }) {
  const emotion = EMOTION_PRESETS[state.emotion] || EMOTION_PRESETS.neutral;
  const intensity = clamp(Number(state.intensity ?? 0.25), 0, 1);
  const pointerX = clamp(Number(pointer.x ?? 0), -1, 1);
  const pointerY = clamp(Number(pointer.y ?? 0), -1, 1);
  const pointerStrength = rounded(clamp(Math.hypot(pointerX, pointerY), 0, 1));
  const followIntensity = 0.45 + intensity * 0.55;
  const mouth = clamp(Number(state.mouth ?? 0), 0, 1);

  const parameters = {
    [PARAMETER_IDS.angleX]: rounded(pointerX * 30 * followIntensity),
    [PARAMETER_IDS.angleY]: rounded(pointerY * -20 * followIntensity),
    [PARAMETER_IDS.angleZ]: rounded(emotion.angleZ * intensity),
    [PARAMETER_IDS.bodyAngleX]: rounded(pointerX * 15 * followIntensity),
    [PARAMETER_IDS.bodyAngleY]: rounded(pointerY * -8 * followIntensity),
    [PARAMETER_IDS.eyeLOpen]: rounded(emotion.eyeOpen),
    [PARAMETER_IDS.eyeROpen]: rounded(emotion.eyeOpen),
    [PARAMETER_IDS.eyeBallX]: rounded(pointerX),
    [PARAMETER_IDS.eyeBallY]: rounded(pointerY * -1),
    [PARAMETER_IDS.mouthOpenY]: rounded(mouth),
    [PARAMETER_IDS.mouthForm]: rounded(emotion.mouthForm),
    [PARAMETER_IDS.breath]: rounded(0.5 + intensity * 0.5)
  };

  return {
    parameters,
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
