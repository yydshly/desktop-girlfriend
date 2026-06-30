const SDK_GLOBALS = [
  { key: "PIXI", label: "PIXI runtime" },
  { key: "Live2DCubismCore", label: "Live2D Cubism Core" },
  { key: "CubismFramework", label: "Cubism Framework" }
];

export function detectLive2DSdk(root = globalThis) {
  const globals = SDK_GLOBALS.map((entry) => ({
    ...entry,
    available: Boolean(root[entry.key])
  }));
  const available = globals.filter((entry) => entry.available).map((entry) => entry.key);
  const missing = globals.filter((entry) => !entry.available).map((entry) => entry.key);

  return {
    ready: missing.length === 0,
    available,
    missing,
    globals
  };
}

export function formatSdkStatus(status) {
  if (status.ready) {
    return "Live2D SDK runtime detected. The next step is loading a model3.json package.";
  }
  return `Live2D SDK runtime is not connected yet. Missing: ${status.missing.join(", ")}.`;
}
