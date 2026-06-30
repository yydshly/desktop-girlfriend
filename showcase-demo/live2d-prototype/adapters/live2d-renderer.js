import { inspectModelPackage } from "../model-package-inspector.js";
import { mapStateToLive2DCommands } from "../live2d-parameter-mapper.js";

export class Live2DRenderer {
  constructor(canvas, options = {}) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.modelUrl = options.modelUrl || "";
    this.model = null;
    this.previewImage = null;
    this.loadState = "idle";
    this.loadError = "";
    this.pointer = { x: 0, y: 0 };
    this.lastCommands = mapStateToLive2DCommands();
  }

  start() {
    this.lastCommands = mapStateToLive2DCommands();
    this.loadPreviewTexture();
    this.draw();
  }

  stop() {}

  setPointer(x, y) {
    this.pointer = { x, y };
    this.draw();
  }

  applyState(nextState) {
    this.lastCommands = mapStateToLive2DCommands(nextState, this.pointer);
    this.draw();
    return this.lastCommands;
  }

  getLastCommands() {
    return this.lastCommands;
  }

  async loadPreviewTexture() {
    this.loadState = "loading";
    this.loadError = "";
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

    this.draw();
  }

  draw() {
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
      "SDK renderer not connected yet"
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
}

function loadImage(src) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.addEventListener("load", () => resolve(image));
    image.addEventListener("error", () => reject(new Error(`Texture image failed to load: ${src}`)));
    image.src = src;
  });
}
