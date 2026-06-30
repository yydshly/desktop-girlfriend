import { mapStateToLive2DCommands } from "../live2d-parameter-mapper.js";

export class Live2DRenderer {
  constructor(canvas, options = {}) {
    this.canvas = canvas;
    this.modelUrl = options.modelUrl || "";
    this.model = null;
    this.pointer = { x: 0, y: 0 };
    this.lastCommands = mapStateToLive2DCommands();
  }

  async start() {
    throw new Error("Live2DRenderer requires a Live2D SDK integration and a legal model asset.");
  }

  stop() {}

  setPointer(x, y) {
    this.pointer = { x, y };
  }

  applyState(nextState) {
    this.lastCommands = mapStateToLive2DCommands(nextState, this.pointer);
    return this.lastCommands;
  }

  getLastCommands() {
    return this.lastCommands;
  }
}
