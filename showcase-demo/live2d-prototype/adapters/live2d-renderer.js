import { inspectModelPackage } from "../model-package-inspector.js";
import { ensureLive2DSdk } from "../live2d-sdk-loader.js";
import { mapStateToLive2DCommands } from "../live2d-parameter-mapper.js";

export class Live2DRenderer {
  constructor(canvas, options = {}) {
    this.canvas = canvas;
    this.ctx = null;
    this.modelUrl = options.modelUrl || "";
    this.allowTextureFallback = options.allowTextureFallback !== false;
    this.onStatusChange = options.onStatusChange || (() => {});
    this.app = null;
    this.model = null;
    this.live2dModel = null;
    this.previewImage = null;
    this.loadState = "idle";
    this.loadError = "";
    this.pointer = { x: 0, y: 0 };
    this.targetPointer = { x: 0, y: 0 };
    this.smoothedPointer = { x: 0, y: 0 };
    this.currentState = {};
    this.lastCommands = mapStateToLive2DCommands();
    this.lastMotionKey = "";
    this.lastExpressionKey = "";
    this.activeExpression = "";
    this.activeMotion = { group: "", index: 0, source: "" };
    this.raf = 0;
    this.idleMotionIndex = 0;
    this.nextIdleMotionAt = 0;
    this.returnToIdleAt = 0;
    this.lastMotionPlayedAt = -Infinity;
  }

  start() {
    this.lastCommands = mapStateToLive2DCommands();
    this.loadLive2DModel();
  }

  stop() {
    if (this.raf) {
      cancelAnimationFrame(this.raf);
      this.raf = 0;
    }
    if (this.app) {
      this.app.destroy(false, { children: true, texture: false, baseTexture: false });
      this.app = null;
      this.live2dModel = null;
    }
  }

  setPointer(x, y) {
    this.targetPointer = { x, y };
    this.draw();
  }

  applyState(nextState) {
    this.currentState = nextState;
    this.lastCommands = mapStateToLive2DCommands(nextState, this.pointer);
    this.applyLive2DCommands();
    this.applyLive2DExpression();
    this.playLive2DMotion();
    this.scheduleReturnToIdle(performance.now());
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

    try {
      const sdk = await ensureLive2DSdk(window);
      if (!sdk.ready) {
        throw new Error(`SDK incomplete after load: ${sdk.missing.join(", ")}`);
      }

      this.loadState = "loading-model";
      this.emitStatus();

      const PIXI = window.PIXI;
      const Live2DModel = getLive2DModelFactory(PIXI);
      this.model = await inspectModelPackage(this.modelUrl);
      const app = new PIXI.Application({
        view: this.canvas,
        autoStart: true,
        backgroundAlpha: 0,
        antialias: true
      });
      const live2dModel = await Live2DModel.from(this.modelUrl);
      live2dModel.anchor.set(0.5, 0.5);
      const placement = calculateLive2DPlacement(
        { width: this.canvas.width, height: this.canvas.height },
        { width: live2dModel.width, height: live2dModel.height }
      );
      live2dModel.scale.set(placement.scale);
      live2dModel.position.set(placement.x, placement.y);
      app.stage.addChild(live2dModel);

      this.app = app;
      this.live2dModel = live2dModel;
      this.loadState = "live2d-ready";
      this.applyLive2DCommands();
      this.playLive2DMotion({ force: true });
      this.startParameterLoop();
      this.emitStatus();
    } catch (error) {
      this.loadError = this.allowTextureFallback
        ? `SDK/model load failed, using texture preview: ${error.message}`
        : `SDK/model load failed: ${error.message}`;
      this.emitStatus();
      if (this.allowTextureFallback) {
        await this.loadPreviewTexture();
        return;
      }
      this.loadState = "error";
      this.emitStatus();
      this.draw();
    }
  }

