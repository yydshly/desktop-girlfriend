import { sanitizeMotionBindings } from "./motion-bindings.js";

export function modelJsonUrlToProfileUrl(modelJsonUrl = "") {
  const baseHref = globalThis.window?.location?.href || "http://127.0.0.1/live2d-prototype/";
  return new URL("profile.json", new URL(modelJsonUrl, baseHref)).toString();
}

export function normalizeModelProfile(profile = {}) {
  return {
    displayName: typeof profile.displayName === "string" ? profile.displayName : "",
    motionBindings: sanitizeMotionBindings(profile.motionBindings || {})
  };
}

export async function loadModelProfile(modelJsonUrl) {
  const profileUrl = modelJsonUrlToProfileUrl(modelJsonUrl);
  const response = await fetch(profileUrl, { cache: "no-store" });
  if (!response.ok) {
    return normalizeModelProfile();
  }
  return normalizeModelProfile(await response.json());
}
