const SDK_GLOBALS = [
  { key: "PIXI", label: "PIXI runtime" },
  { key: "Live2DCubismCore", label: "Live2D Cubism Core" },
  {
    key: "PIXI.live2d.Live2DModel.from",
    label: "PIXI Live2D Cubism 4 model loader",
    getValue: (root) => root.PIXI?.live2d?.Live2DModel?.from
  }
];

const CDN_SCRIPTS = [
  "https://cdn.jsdelivr.net/npm/pixi.js@6.5.10/dist/browser/pixi.min.js",
  "https://cubism.live2d.com/sdk-web/cubismcore/live2dcubismcore.min.js",
  "https://cdn.jsdelivr.net/npm/pixi-live2d-display@0.4.0/dist/cubism4.min.js"
];

const SDK_READY_TIMEOUT_MS = 5000;
const SDK_READY_POLL_MS = 50;

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

  return waitForSdkReady(root);
}

async function waitForSdkReady(root) {
  const startedAt = Date.now();
  let status = detectLive2DSdk(root);

  while (!status.ready && Date.now() - startedAt < SDK_READY_TIMEOUT_MS) {
    await delay(SDK_READY_POLL_MS);
    status = detectLive2DSdk(root);
  }

  return status;
}

function loadScriptOnce(src, documentRef) {
  if (!documentRef) {
    return Promise.reject(new Error("Document is not available for script loading."));
  }

  const existing = documentRef.querySelector(`script[data-live2d-sdk="${src}"]`);
  if (existing) {
    return waitForScript(existing, src);
  }

  return new Promise((resolve, reject) => {
    const script = documentRef.createElement("script");
    script.src = src;
    script.async = false;
    script.dataset.live2dSdk = src;
    script.addEventListener("load", () => {
      script.dataset.live2dLoaded = "true";
      resolve();
    });
    script.addEventListener("error", () => {
      script.dataset.live2dError = "true";
      reject(new Error(`Failed to load SDK script: ${src}`));
    });
    documentRef.head.appendChild(script);
  });
}

function waitForScript(script, src) {
  if (script.dataset.live2dLoaded === "true") {
    return Promise.resolve();
  }

  if (script.dataset.live2dError === "true") {
    return Promise.reject(new Error(`Failed to load SDK script: ${src}`));
  }

  return new Promise((resolve, reject) => {
    script.addEventListener("load", () => {
      script.dataset.live2dLoaded = "true";
      resolve();
    });
    script.addEventListener("error", () => {
      script.dataset.live2dError = "true";
      reject(new Error(`Failed to load SDK script: ${src}`));
    });
  });
}

function delay(ms) {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}