  draw() {
    if (this.live2dModel) {
      return;
    }
    if (!this.shouldDrawFallback()) {
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

  shouldDrawFallback() {
    return this.allowTextureFallback
      && (Boolean(this.previewImage) || this.loadState === "ready" || this.loadState === "error");
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

    const parameters = calculateAnimatedLive2DParameters(
      this.lastCommands.parameters,
      this.lastCommands,
      performance.now()
    );

    Object.entries(parameters).forEach(([id, value]) => {
      coreModel.setParameterValueById(id, value);
    });
  }

  startParameterLoop() {
    if (this.raf || typeof requestAnimationFrame !== "function") {
      return;
    }

    const frame = () => {
      this.updateSmoothedPointer();
      this.applyLive2DCommands();
      this.applyLive2DExpression();
      this.advanceReturnToIdle(performance.now());
      this.advanceIdleMotion(performance.now());
      this.raf = requestAnimationFrame(frame);
    };
    this.raf = requestAnimationFrame(frame);
  }

  updateSmoothedPointer() {
    this.smoothedPointer = smoothPointer(this.smoothedPointer, this.targetPointer, 0.18);
    this.pointer = this.smoothedPointer;
    this.lastCommands = mapStateToLive2DCommands(this.currentState, this.pointer);
  }

  advanceIdleMotion(now) {
    if (!this.live2dModel?.motion || !shouldAutoRotateIdleMotion(this.lastCommands)) {
      return;
    }

    if (now < this.nextIdleMotionAt) {
      return;
    }

    this.idleMotionIndex = (
      this.idleMotionIndex + 1
    ) % getMotionGroupCount(this.model?.motionGroupCounts, "Idle", DEFAULT_IDLE_MOTION_COUNT);
    this.nextIdleMotionAt = now + IDLE_MOTION_INTERVAL_MS;
    this.playLive2DMotion({
      force: true,
      override: { group: "Idle", index: this.idleMotionIndex, source: "idle-auto" }
    });
  }

  scheduleReturnToIdle(now) {
    const delay = getReturnToIdleDelayMs(this.lastCommands);
    this.returnToIdleAt = delay > 0 ? now + delay : 0;
  }

  advanceReturnToIdle(now) {
    if (!this.returnToIdleAt || now < this.returnToIdleAt) {
      return;
    }

    this.returnToIdleAt = 0;
    this.currentState = {
      emotion: "neutral",
      mouth: 0,
      gaze: "cursor",
      motion: "idle",
      intensity: 0.25,
      source: "visual.auto-idle"
    };
    this.lastCommands = mapStateToLive2DCommands(this.currentState, this.pointer);
    this.applyLive2DCommands();
    this.applyLive2DExpression();
    this.playLive2DMotion({
      force: true,
      override: { group: "Idle", index: 0, source: "auto-return" }
    });
  }

  playLive2DMotion(options = {}) {
    if (!this.live2dModel?.motion) {
      return;
    }

    const now = performance.now();
    if (!options.force && now - this.lastMotionPlayedAt < MOTION_COOLDOWN_MS) {
      return;
    }

    const motion = options.override || mapCommandToModelMotion(
      this.lastCommands,
      this.model?.motionGroupCounts
    );
    const motionKey = `${motion.group}:${motion.index}:${motion.source}`;
    if (!options.force && motionKey === this.lastMotionKey) {
      return;
    }

    this.live2dModel.motion(motion.group, motion.index);
    this.lastMotionPlayedAt = now;
    this.lastMotionKey = motionKey;
    this.activeMotion = motion;
    this.emitStatus();
  }

  applyLive2DExpression() {
    if (!this.live2dModel?.expression) {
      return;
    }

    const expression = resolveSupportedExpression(
      this.lastCommands.expression || "",
      this.model?.expressionNames
    );
    if (!expression || expression === this.lastExpressionKey) {
      return;
    }

    this.live2dModel.expression(expression);
    this.lastExpressionKey = expression;
    this.activeExpression = expression;
    this.emitStatus();
  }

  emitStatus() {
    this.onStatusChange({
      loadState: this.loadState,
      loadError: this.loadError,
      modelUrl: this.modelUrl,
      hasLive2DModel: Boolean(this.live2dModel),
      activeMotion: this.activeMotion,
      activeExpression: this.activeExpression,
      modelCapabilities: getModelCapabilities(this.model)
    });
  }
}

const DEFAULT_IDLE_MOTION_COUNT = 9;
const IDLE_MOTION_INTERVAL_MS = 6500;
const MOTION_COOLDOWN_MS = 650;
const EXPRESSIVE_RETURN_TO_IDLE_MS = 4200;

function getLive2DModelFactory(PIXI) {
  const Live2DModel = PIXI?.live2d?.Live2DModel;
  if (!Live2DModel?.from) {
    throw new Error("PIXI Live2D Cubism 4 model loader is missing.");
  }
  return Live2DModel;
}

export function calculateLive2DPlacement(canvasSize, modelSize) {
  const safeModelWidth = Math.max(1, modelSize.width);
  const safeModelHeight = Math.max(1, modelSize.height);
  const scale = Math.min(
    canvasSize.width / safeModelWidth * 0.92,
    canvasSize.height / safeModelHeight * 1.08
  );

  return {
    scale,
    x: canvasSize.width / 2,
    y: canvasSize.height * 0.55
  };
}

export function mapCommandToModelMotion(command = {}, motionGroupCounts = null) {
  const motion = command.motion || "idle";
  const expressiveMotions = new Set(["greet", "happy", "reply", "comfort", "speak"]);
  if (expressiveMotions.has(motion) && hasMotionGroup(motionGroupCounts, "TapBody")) {
    return {
      group: "TapBody",
      index: 0,
      source: motion
    };
  }

  return {
    group: "Idle",
    index: getIdleMotionVariantIndex(motion, motionGroupCounts),
    source: motion
  };
}

function getMotionGroupCount(motionGroupCounts = {}, group, fallback) {
  const count = Number((motionGroupCounts || {})[group] ?? fallback);
  return Number.isFinite(count) && count > 0 ? Math.floor(count) : fallback;
}

function hasMotionGroup(motionGroupCounts = null, group) {
  if (!motionGroupCounts) {
    return group === "TapBody";
  }
  const count = Number(motionGroupCounts[group] ?? 0);
  return Number.isFinite(count) && count > 0;
}

function getIdleMotionVariantIndex(motion, motionGroupCounts = null) {
  const preferredIndexByMotion = {
    idle: 0,
    think: 1,
    sad: 2,
    listen: 3,
    comfort: 4,
    reply: 0,
    speak: 0,
    greet: 0,
    happy: 0
  };
  const preferredIndex = preferredIndexByMotion[motion] ?? 0;
  const idleCount = getMotionGroupCount(motionGroupCounts, "Idle", DEFAULT_IDLE_MOTION_COUNT);
  return idleCount > 0 ? preferredIndex % idleCount : 0;
}

export function shouldAutoRotateIdleMotion(command = {}) {
  const motion = command.motion || "idle";
  return motion === "idle" || motion === "think" || motion === "sad";
}

export function getReturnToIdleDelayMs(command = {}) {
  const motion = command.motion || "";
  const expressiveMotions = new Set(["greet", "happy", "reply", "comfort", "speak"]);
  return expressiveMotions.has(motion) ? EXPRESSIVE_RETURN_TO_IDLE_MS : 0;
}

export function resolveSupportedExpression(expression = "", expressionNames = null) {
  if (!expression) {
    return "";
  }
  if (!Array.isArray(expressionNames)) {
    return expression;
  }
  return expressionNames.includes(expression) ? expression : "";
}

export function getModelCapabilities(model = null) {
  return {
    expressionCount: Number(model?.expressionCount ?? 0),
    expressionNames: Array.isArray(model?.expressionNames) ? model.expressionNames : [],
    motionCount: Number(model?.motionCount ?? 0),
    motionGroupCounts: model?.motionGroupCounts || {}
  };
}

export function calculateAnimatedLive2DParameters(parameters = {}, command = {}, now = 0) {
  const next = { ...parameters };
  const motion = command.motion || "";
  const speaking = motion === "reply"
    || motion === "speak"
    || command.expression === "speaking"
    || command.visualIntent === "speaking";

  if (speaking) {
    const pulse = 0.45 + Math.sin(now / 82) * 0.28 + Math.sin(now / 37) * 0.12;
    next.ParamMouthOpenY = roundToThree(Math.max(Number(next.ParamMouthOpenY ?? 0), pulse));
    next.ParamAngleX = roundParameter(
      Number(next.ParamAngleX ?? 0) + Math.sin(now / 260) * 2.2
    );
    next.ParamBodyAngleX = roundParameter(
      Number(next.ParamBodyAngleX ?? 0) + Math.sin(now / 320) * 1.4
    );
  }

  return next;
}

function roundToThree(value) {
  return Number(Math.min(1, Math.max(0, value)).toFixed(3));
}

function roundParameter(value) {
  return Number(value.toFixed(3));
}

export function smoothPointer(current = { x: 0, y: 0 }, target = { x: 0, y: 0 }, alpha = 0.18) {
  return {
    x: smoothAxis(Number(current.x ?? 0), Number(target.x ?? 0), alpha),
    y: smoothAxis(Number(current.y ?? 0), Number(target.y ?? 0), alpha)
  };
}

function smoothAxis(current, target, alpha) {
  const next = current + (target - current) * alpha;
  if (Math.abs(next - target) < 0.002) {
    return target;
  }
  return Number(next.toFixed(3));
}

function loadImage(src) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.addEventListener("load", () => resolve(image));
    image.addEventListener("error", () => reject(new Error(`Texture image failed to load: ${src}`)));
    image.src = src;
  });
}
