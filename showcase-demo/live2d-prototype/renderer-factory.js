import { Live2DRenderer } from "./adapters/live2d-renderer.js";
import { PlaceholderRenderer } from "./adapters/placeholder-renderer.js";

const RENDERER_LABELS = {
  placeholder: "placeholder renderer",
  live2d: "live2d adapter dry run"
};

export function createAvatarRenderer(mode, canvas, options = {}) {
  if (mode === "live2d") {
    return new Live2DRenderer(canvas, options);
  }
  return new PlaceholderRenderer(canvas);
}

export function getRendererLabel(mode) {
  return RENDERER_LABELS[mode] || RENDERER_LABELS.placeholder;
}
