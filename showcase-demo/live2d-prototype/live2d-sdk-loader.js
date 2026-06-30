const SDK_GLOBALS = [
  { key: "PIXI", label: "PIXI runtime" },
  { key: "Live2DCubismCore", label: "Live2D Cubism Core" },
  { key: "PIXI.live2d", label: "PIXI Live2D plugin", getValue: (root) => root.PIXI?.live2d }
];

const CDN_SCRIPTS = [
  "https://cdn.jsdelivr.net/npm/pixi.js@6.5.10/dist/browser/pixi.min.js",
  "https://cubism.live2d.com/sdk-web/cubismcore/live2dcubismcore.min.js",
  "https://cdn.jsdelivr.net/npm/pixi-live2d-display@0.4.0/dist/index.min.js"
];

export function detectLive2DSdk(root = globalThis) {
  const globals = SDK_GLOBALS.map((entry) => ({
    ...entry,
    available: Boolean(entry.getValue ? entry.getValue(root) : root[entry.key])
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

export async function ensureLive2DSdk(root = globalThis) {
  const before = detectLive2DSdk(root);
  if (before.ready) {
    return before;
  }

  for (const src of CDN_SCRIPTS) {
    await loadScriptOnce(src, root.document);
  }

  return detectLive2DSdk(root);
}

function loadScriptOnce(src, documentRef) {
  if (!documentRef) {
    return Promise.reject(new Error("Document is not available for script loading."));
  }

  const existing = documentRef.querySelector(`script[data-live2d-sdk="${src}"]`);
  if (existing) {
    return Promise.resolve();
  }

  return new Promise((resolve, reject) => {
    const script = documentRef.createElement("script");
    script.src = src;
    script.async = false;
    script.dataset.live2dSdk = src;
    script.addEventListener("load", () => resolve());
    script.addEventListener("error", () => reject(new Error(`Failed to load SDK script: ${src}`)));
    documentRef.head.appendChild(script);
  });
}
