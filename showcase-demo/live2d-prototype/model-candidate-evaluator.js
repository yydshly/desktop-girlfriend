const REQUIRED_ACTIONS = Object.freeze(["idle", "listen", "think", "speak", "happy", "comfort", "greet"]);
const REQUIRED_EXPRESSIONS = Object.freeze(["neutral", "happy", "thinking", "sad", "soft", "engaged"]);

export function evaluateModelCandidate(packageInfo = {}, profile = {}) {
  const checks = [
    scoreActionMappings(profile),
    scoreExpressionMappings(profile),
    scoreExpressionAssets(packageInfo),
    scoreIdleMotions(packageInfo),
    scoreSpeakMotion(packageInfo),
    scoreLipSync(packageInfo),
    scoreEyeBlink(packageInfo),
    scorePhysics(packageInfo),
    scoreTexturePackage(packageInfo)
  ];
  const score = checks.reduce((sum, check) => sum + check.score, 0);
  return {
    score,
    grade: gradeCandidate(score),
    missing: checks.flatMap((check) => check.missing),
    checks
  };
}

function scoreActionMappings(profile) {
  const mappings = profile?.mappings?.actions || {};
  const missing = REQUIRED_ACTIONS.filter((action) => !mappings[action]);
  return {
    key: "actionMappings",
    score: missing.length ? Math.round(18 * (1 - missing.length / REQUIRED_ACTIONS.length)) : 18,
    missing: missing.length ? [`action mappings: ${missing.join(", ")}`] : []
  };
}

function scoreExpressionMappings(profile) {
  const mappings = profile?.mappings?.expressions || {};
  const missing = REQUIRED_EXPRESSIONS.filter((expression) => !hasStringMapping(mappings[expression]));
  return {
    key: "expressionMappings",
    score: missing.length ? Math.round(18 * (1 - missing.length / REQUIRED_EXPRESSIONS.length)) : 18,
    missing: missing.length ? [`expression mappings: ${missing.join(", ")}`] : []
  };
}

function scoreExpressionAssets(packageInfo) {
  const count = Number(packageInfo.expressionCount ?? 0);
  const score = count >= REQUIRED_EXPRESSIONS.length ? 14 : Math.round(14 * Math.min(1, count / REQUIRED_EXPRESSIONS.length));
  return {
    key: "expressionAssets",
    score,
    missing: count ? [] : ["expression assets"]
  };
}

function scoreIdleMotions(packageInfo) {
  const count = Number(packageInfo.motionGroupCounts?.Idle ?? 0);
  const score = count >= 4 ? 12 : Math.round(12 * Math.min(1, count / 4));
  return {
    key: "idleMotions",
    score,
    missing: count >= 4 ? [] : ["idle motion variety"]
  };
}

function scoreSpeakMotion(packageInfo) {
  const count = Number(packageInfo.motionGroupCounts?.TapBody ?? 0);
  return {
    key: "speakMotion",
    score: count > 0 ? 10 : 0,
    missing: count > 0 ? [] : ["speak/greet motion group"]
  };
}

function scoreLipSync(packageInfo) {
  const ids = Array.isArray(packageInfo.lipSyncIds) ? packageInfo.lipSyncIds : [];
  return {
    key: "lipSync",
    score: ids.length ? 10 : 0,
    missing: ids.length ? [] : ["lip sync parameter"]
  };
}

function scoreEyeBlink(packageInfo) {
  const ids = Array.isArray(packageInfo.eyeBlinkIds) ? packageInfo.eyeBlinkIds : [];
  return {
    key: "eyeBlink",
    score: ids.length >= 2 ? 6 : 0,
    missing: ids.length >= 2 ? [] : ["eye blink parameters"]
  };
}

function scorePhysics(packageInfo) {
  return {
    key: "physics",
    score: packageInfo.physics ? 6 : 0,
    missing: packageInfo.physics ? [] : ["physics"]
  };
}

function scoreTexturePackage(packageInfo) {
  const count = Number(packageInfo.textureCount ?? 0);
  return {
    key: "textures",
    score: count > 0 ? 6 : 0,
    missing: count > 0 ? [] : ["textures"]
  };
}

function gradeCandidate(score) {
  if (score >= 85) {
    return "strong";
  }
  if (score >= 70) {
    return "candidate";
  }
  if (score >= 45) {
    return "baseline";
  }
  return "weak";
}

function hasStringMapping(value) {
  return typeof value === "string" && value.trim().length > 0;
}
