export function modelIdToModelJsonUrl(modelId) {
  const safeParts = String(modelId || "")
    .split("/")
    .map((part) => part.trim())
    .filter(Boolean);
  if (safeParts.length === 0) {
    return "";
  }
  const modelName = safeParts[safeParts.length - 1];
  return `./assets/models/${safeParts.join("/")}/${modelName}.model3.json`;
}

export function resolveModelUrlFromRoute(routeParams, fallbackModelUrl) {
  const modelId = routeParams.get("model");
  if (!modelId) {
    return fallbackModelUrl;
  }
  return modelIdToModelJsonUrl(modelId) || fallbackModelUrl;
}
