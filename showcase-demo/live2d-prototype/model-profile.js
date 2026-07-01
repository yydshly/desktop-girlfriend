import { sanitizeMotionBindings } from "./motion-bindings.js";
import {
  CHARACTER_CONTRACT_VERSION,
  normalizeCharacterAction,
  normalizeCharacterExpression
} from "./character-contract.js";

export function modelJsonUrlToProfileUrl(modelJsonUrl = "") {
  const baseHref = globalThis.window?.location?.href || "http://127.0.0.1/live2d-prototype/";
  return new URL("profile.json", new URL(modelJsonUrl, baseHref)).toString();
}

export function normalizeModelProfile(profile = {}) {
  const mappings = sanitizeProfileMappings(profile.mappings || {}, profile.motionBindings || {});
  return {
    schemaVersion: CHARACTER_CONTRACT_VERSION,
    displayName: typeof profile.displayName === "string" ? profile.displayName : "",
    motionBindings: mappings.actions,
    mappings,
    desktopPlacement: sanitizeDesktopPlacement(profile.desktopPlacement || {})
  };
}

export function createEffectiveModelProfile(profile = {}, actionOverrides = {}) {
  const normalizedProfile = normalizeModelProfile(profile);
  const mappings = sanitizeProfileMappings({
    ...normalizedProfile.mappings,
    actions: {
      ...(normalizedProfile.mappings.actions || {}),
      ...actionOverrides
    }
  });
  return {
    ...normalizedProfile,
    motionBindings: mappings.actions,
    mappings
  };
}

export function sanitizeProfileMappings(mappings = {}, legacyMotionBindings = {}) {
  const actions = sanitizeActionMappings({
    ...legacyMotionBindings,
    ...(mappings.actions || {})
  });
  return {
    actions,
    expressions: sanitizeExpressionMappings(mappings.expressions || {})
  };
}

function sanitizeActionMappings(actions = {}) {
  const sanitized = {};
  for (const [action, binding] of Object.entries(actions || {})) {
    const normalizedAction = normalizeCharacterAction(action, "");
    if (!normalizedAction) {
      continue;
    }
    const cleanBinding = sanitizeMotionBindings({ [normalizedAction]: binding })[normalizedAction];
    if (cleanBinding) {
      sanitized[normalizedAction] = cleanBinding;
    }
  }
  return sanitized;
}

function sanitizeExpressionMappings(expressions = {}) {
  const sanitized = {};
  for (const [expression, modelExpression] of Object.entries(expressions || {})) {
    const normalizedExpression = normalizeCharacterExpression(expression, "");
    if (!normalizedExpression || typeof modelExpression !== "string" || !modelExpression.trim()) {
      continue;
    }
    sanitized[normalizedExpression] = modelExpression.trim();
  }
  return sanitized;
}

export function sanitizeDesktopPlacement(placement = {}) {
  const sanitized = {};
  const scaleMultiplier = finiteNumber(placement.scaleMultiplier);
  const xOffsetRatio = finiteNumber(placement.xOffsetRatio);
  const yRatio = finiteNumber(placement.yRatio);
  const pointerFollowXRatio = finiteNumber(placement.pointerFollowXRatio);
  const pointerFollowYRatio = finiteNumber(placement.pointerFollowYRatio);
  const headTrackingMultiplier = finiteNumber(placement.headTrackingMultiplier);
  const eyeTrackingMultiplier = finiteNumber(placement.eyeTrackingMultiplier);
  const bodyTrackingMultiplier = finiteNumber(placement.bodyTrackingMultiplier);
  const ambientGestureIntervalMs = finiteNumber(placement.ambientGestureIntervalMs);
  if (scaleMultiplier !== null) {
    sanitized.scaleMultiplier = clamp(scaleMultiplier, 0.75, 1.35);
  }
  if (xOffsetRatio !== null) {
    sanitized.xOffsetRatio = clamp(xOffsetRatio, -0.35, 0.35);
  }
  if (yRatio !== null) {
    sanitized.yRatio = clamp(yRatio, 0.42, 0.68);
  }
  if (pointerFollowXRatio !== null) {
    sanitized.pointerFollowXRatio = clamp(pointerFollowXRatio, 0, 0.035);
  }
  if (pointerFollowYRatio !== null) {
    sanitized.pointerFollowYRatio = clamp(pointerFollowYRatio, 0, 0.025);
  }
  if (headTrackingMultiplier !== null) {
    sanitized.headTrackingMultiplier = clamp(headTrackingMultiplier, 0.4, 1.6);
  }
  if (eyeTrackingMultiplier !== null) {
    sanitized.eyeTrackingMultiplier = clamp(eyeTrackingMultiplier, 0.4, 1.8);
  }
  if (bodyTrackingMultiplier !== null) {
    sanitized.bodyTrackingMultiplier = clamp(bodyTrackingMultiplier, 0, 1.4);
  }
  if (ambientGestureIntervalMs !== null) {
    sanitized.ambientGestureIntervalMs = clamp(ambientGestureIntervalMs, 4000, 20000);
  }
  if (placement.pointerFollow === false) {
    sanitized.pointerFollow = false;
  }
  return sanitized;
}

export async function loadModelProfile(modelJsonUrl) {
  const profileUrl = modelJsonUrlToProfileUrl(modelJsonUrl);
  const response = await fetch(profileUrl, { cache: "no-store" });
  if (!response.ok) {
    return normalizeModelProfile();
  }
  return normalizeModelProfile(await response.json());
}

function finiteNumber(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function clamp(value, minimum, maximum) {
  return Math.min(maximum, Math.max(minimum, value));
}
