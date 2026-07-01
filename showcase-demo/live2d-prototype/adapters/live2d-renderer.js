import { inspectModelPackage } from "../model-package-inspector.js";
import { ensureLive2DSdk } from "../live2d-sdk-loader.js";
import { mapStateToLive2DCommands } from "../live2d-parameter-mapper.js";
import {
  AMBIENT_GESTURE_INTERVAL_MS,
  canRunPassiveBehavior,
  HOVER_REACTION_COOLDOWN_MS,
  updateAmbientGestureSchedule,
  updatePassiveBehaviorSchedule
} from "../passive-behavior-scheduler.js";
import { sanitizeMotionBindings } from "../motion-bindings.js";

export class Live2DRenderer {
  constructor(canvas, options = {}) {
    this.canvas = canvas;
    this.ctx = null;
    this.modelUrl = options.modelUrl || "";
    this.allowTextureFallback = options.allowTextureFallback !== false;
    this.onStatusChange = options.onStatusChange || (() => {});
    this.motionBindings = options.motionBindings || {};
    this.placementProfile = options.placementProfile || {};
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
    this.lastCommands = mapStateToLive2DCommands({}, { x: 0, y: 0 }, this.placementProfile);
    this.lastMotionKey = "";
    this.lastExpressionKey = "";
    this.activeExpression = "";
    this.activeMotion = { group: "", index: 0, source: "" };
    this.raf = 0;
    this.idleMotionIndex = 0;
    this.nextIdleMotionAt = 0;
    this.returnToIdleAt = 0;
    this.lastMotionPlayedAt = -Infinity;
    this.pointerReaction = { startedAt: 0, x: 0, y: 0 };
    this.hasPointerInput = false;
    this.hoverDwellStartedAt = 0;
    this.nextHoverReactionAt = 0;
    this.nextAmbientGestureAt = Infinity;
    this.ambientGestureIndex = 0;
    this.passiveSuppressedUntil = 0;
    this.behaviorEvents = [];
  }

  start() {
    this.lastCommands = mapStateToLive2DCommands({}, { x: 0, y: 0 }, this.placementProfile);
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
    this.hasPointerInput = true;
    this.targetPointer = { x, y };
    this.draw();
  }

  triggerPointerReaction(x = this.pointer.x, y = this.pointer.y, now = performance.now()) {
    this.pointerReaction = {
      startedAt: now,
      x: clampUnit(Number(x ?? 0)),
      y: clampUnit(Number(y ?? 0))
    };
    this.hasPointerInput = true;
    this.hoverDwellStartedAt = 0;
    this.nextHoverReactionAt = now + HOVER_REACTION_COOLDOWN_MS;
    this.passiveSuppressedUntil = Math.max(this.passiveSuppressedUntil, now + TAP_PASSIVE_SUPPRESSION_MS);
    this.recordBehaviorEvent("pointer.tap", {
      x: this.pointerReaction.x,
      y: this.pointerReaction.y
    }, now);
    this.targetPointer = { x: this.pointerReaction.x, y: this.pointerReaction.y };
    this.applyLive2DPlacement();
    this.applyLive2DCommands();
    this.draw();
  }

  applyState(nextState) {
    const now = performance.now();
    this.currentState = nextState;
    this.lastCommands = mapStateToLive2DCommands(nextState, this.pointer, this.placementProfile);
    this.applyLive2DCommands();
    this.applyLive2DExpression();
    this.playLive2DMotion();
    this.scheduleReturnToIdle(now);
    this.suppressPassiveBehaviorForState(now);
    this.draw();
    return this.lastCommands;
  }

  getLastCommands() {
    return this.lastCommands;
  }

  setMotionBindings(bindings = {}) {
    this.motionBindings = sanitizeMotionBindings(bindings);
    this.emitStatus();
  }

