import { mountLive2DDebugPanel } from "./debug-panel.js";
import { getLive2DAppMode, shouldMountDebugPanel } from "./live2d-app-mode.js";
import { detectLive2DSdk } from "./live2d-sdk-loader.js";
import { createLive2DRuntime } from "./runtime-app.js";

const routeParams = new URLSearchParams(window.location.search);
const mode = getLive2DAppMode(routeParams);
document.documentElement.dataset.mode = mode;

const runtime = createLive2DRuntime({
  document,
  window,
  routeParams,
  mode
});

if (shouldMountDebugPanel(mode)) {
  mountLive2DDebugPanel({
    document,
    window,
    runtime,
    mode
  });
}

runtime.start();

window.live2dPrototype = {
  applyState: (state) => runtime.applyState(state),
  playSequence: (name) => runtime.playSequence(name),
  playMotionProbe: (group, index) => runtime.playMotionProbe(group, index),
  handleBridgeMessage: (message) => runtime.handleBridgeMessage(message),
  isDesktopMode: () => runtime.isDesktopMode(),
  getModelUrl: () => runtime.getModelUrl(),
  getRendererMode: () => runtime.getRendererMode(),
  detectSdk: () => detectLive2DSdk(window),
  inspectModel: () => runtime.inspectModel()
};
