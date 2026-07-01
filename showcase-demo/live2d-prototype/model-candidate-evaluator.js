const REQUIRED_ACTIONS = Object.freeze(["idle", "listen", "think", "speak", "happy", "comfort", "greet"]);
const REQUIRED_EXPRESSIONS = Object.freeze(["neutral", "happy", "thinking", "sad", "soft", "engaged"]);
const IDLE_QUALITY_ACTIONS = Object.freeze(["idle", "listen", "think", "comfort"]);
const EXPRESSIVE_ACTIONS = Object.freeze(["speak", "reply", "greet", "happy"]);

export function evaluateModelCandidate(packageInfo = {}, profile = {}) {
  const checks = [
    scoreActionMappings(profile, packageInfo),
    scoreExpressionMappings(profile),
    scoreExpressionAssets(packageInfo),
    scoreIdleMotions(packageInfo, profile),
    scoreSpeakMotion(packageInfo, profile),
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

function scoreActionMappings(profile, packageInfo) {
  const mappings = profile?.mappings?.actions || {};
  const missing = REQUIRED_ACTIONS.filter((action) => !hasValidActionMapping(mappings, action, packageInfo));
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

function scoreIdleMotions(packageInfo, profile) {
  const mappings = profile?.mappings?.actions || {};
  const mappedCount = IDLE_QUALITY_ACTIONS.filter((action) => (
    hasValidActionMapping(mappings, action, packageInfo)
  )).length;
  const fallbackCount = mappedCount ? mappedCount : Number(packageInfo.motionGroupCounts?.Idle ?? 0);
  const score = fallbackCount >= 4 ? 12 : Math.round(12 * Math.min(1, fallbackCount / 4));
  return {
    key: "idleMotions",
    score,
    missing: fallbackCount >= 4 ? [] : ["idle motion variety"]
  };
}

function scoreSpeakMotion(packageInfo, profile) {
  const mappings = profile?.mappings?.actions || {};
  const hasExpressiveMapping = EXPRESSIVE_ACTIONS.some((action) => (
    hasValidActionMapping(mappings, action, packageInfo)
  ));
  const count = hasExpressiveMapping ? 1 : Number(packageInfo.motionGroupCounts?.TapBody ?? 0);
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

function hasValidActionMapping(mappings = {}, action, packageInfo = {}) {
  return hasMotion(packageInfo, mappings[action]);
}

function hasMotion(packageInfo = {}, binding = null) {
  const group = String(binding?.group || "").trim();
  const index = Math.max(0, Math.floor(Number(binding?.index ?? 0)));
  const count = Number(packageInfo?.motionGroupCounts?.[group] ?? 0);
  return Boolean(group) && Number.isFinite(count) && index >= 0 && index < count;
}