  setPlacementProfile(profile = {}) {
    this.placementProfile = profile || {};
    this.applyLive2DPlacement();
    this.emitStatus();
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
      this.applyLive2DPlacement(live2dModel);
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

  applyLive2DPlacement(model = this.live2dModel) {
    if (!model) {
      return null;
    }
    const placement = calculateLive2DPlacement(
      { width: this.canvas.width, height: this.canvas.height },
      getUnscaledLive2DModelSize(model),
      this.placementProfile
    );
    const followOffset = calculatePointerFollowOffset(
      { width: this.canvas.width, height: this.canvas.height },
      this.pointer,
      this.placementProfile
    );
    const reaction = calculatePointerReactionEffect(this.pointerReaction, performance.now());
    model.scale.set(roundTo(placement.scale * reaction.scaleMultiplier, 3));
    model.position.set(
      placement.x + followOffset.x + reaction.offsetX,
      placement.y + followOffset.y + reaction.offsetY
    );
    return {
      ...placement,
      scale: roundTo(placement.scale * reaction.scaleMultiplier, 3),
      x: roundTo(placement.x + followOffset.x + reaction.offsetX, 3),
      y: roundTo(placement.y + followOffset.y + reaction.offsetY, 3),
      followOffset,
      reaction
    };
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
      const followOffset = calculatePointerFollowOffset(
        { width: w, height: h },
        this.pointer,
        this.placementProfile
      );
      const reaction = calculatePointerReactionEffect(this.pointerReaction, performance.now());
      const reactedW = drawW * reaction.scaleMultiplier;
      const reactedH = drawH * reaction.scaleMultiplier;
      ctx.drawImage(
        this.previewImage,
        (w - reactedW) / 2 + followOffset.x + reaction.offsetX,
        (h - reactedH) / 2 + followOffset.y + reaction.offsetY,
        reactedW,
        reactedH
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

    const now = performance.now();
    const parameters = calculateAnimatedLive2DParameters(
      mergeAdapterParameters(this.lastCommands.parameters, this.currentState, this.lastCommands),
      {
        ...this.lastCommands,
        pointerReaction: calculatePointerReactionEffect(this.pointerReaction, now)
      },
      now
    );

    Object.entries(parameters).forEach(([id, value]) => {
      coreModel.setParameterValueById(id, value);
    });
  }

  startParameterLoop() {
    if (this.raf || typeof requestAnimationFrame !== "function") {
      return;
    }

    const startAt = performance.now();
    this.nextAmbientGestureAt = startAt + getAmbientGestureIntervalMs(this.placementProfile);

    const frame = () => {
      const now = performance.now();
      this.updateSmoothedPointer();
      this.advancePassiveBehavior(now);
      this.applyLive2DPlacement();
      this.applyLive2DCommands();
      this.applyLive2DExpression();
      this.advanceReturnToIdle(now);
      this.advanceIdleMotion(now);
      this.raf = requestAnimationFrame(frame);
    };
    this.raf = requestAnimationFrame(frame);
  }

  updateSmoothedPointer() {
    this.smoothedPointer = smoothPointer(this.smoothedPointer, this.targetPointer, 0.18);
    this.pointer = this.smoothedPointer;
    this.lastCommands = mapStateToLive2DCommands(this.currentState, this.pointer, this.placementProfile);
  }

  advancePassiveBehavior(now) {
    const schedule = updatePassiveBehaviorSchedule({
      now,
      pointer: this.pointer,
      command: this.lastCommands,
      hasPointerInput: this.hasPointerInput,
      activeReaction: calculatePointerReactionEffect(this.pointerReaction, now).active,
      hoverDwellStartedAt: this.hoverDwellStartedAt,
      nextHoverReactionAt: this.nextHoverReactionAt,
      nextAmbientGestureAt: this.nextAmbientGestureAt,
      ambientGestureIndex: this.ambientGestureIndex,
      ambientIntervalMs: getAmbientGestureIntervalMs(this.placementProfile),
      passiveSuppressedUntil: this.passiveSuppressedUntil
    });
    this.hoverDwellStartedAt = schedule.hoverDwellStartedAt;
    this.nextHoverReactionAt = schedule.nextHoverReactionAt;
    this.nextAmbientGestureAt = schedule.nextAmbientGestureAt;
    this.ambientGestureIndex = schedule.ambientGestureIndex;
    if (!schedule.reaction) {
      return;
    }

    this.pointerReaction = schedule.reaction;
    this.recordBehaviorEvent(schedule.eventType, schedule.eventDetail, now);
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

  advanceAmbientGesture(now) {
    const schedule = updateAmbientGestureSchedule({
      now,
      command: this.lastCommands,
      activeReaction: calculatePointerReactionEffect(this.pointerReaction, now).active,
      nextAmbientGestureAt: this.nextAmbientGestureAt,
      ambientGestureIndex: this.ambientGestureIndex,
      intervalMs: getAmbientGestureIntervalMs(this.placementProfile)
    });
    this.nextAmbientGestureAt = schedule.nextAmbientGestureAt;
    this.ambientGestureIndex = schedule.ambientGestureIndex;
    if (!schedule.reaction) {
      return;
    }

    this.pointerReaction = schedule.reaction;
    this.recordBehaviorEvent("ambient.gesture", schedule.eventDetail, now);
  }

  scheduleReturnToIdle(now) {
    const delay = getReturnToIdleDelayMs(this.lastCommands);
    this.returnToIdleAt = delay > 0 ? now + delay : 0;
  }

  suppressPassiveBehaviorForState(now) {
    const delay = getReturnToIdleDelayMs(this.lastCommands);
    if (delay <= 0) {
      return;
    }
    this.passiveSuppressedUntil = Math.max(
      this.passiveSuppressedUntil,
      now + delay + EXPRESSIVE_PASSIVE_SUPPRESSION_TAIL_MS
    );
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
    this.lastCommands = mapStateToLive2DCommands(this.currentState, this.pointer, this.placementProfile);
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

    const motion = options.override || resolveAdapterMotion(this.currentState) || mapCommandToModelMotion(
      this.lastCommands,
      this.model?.motionGroupCounts,
      this.motionBindings
    );
    const motionKey = `${motion.group}:${motion.index}:${motion.source}`;
    if (!options.force && motionKey === this.lastMotionKey) {
      return;
    }

    this.live2dModel.motion(motion.group, motion.index);
    this.lastMotionPlayedAt = now;
    this.lastMotionKey = motionKey;
    this.activeMotion = motion;
    this.recordBehaviorEvent("motion.play", {
      group: motion.group,
      index: motion.index,
      source: motion.source
    }, now);
    this.emitStatus();
  }

  playMotionProbe(group, index) {
    if (!this.live2dModel?.motion) {
      return;
    }
    const motion = {
      group: String(group || "Idle"),
      index: Math.max(0, Math.floor(Number(index || 0))),
      source: "manual.motion-probe"
    };
    this.live2dModel.motion(motion.group, motion.index);
    const now = performance.now();
    this.lastMotionPlayedAt = now;
    this.lastMotionKey = `${motion.group}:${motion.index}:${motion.source}`;
    this.activeMotion = motion;
    this.recordBehaviorEvent("motion.probe", {
      group: motion.group,
      index: motion.index,
      source: motion.source
    }, now);
    this.emitStatus();
  }

  applyLive2DExpression() {
    if (!this.live2dModel?.expression) {
      return;
    }

    const expression = resolveSupportedExpression(
      resolveAdapterExpression(this.currentState) || this.lastCommands.expression || "",
      this.model?.expressionNames
    );
    if (!expression || expression === this.lastExpressionKey) {
      return;
    }

    this.live2dModel.expression(expression);
    this.lastExpressionKey = expression;
    this.activeExpression = expression;
    this.recordBehaviorEvent("expression.apply", { expression });
    this.emitStatus();
  }

  recordBehaviorEvent(type, detail = {}, now = performance.now()) {
    this.behaviorEvents = [
      {
        type,
        at: Math.round(now),
        detail
      },
      ...this.behaviorEvents
    ].slice(0, MAX_BEHAVIOR_EVENTS);
  }

  emitStatus() {
    this.onStatusChange({
      loadState: this.loadState,
      loadError: this.loadError,
      modelUrl: this.modelUrl,
      hasLive2DModel: Boolean(this.live2dModel),
      activeMotion: this.activeMotion,
      activeExpression: this.activeExpression,
      modelCapabilities: getModelCapabilities(this.model),
      commandDiagnostics: getCommandDiagnostics(this.lastCommands, this.model, this.motionBindings),
      modelAdapterCommands: getModelAdapterCommandDiagnostics(this.currentState),
      motionBindings: this.motionBindings,
      behaviorEvents: this.behaviorEvents
    });
  }
}

const DEFAULT_IDLE_MOTION_COUNT = 9;
const IDLE_MOTION_INTERVAL_MS = 6500;
const MOTION_COOLDOWN_MS = 650;
const EXPRESSIVE_RETURN_TO_IDLE_MS = 4200;
const EXPRESSIVE_PASSIVE_SUPPRESSION_TAIL_MS = 900;
const TAP_PASSIVE_SUPPRESSION_MS = 1400;
const MAX_BEHAVIOR_EVENTS = 12;

function getLive2DModelFactory(PIXI) {
  const Live2DModel = PIXI?.live2d?.Live2DModel;
  if (!Live2DModel?.from) {
    throw new Error("PIXI Live2D Cubism 4 model loader is missing.");
  }
  return Live2DModel;
}

function getAmbientGestureIntervalMs(placementProfile = {}) {
  const interval = Number(placementProfile.ambientGestureIntervalMs ?? AMBIENT_GESTURE_INTERVAL_MS);
  return Number.isFinite(interval) && interval > 0 ? interval : AMBIENT_GESTURE_INTERVAL_MS;
}

function getUnscaledLive2DModelSize(model) {
  const internalWidth = readPositiveNumber(model?.internalModel?.width)
    ?? readPositiveNumber(model?.internalModel?.originalWidth);
  const internalHeight = readPositiveNumber(model?.internalModel?.height)
    ?? readPositiveNumber(model?.internalModel?.originalHeight);
  if (internalWidth && internalHeight) {
    return { width: internalWidth, height: internalHeight };
  }

  const scaleX = readPositiveNumber(model?.scale?.x) ?? 1;
  const scaleY = readPositiveNumber(model?.scale?.y) ?? 1;
  return {
    width: readPositiveNumber(Number(model?.width) / scaleX) ?? readPositiveNumber(model?.width) ?? 1,
    height: readPositiveNumber(Number(model?.height) / scaleY) ?? readPositiveNumber(model?.height) ?? 1
  };
}

function readPositiveNumber(value) {
  const numeric = Number(value);
  return Number.isFinite(numeric) && numeric > 0 ? numeric : null;
}

export function calculateLive2DPlacement(canvasSize, modelSize, placementProfile = {}) {
  const safeModelWidth = Math.max(1, modelSize.width);
  const safeModelHeight = Math.max(1, modelSize.height);
  const baseScale = Math.min(
    canvasSize.width / safeModelWidth * 0.92,
    canvasSize.height / safeModelHeight * 1.08
  );
  const scaleMultiplier = Number(placementProfile.scaleMultiplier ?? 1);
  const xOffsetRatio = Number(placementProfile.xOffsetRatio ?? 0);
  const yRatio = Number(placementProfile.yRatio ?? 0.55);
  const scale = baseScale * (Number.isFinite(scaleMultiplier) ? scaleMultiplier : 1);

  return {
    scale: roundTo(scale, 3),
    x: roundTo(canvasSize.width / 2 + canvasSize.width * (Number.isFinite(xOffsetRatio) ? xOffsetRatio : 0), 3),
    y: roundTo(canvasSize.height * (Number.isFinite(yRatio) ? yRatio : 0.55), 3)
  };
}

export function calculatePointerFollowOffset(canvasSize, pointer = {}, placementProfile = {}) {
  const x = clampUnit(Number(pointer.x ?? 0));
  const y = clampUnit(Number(pointer.y ?? 0));
  const strength = Math.min(1, Math.hypot(x, y));
  const xRatio = Number(placementProfile.pointerFollowXRatio ?? 0.0075);
  const yRatio = Number(placementProfile.pointerFollowYRatio ?? 0.005);
  const enabled = placementProfile.pointerFollow !== false;

  if (!enabled) {
    return { x: 0, y: 0, strength: 0 };
  }

  return {
    x: roundTo(canvasSize.width * x * (Number.isFinite(xRatio) ? xRatio : 0.055), 3),
    y: roundTo(canvasSize.height * y * (Number.isFinite(yRatio) ? yRatio : 0.028), 3),
    strength: roundTo(strength, 3)
  };
}

export function calculatePointerReactionEffect(reaction = {}, now = 0) {
  const startedAt = Number(reaction.startedAt ?? 0);
  const elapsed = now - startedAt;
  const durationMs = Number(reaction.durationMs ?? 560);
  if (!startedAt || elapsed < 0 || elapsed > durationMs) {
    return {
      active: false,
      envelope: 0,
      x: 0,
      y: 0,
      offsetX: 0,
      offsetY: 0,
      scaleMultiplier: 1
    };
  }

  const x = clampUnit(Number(reaction.x ?? 0));
  const y = clampUnit(Number(reaction.y ?? 0));
  const progress = elapsed / durationMs;
  const envelope = Math.sin(Math.PI * progress);
  return {
    active: true,
    envelope: roundTo(envelope, 3),
    x,
    y,
    offsetX: roundTo(x * 24 * envelope, 3),
    offsetY: roundTo(y * 14 * envelope - 10 * envelope, 3),
    scaleMultiplier: roundTo(1 + 0.028 * envelope, 3)
  };
}

function roundTo(value, digits) {
  const factor = 10 ** digits;
  return Math.round(value * factor) / factor;
}

function resolveAdapterMotion(state = {}) {
  const command = state.modelCommands?.motion;
  if (!command?.group) {
    return null;
  }
  return {
    group: String(command.group),
    index: Math.max(0, Math.floor(Number(command.index ?? 0))),
    source: `model-adapter:${command.action || "unknown"}`
  };
}

function resolveAdapterExpression(state = {}) {
  const expression = state.modelCommands?.expression?.name;
  return typeof expression === "string" ? expression.trim() : "";
}

function mergeAdapterParameters(parameters = {}, state = {}, command = {}) {
  const adapterParameters = state.modelCommands?.parameters;
  if (!adapterParameters) {
    return parameters;
  }

  const next = { ...parameters };
  const aliases = command.parameterDiagnostics || {};
  const mouth = readUnitParameter(adapterParameters.mouth);
  if (mouth !== null) {
    writeAliasedParameter(next, aliases.mouthOpen, mouth, "ParamMouthOpenY");
  }

  const intensity = readUnitParameter(adapterParameters.intensity);
  if (intensity !== null) {
    writeAliasedParameter(next, aliases.breath, 0.5 + intensity * 0.5, "ParamBreath");
  }

  return next;
}

function writeAliasedParameter(parameters, alias = null, value, fallbackId) {
  const id = typeof alias?.id === "string" && alias.id.trim() ? alias.id.trim() : fallbackId;
  const min = Number.isFinite(Number(alias?.min)) ? Number(alias.min) : 0;
  const max = Number.isFinite(Number(alias?.max)) ? Number(alias.max) : 1;
  const scale = Number.isFinite(Number(alias?.scale)) ? Number(alias.scale) : 1;
  const scaled = Number(value) * scale;
  const next = alias?.invert ? -scaled : scaled;
  parameters[id] = roundToThree(Math.min(max, Math.max(min, next)));
}

function readUnitParameter(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return null;
  }
  return Math.min(1, Math.max(0, number));
}

export function mapCommandToModelMotion(command = {}, motionGroupCounts = null, motionBindings = {}) {
  const motion = command.motion || "idle";
  const binding = resolveMotionBinding(motion, motionBindings, motionGroupCounts);
  if (binding) {
    return { ...binding, source: `${motion}-binding` };
  }

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

function resolveMotionBinding(motion, motionBindings = {}, motionGroupCounts = null) {
  const binding = motionBindings?.[motion];
  if (!binding) {
    return null;
  }
  const group = String(binding.group || "");
  const index = Math.max(0, Math.floor(Number(binding.index ?? 0)));
  if (!group || !hasMotionIndex(motionGroupCounts, group, index)) {
    return null;
  }
  return { group, index };
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

function hasMotionIndex(motionGroupCounts = null, group, index) {
  if (!motionGroupCounts) {
    return group === "TapBody" ? index === 0 : group === "Idle" && index >= 0 && index < DEFAULT_IDLE_MOTION_COUNT;
  }
  const count = Number(motionGroupCounts[group] ?? 0);
  return Number.isFinite(count) && index >= 0 && index < count;
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
  return canRunPassiveBehavior(command);
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

export function getCommandDiagnostics(command = {}, model = null, motionBindings = {}) {
  const requestedMotion = command.motion || "";
  const requestedExpression = command.expression || "";
  const resolvedExpression = resolveSupportedExpression(
    requestedExpression,
    model?.expressionNames
  );
  return {
    requestedMotion,
    requestedExpression,
    resolvedMotion: mapCommandToModelMotion(command, model?.motionGroupCounts, motionBindings),
    resolvedExpression,
    expressionSupport: getExpressionSupport(requestedExpression, resolvedExpression, model)
  };
}

function getModelAdapterCommandDiagnostics(state = {}) {
  const commands = state.modelCommands;
  if (!commands) {
    return null;
  }

  return {
    motion: formatAdapterMotionDiagnostic(commands.motion),
    expression: formatAdapterExpressionDiagnostic(commands.expression),
    parameters: formatAdapterParameterDiagnostic(commands.parameters)
  };
}

function formatAdapterMotionDiagnostic(motion = null) {
  if (!motion?.group) {
    return null;
  }
  return {
    group: String(motion.group),
    index: Math.max(0, Math.floor(Number(motion.index ?? 0))),
    action: String(motion.action || "")
  };
}

function formatAdapterExpressionDiagnostic(expression = null) {
  if (!expression) {
    return null;
  }
  return {
    name: typeof expression.name === "string" ? expression.name : "",
    semantic: typeof expression.semantic === "string" ? expression.semantic : ""
  };
}

function formatAdapterParameterDiagnostic(parameters = null) {
  if (!parameters) {
    return null;
  }
  return {
    gaze: typeof parameters.gaze === "string" && parameters.gaze.trim()
      ? parameters.gaze.trim()
      : "cursor",
    mouth: readUnitParameter(parameters.mouth) ?? 0,
    intensity: readUnitParameter(parameters.intensity) ?? 0,
    speaking: {
      active: Boolean(parameters.speaking?.active),
      source: typeof parameters.speaking?.source === "string" ? parameters.speaking.source : "idle",
      rhythm: typeof parameters.speaking?.rhythm === "string" ? parameters.speaking.rhythm : "none"
    }
  };
}

function getExpressionSupport(requestedExpression, resolvedExpression, model = null) {
  if (!requestedExpression) {
    return "none";
  }
  if (!Array.isArray(model?.expressionNames)) {
    return "unknown";
  }
  return resolvedExpression ? "available" : "missing";
}

export function calculateAnimatedLive2DParameters(parameters = {}, command = {}, now = 0) {
  const next = { ...parameters };
  const motion = command.motion || "";
  const adapterParameters = command.modelCommands?.parameters || {};
  const speakingParameter = adapterParameters.speaking || {};
  const speaking = Boolean(speakingParameter.active);
  const speakingMouth = readUnitParameter(adapterParameters.mouth);
  const pointer = normalizePointerCommand(command);
  const idleHeadScale = 1 - pointer.strength * 0.35;
  const idleEyeScale = 1 - pointer.strength * 0.7;
  const thinking = motion === "think"
    || motion === "listen"
    || command.expression === "thinking"
    || command.visualIntent === "thinking"
    || command.visualIntent === "listening";

  if (speaking) {
    if (speakingMouth !== null) {
      next.ParamMouthOpenY = roundToThree(Math.max(Number(next.ParamMouthOpenY ?? 0), speakingMouth));
    }
    next.ParamAngleX = roundParameter(
      Number(next.ParamAngleX ?? 0) + Math.sin(now / 260) * 2.2
    );
    next.ParamBodyAngleX = roundParameter(
      Number(next.ParamBodyAngleX ?? 0) + Math.sin(now / 320) * 1.4
    );
  }

  if (!speaking) {
    const breath = 0.5 + Math.sin(now / 900) * 0.08;
    next.ParamBreath = roundToThree(Math.max(Number(next.ParamBreath ?? 0.5), breath));
    next.ParamAngleZ = roundParameter(
      Number(next.ParamAngleZ ?? 0) + Math.sin(now / 1400) * 0.9 * idleHeadScale
    );
    next.ParamAngleY = roundParameter(
      Number(next.ParamAngleY ?? 0) + Math.sin(now / 2100) * 1.1 * idleHeadScale
    );
    next.ParamEyeBallX = clampRoundedParameter(
      Number(next.ParamEyeBallX ?? 0) + Math.sin(now / 1800) * 0.12 * idleEyeScale,
      -1,
      1
    );
    next.ParamEyeBallY = clampRoundedParameter(
      Number(next.ParamEyeBallY ?? 0) + Math.sin(now / 2400) * 0.06 * idleEyeScale,
      -1,
      1
    );
    next.ParamBodyAngleX = roundParameter(
      Number(next.ParamBodyAngleX ?? 0) + Math.sin(now / 1250) * 0.8 * idleHeadScale
    );
    next.ParamBodyAngleY = roundParameter(
      Number(next.ParamBodyAngleY ?? 0) + Math.sin(now / 2300) * 0.5 * idleHeadScale
    );
  }

  if (command.pointerReaction?.active) {
    const reaction = command.pointerReaction;
    next.ParamAngleX = roundParameter(
      Number(next.ParamAngleX ?? 0) + reaction.x * 5.5 * reaction.envelope
    );
    next.ParamAngleY = roundParameter(
      Number(next.ParamAngleY ?? 0) + reaction.y * -4 * reaction.envelope
    );
    next.ParamAngleZ = roundParameter(
      Number(next.ParamAngleZ ?? 0) + reaction.x * -3.5 * reaction.envelope
    );
    next.ParamBodyAngleX = roundParameter(
      Number(next.ParamBodyAngleX ?? 0) + reaction.x * 3.5 * reaction.envelope
    );
    next.ParamBodyAngleY = roundParameter(
      Number(next.ParamBodyAngleY ?? 0) + reaction.y * -2.8 * reaction.envelope
    );
  }

  if (thinking) {
    next.ParamAngleY = roundParameter(
      Number(next.ParamAngleY ?? 0) + 1.1 + Math.sin(now / 760) * 0.7
    );
    next.ParamEyeBallY = roundParameter(
      Number(next.ParamEyeBallY ?? 0) - 0.08 + Math.sin(now / 980) * 0.04
    );
    next.ParamBodyAngleX = roundParameter(
      Number(next.ParamBodyAngleX ?? 0) + Math.sin(now / 680) * 0.9
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

function clampRoundedParameter(value, min, max) {
  return roundParameter(Math.min(max, Math.max(min, value)));
}

function normalizePointerCommand(command = {}) {
  const pointer = command.pointer;
  if (!pointer || typeof pointer !== "object") {
    return { x: 0, y: 0, strength: 0 };
  }

  const x = clampUnit(Number(pointer.x ?? 0));
  const y = clampUnit(Number(pointer.y ?? 0));
  const fallbackStrength = Math.min(1, Math.hypot(x, y));
  const strength = clamp01(Number(pointer.strength ?? fallbackStrength));
  return { x, y, strength };
}

function clamp01(value) {
  if (!Number.isFinite(value)) {
    return 0;
  }
  return Math.min(1, Math.max(0, value));
}

function clampUnit(value) {
  if (!Number.isFinite(value)) {
    return 0;
  }
  return Math.min(1, Math.max(-1, value));
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
