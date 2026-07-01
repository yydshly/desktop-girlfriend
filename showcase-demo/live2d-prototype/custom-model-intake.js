import {
  CANONICAL_CHARACTER_ACTIONS,
  CANONICAL_CHARACTER_EXPRESSIONS,
  validateCharacterProfile
} from "./character-contract.js";

const REQUIRED_DESKTOP_PLACEMENT_FIELDS = Object.freeze([
  "scaleMultiplier",
  "xOffsetRatio",
  "yRatio",
  "pointerFollowXRatio",
  "pointerFollowYRatio",
  "headTrackingMultiplier",
  "eyeTrackingMultiplier",
  "bodyTrackingMultiplier",
  "ambientGestureIntervalMs"
]);

const REQUIRED_CUSTOM_ACTIONS = Object.freeze([
  "idle",
  "greet",
  "listen",
  "think",
  "reply",
  "comfort",
  "sad",
  "happy",
  "speak"
]);

export function validateCustomModelIntake(packageInfo = {}, profile = {}) {
  const blockers = [];
  const warnings = [];

  collectPackageBlockers(packageInfo, blockers);
  collectProfileIssues(profile, packageInfo, blockers, warnings);

  return {
    ready: blockers.length === 0,
    grade: gradeIntake(blockers, warnings),
    blockers,
    warnings,
    summary: buildIntakeSummary(packageInfo, profile)
  };
}

function collectPackageBlockers(packageInfo, blockers) {
  if (!packageInfo.moc) {
    blockers.push("model3 FileReferences.Moc is required");
  }
  if (Number(packageInfo.textureCount ?? 0) <= 0) {
    blockers.push("at least one texture is required");
  }
  if (Number(packageInfo.motionCount ?? 0) <= 0) {
    blockers.push("at least one motion is required");
  }
}

function collectProfileIssues(profile, packageInfo, blockers, warnings) {
  const profileValidation = validateCharacterProfile(profile);
  blockers.push(...profileValidation.errors);
  warnings.push(...profileValidation.warnings);

  const actions = profile?.mappings?.actions || {};
  for (const action of REQUIRED_CUSTOM_ACTIONS) {
    const binding = actions[action];
    if (!binding) {
      blockers.push(`mappings.actions.${action} is required`);
      continue;
    }
    if (!hasMotion(packageInfo, binding.group, binding.index)) {
      blockers.push(`mappings.actions.${action} points to missing motion ${binding.group}[${binding.index}]`);
    }
  }

  const expressions = profile?.mappings?.expressions || {};
  for (const expression of CANONICAL_CHARACTER_EXPRESSIONS) {
    const modelExpression = expressions[expression];
    if (!modelExpression) {
      warnings.push(`mappings.expressions.${expression} is not mapped`);
      continue;
    }
    if (!hasExpression(packageInfo, modelExpression)) {
      blockers.push(`mappings.expressions.${expression} points to missing expression ${modelExpression}`);
    }
  }

  const desktopPlacement = profile?.desktopPlacement || {};
  for (const field of REQUIRED_DESKTOP_PLACEMENT_FIELDS) {
    if (!Number.isFinite(Number(desktopPlacement[field]))) {
      warnings.push(`desktopPlacement.${field} should be tuned for desktop mode`);
    }
  }

  if (!Array.isArray(packageInfo.lipSyncIds) || packageInfo.lipSyncIds.length === 0) {
    warnings.push("lip sync parameter is recommended for speaking");
  }
  if (!Array.isArray(packageInfo.eyeBlinkIds) || packageInfo.eyeBlinkIds.length < 2) {
    warnings.push("eye blink parameters are recommended");
  }
  if (!packageInfo.physics) {
    warnings.push("physics is recommended for hair and clothing softness");
  }
}

function hasMotion(packageInfo, group, index) {
  const count = Number(packageInfo?.motionGroupCounts?.[group] ?? 0);
  const motionIndex = Number(index);
  return typeof group === "string"
    && group.length > 0
    && Number.isInteger(motionIndex)
    && motionIndex >= 0
    && motionIndex < count;
}

function hasExpression(packageInfo, expression) {
  const names = Array.isArray(packageInfo.expressionNames) ? packageInfo.expressionNames : [];
  return typeof expression === "string" && names.includes(expression);
}

function gradeIntake(blockers, warnings) {
  if (blockers.length) {
    return "blocked";
  }
  return warnings.length ? "usable-with-warnings" : "ready";
}

function buildIntakeSummary(packageInfo, profile) {
  const actions = profile?.mappings?.actions || {};
  const expressions = profile?.mappings?.expressions || {};
  return {
    displayName: profile.displayName || "",
    modelVersion: packageInfo.version || "unknown",
    motionGroups: packageInfo.motionGroupCounts || {},
    expressionCount: Number(packageInfo.expressionCount ?? 0),
    mappedActions: CANONICAL_CHARACTER_ACTIONS.filter((action) => Boolean(actions[action])),
    mappedExpressions: CANONICAL_CHARACTER_EXPRESSIONS.filter((expression) => Boolean(expressions[expression]))
  };
}
