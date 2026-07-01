export function sanitizeMotionBindings(bindings = {}) {
  return Object.fromEntries(
    Object.entries(bindings || {})
      .map(([motion, binding]) => [
        motion,
        {
          group: String(binding?.group || "Idle"),
          index: Math.max(0, Math.floor(Number(binding?.index ?? 0)))
        }
      ])
      .filter(([motion]) => typeof motion === "string" && motion.length > 0)
  );
}

export function serializeMotionBindings(bindings = {}) {
  return JSON.stringify(sanitizeMotionBindings(bindings), null, 2);
}

export function parseMotionBindingsText(text = "") {
  const parsed = JSON.parse(text || "{}");
  if (!parsed || Array.isArray(parsed) || typeof parsed !== "object") {
    throw new Error("Motion bindings must be a JSON object.");
  }
  return sanitizeMotionBindings(parsed);
}
