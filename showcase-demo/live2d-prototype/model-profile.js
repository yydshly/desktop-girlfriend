import { sanitizeMotionBindings } from "./motion-bindings.js";

export function modelJsonUrlToProfileUrl(modelJsonUrl = "") {
  const baseHref = globalThis.window?.location?.href || "http://127.0.0.1/live2d-prototype/";
  return new URL("profile.json", new URL(modelJsonUrl, baseHref)).toString();
}

export function normalizeModelProfile(profile = {}) {
  return {
    displayName: typeof profile.displayName === "string" ? profile.displayName : "",
    motionBindings: sanitizeMotionBindings(profile.motionBindings || {}),
    desktopPlacement: sanitizeDesktopPlacement(profile.desktopPlacement || {})
  };
}

export function sanitizeDesktopPlacement(placement = {}) {
  const sanitized = {};
  const scaleMultiplier = finiteNumber(placement.scaleMultiplier);
  const xOffsetRatio = finiteNumber(placement.xOffsetRatio);
  const yRatio = finiteNumber(placement.yRatio);
  if (scaleMultiplier !== null) {
    sanitized.scaleMultiplier = clamp(scaleMultiplier, 0.75, 1.35);
  }
  if (xOffsetRatio !== null) {
    sanitized.xOffsetRatio = clamp(xOffsetRatio, -0.35, 0.35);
  }
  if (yRatio !== null) {
    sanitized.yRatio = clamp(yRatio, 0.42, 0.68);
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
