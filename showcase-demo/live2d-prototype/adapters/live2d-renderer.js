import { inspectModelPackage } from "../model-package-inspector.js";
import { ensureLive2DSdk } from "../live2d-sdk-loader.js";
import { mapStateToLive2DCommands } from "../live2d-parameter-mapper.js";

export class Live2DRenderer {
  constructor(canvas, options = {}) {
    this.canvas = canvas;
    this.ctx = null;
    this.modelUrl = options.modelUrl || "";
    this.onStatusChange = options.onStatusChange || (() => {});
    this.app = null;
    this.model = null;
    this.live2dModel = null;
    this.previewImage = null;
    this.loadState = "idle";
    this.loadError = "";
    this.pointer = { x: 0, y: 0 };
    this.currentState = {};
    this.lastCommands = mapStateToLive2DCommands();
  }

  start() {
    this.lastCommands = mapStateToLive2DCommands();
    this.loadLive2DModel();
    this.draw();
  }

  stop() {
    if (this.app) {
      this.app.destroy(false, { children: true, texture: false, baseTexture: false });
      this.app = null;
      this.live2dModel = null;
    }
  }

  setPointer(x, y) {
    this.pointer = { x, y };
    this.lastCommands = mapStateToLive2DCommands(this.currentState, this.pointer);
    this.applyLive2DCommands();
    this.draw();
  }

  applyState(nextState) {
    this.currentState = nextState;
    this.lastCommands = mapStateToLive2DCommands(nextState, this.pointer);
    this.applyLive2DCommands();
    this.draw();
    return this.lastCommands;
  }

  getLastCommands() {
    return this.lastCommands;
  }

  async loadPreviewTexture() {
    this.loadState = "loading";
    this.emitStatus();
    this.draw();

    try {
      const packageInfo = await inspectModelPackage(this.modelUrl);
      if (!packageInfo.firstTextureUrl) {
        throw new Error("Model package does not reference a texture.");
      }
      this.model = packageInfo;
      this.previewImage = await loadImage(packageInfo.firstTextureUrl);
      this.loadState = "ready";
    } catch (error) {
      this.loadState = "error";
      this.loadError = error.message;
    }

    this.emitStatus();
    this.draw();
  }

  async loadLive2DModel() {
    this.loadState = "loading-sdk";
    this.loadError = "";
    this.emitStatus();
    this.draw();

    try {
      const sdk = await ensureLive2DSdk(window);
      if (!sdk.ready) {
        throw new Error(`SDK incomplete after load: ${sdk.missing.join(", ")}`);
      }

      this.loadState = "loading-model";
      this.emitStatus();
      this.draw();

      const PIXI = window.PIXI;
      const app = new PIXI.Application({
        view: this.canvas,
        autoStart: true,
        backgroundAlpha: 0,
        antialias: true
      });
      const live2dModel = await PIXI.live2d.Live2DModel.from(this.modelUrl);
      live2dModel.anchor.set(0.5, 0.5);
      live2dModel.scale.set(Math.min(this.canvas.width / live2dModel.width, this.canvas.height / live2dModel.height) * 0.82);
      live2dModel.position.set(this.canvas.width / 2, this.canvas.height / 2);
      app.stage.addChild(live2dModel);

      this.app = app;
      this.live2dModel = live2dModel;
      this.loadState = "live2d-ready";
      this.applyLive2DCommands();
      this.emitStatus();
    } catch (error) {
      this.loadError = `SDK/model load failed, using texture preview: ${error.message}`;
      this.emitStatus();
      await this.loadPreviewTexture();
    }
  }

  draw() {
    if (this.live2dModel) {
      return;
    }
    this.ctx = this.ctx || this.canvas.getContext("2d");
    const ctx = this.ctx;
    const w = this.canvas.width;
    const h = this.canvas.height;
    ctx.clearRect(0, 0, w, h);

    ctx.fillStyle = "#10161a";
    ctx.fillRect(0, 0, w, h);
    ctx.fillStyle = "rgba(242, 166, 179, 0.12)";
    ctx.beginPath();
    ctx.ellipse(w / 2, h * 0.52, w * 0.31, h * 0.36, 0, 0, Math.PI * 2);
    ctx.fill();

    if (this.previewImage) {
      const maxW = w * 0.72;
      const maxH = h * 0.72;
      const scale = Math.min(maxW / this.previewImage.width, maxH / this.previewImage.height);
      const drawW = this.previewImage.width * scale;
      const drawH = this.previewImage.height * scale;
      const offsetX = this.pointer.x * 18;
      const offsetY = this.pointer.y * 12;
      ctx.drawImage(
        this.previewImage,
        (w - drawW) / 2 + offsetX,
        (h - drawH) / 2 + offsetY,
        drawW,
        drawH
      );
    }

    this.drawStatusText();
  }

  drawStatusText() {
    const ctx = this.ctx;
    const lines = [
      "Live2D adapter dry run",
      `model: ${this.modelUrl || "not configured"}`,
      `state: ${this.loadState}`,
      this.live2dModel ? "SDK renderer active" : "SDK renderer fallback preview"
    ];
    if (this.loadError) {
      lines.push(`error: ${this.loadError}`);
    }
    if (this.model) {
      lines.push(`motions: ${this.model.motionCount}, textures: ${this.model.textureCount}`);
    }

    ctx.save();
    ctx.font = "26px Segoe UI, sans-serif";
    ctx.fillStyle = "rgba(8, 11, 14, 0.72)";
    ctx.fillRect(28, 28, this.canvas.width - 56, 168);
    ctx.fillStyle = "#f4f7f8";
    lines.forEach((line, index) => {
      ctx.fillText(line, 48, 70 + index * 28);
    });
    ctx.restore();
  }

  applyLive2DCommands() {
    if (!this.live2dModel) {
      return;
    }

    const coreModel = this.live2dModel.internalModel?.coreModel;
    if (!coreModel?.setParameterValueById) {
      return;
    }

    Object.entries(this.lastCommands.parameters).forEach(([id, value]) => {
      coreModel.setParameterValueById(id, value);
    });
  }

  emitStatus() {
    this.onStatusChange({
      loadState: this.loadState,
      loadError: this.loadError,
      modelUrl: this.modelUrl,
      hasLive2DModel: Boolean(this.live2dModel)
    });
  }
}

function loadImage(src) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.addEventListener("load", () => resolve(image));
    image.addEventListener("error", () => reject(new Error(`Texture image failed to load: ${src}`)));
    image.src = src;
  });
}
