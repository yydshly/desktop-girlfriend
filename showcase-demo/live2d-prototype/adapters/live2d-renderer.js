export class Live2DRenderer {
  constructor(canvas, options = {}) {
    this.canvas = canvas;
    this.modelUrl = options.modelUrl || "";
    this.model = null;
  }

  async start() {
    throw new Error("Live2DRenderer requires a Live2D SDK integration and a legal model asset.");
  }

  stop() {}

  setPointer(_x, _y) {}

  applyState(_nextState) {}
}
