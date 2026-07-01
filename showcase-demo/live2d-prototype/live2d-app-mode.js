export function getLive2DAppMode(routeParams = new URLSearchParams()) {
  return routeParams.get("desktop") === "1" ? "desktop" : "showcase";
}

export function shouldMountDebugPanel(mode) {
  return mode !== "desktop";
}
