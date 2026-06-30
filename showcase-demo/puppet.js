const stage = document.querySelector(".puppet-stage");
const puppet = document.querySelector(".avatar-puppet");
const realLayerStack = document.querySelector(".real-layer-stack");
const pupils = document.querySelectorAll(".pupil");
const mouth = document.querySelector(".mouth");
const head = document.querySelector(".head-control");
const bubble = document.querySelector(".bubble");
const logList = document.querySelector("#puppet-log");
const configOutput = document.querySelector("#config-output");
const sequenceStatus = document.querySelector("#sequence-status");
const bridgeStatus = document.querySelector("#bridge-status");
const connectBridgeButton = document.querySelector("#connect-bridge");
const disconnectBridgeButton = document.querySelector("#disconnect-bridge");
const turnReadouts = {
  id: document.querySelector("#turn-id"),
  intent: document.querySelector("#turn-intent"),
  tts: document.querySelector("#turn-tts"),
  user: document.querySelector("#turn-user"),
  response: document.querySelector("#turn-response"),
};
const canvas = document.querySelector(".fx-layer");
const ctx = canvas.getContext("2d");

const defaultCalibration = {
  eyeTop: 24.6,
  eyeLeft: 42.2,
  eyeRight: 53.9,
  mouthTop: 31.2,
  mouthLeft: 49.8,
};

const fallbackMotionPlanner = {
  version: 1,
  type: "avatar.motion-planner",
  sequences: {
    reply: [
      { delay: 0, label: "AI: 正在理解内容", event: { emotion: "calm", action: "think", mouth: "closed", gaze: "center", speaking: false, intensity: 0.5 } },
      { delay: 1200, label: "AI: 生成回复", event: { emotion: "happy", action: "speak", mouth: "medium", gaze: "cursor", speaking: true, intensity: 0.72 } },
      { delay: 3600, label: "AI: 回复完成", event: { emotion: "calm", action: "idle", mouth: "closed", gaze: "cursor", speaking: false, intensity: 0.35 } },
    ],
  },
};

const state = {
  renderer: "png-puppet",
  assetMode: "pseudo-layer fallback",
  emotion: "calm",
  action: "idle",
  mouth: "closed",
  gaze: "cursor",
  speaking: false,
  intensity: 0.45,
  calibration: { ...defaultCalibration },
  configSource: "defaults",
  plannerSource: "fallback",
  currentTurn: null,
};

const readouts = {
  renderer: document.querySelector("#r-renderer"),
  assetMode: document.querySelector("#r-asset-mode"),
  emotion: document.querySelector("#r-emotion"),
  action: document.querySelector("#r-action"),
  mouth: document.querySelector("#r-mouth"),
  gaze: document.querySelector("#r-gaze"),
};

const particles = [];
const colors = {
  happy: ["#ffd36b", "#fff0a8", "#ff9f7a"],
  calm: ["#8de8cf", "#9fcfff", "#d7fff5"],
  excited: ["#ff8df2", "#c891ff", "#ffd36b"],
  sad: ["#74b7ff", "#b9d4e8", "#e3f1ff"],
};

const lineByAction = {
  idle: "待机：呼吸、眨眼、低强度情绪粒子。",
  happy: "开心：暖色氛围，身体轻微上扬。",
  think: "思考：头部倾斜，出现思考气泡。",
  speak: "说话：自动口型，后续可接 TTS 音量或音素。",
  sing: "唱歌：身体轻摆，口型持续变化。",
  wave: "挥手：用状态事件触发短动作，随后回到待机。",
  sad: "低落：冷色粒子，整体亮度收敛。",
};

let motionPlanner = fallbackMotionPlanner;
let sequenceTimers = [];
let bridgeSocket = null;
let bridgeUrl = "ws://127.0.0.1:8765/avatar";

class PngPuppetRenderer {
  constructor() {
    this.id = "png-puppet";
    this.assetMode = "pseudo-layer fallback";
    this.layerElements = new Map();
    this.blinkTimer = 0;
    this.blinkResetTimer = 0;
    this.mouthTimer = 0;
    this.mouthFrame = 0;
  }

  applyState(nextState) {
    stage.dataset.emotion = nextState.emotion;
    stage.dataset.action = nextState.action;
    stage.dataset.speaking = String(nextState.speaking);
    puppet.dataset.assetMode = this.assetMode === "real-layers" ? "real-layers" : "pseudo";
    this.setMouth(nextState.mouth);
    this.setSpeaking(Boolean(nextState.speaking), nextState.mouth);
  }

  setMouth(shape) {
    mouth.className = `mouth mouth-${shape}`;
    puppet.dataset.mouth = shape;
    state.mouth = shape;
    readouts.mouth.textContent = shape;
  }

  setGaze(dx, dy) {
    pupils.forEach((pupil) => {
      pupil.style.transform = `translate(${dx * 7}px, ${dy * 5}px)`;
    });
    this.layerElements.get("pupil-left")?.style.setProperty("transform", `translate(${dx * 7}px, ${dy * 5}px)`);
    this.layerElements.get("pupil-right")?.style.setProperty("transform", `translate(${dx * 7}px, ${dy * 5}px)`);
    head.style.transform = `rotate(${dx * 2.2}deg) translate(${dx * 2}px, ${dy * 2}px)`;
  }

  setBlink(active) {
    puppet.dataset.blink = String(active);
  }

  startBlinkLoop() {
    window.clearInterval(this.blinkTimer);
    window.clearTimeout(this.blinkResetTimer);
    this.blinkTimer = window.setInterval(() => {
      if (this.assetMode !== "real-layers") return;
      this.setBlink(true);
      this.blinkResetTimer = window.setTimeout(() => this.setBlink(false), 130);
    }, 3600);
  }

  setSpeaking(speaking, baseShape = "closed") {
    window.clearInterval(this.mouthTimer);
    if (!speaking || this.assetMode !== "real-layers") {
      this.setMouth(baseShape);
      return;
    }

    const shapes = ["small", "medium", "large", "medium"];
    this.mouthTimer = window.setInterval(() => {
      const shape = shapes[this.mouthFrame % shapes.length];
      this.mouthFrame += 1;
      this.setMouth(shape);
    }, 140);
  }

  setCalibration(calibration) {
    const root = document.documentElement;
    root.style.setProperty("--eye-top", `${calibration.eyeTop}%`);
    root.style.setProperty("--eye-left-x", `${calibration.eyeLeft}%`);
    root.style.setProperty("--eye-right-x", `${calibration.eyeRight}%`);
    root.style.setProperty("--mouth-top", `${calibration.mouthTop}%`);
    root.style.setProperty("--mouth-left-x", `${calibration.mouthLeft}%`);
  }

  async tryLoadRealLayers(manifestUrl) {
    try {
      const response = await fetch(manifestUrl, { cache: "no-store" });
      if (!response.ok) throw new Error(`manifest HTTP ${response.status}`);
      const manifest = await response.json();
      const required = manifest.layers?.filter((layer) => layer.required !== false) || [];
      const missing = [];

      await Promise.all(required.map(async (layer) => {
        const image = new Image();
        image.decoding = "async";
        image.src = `./assets/avatar/layers/${layer.file}`;
        await image.decode().catch(() => missing.push(layer.file));
      }));

      if (missing.length > 0) {
        throw new Error(`missing layer files: ${missing.join(", ")}`);
      }

      realLayerStack.replaceChildren();
      this.layerElements.clear();

      manifest.layers.forEach((layer, index) => {
        const image = document.createElement("img");
        image.className = "real-avatar-layer";
        image.src = `./assets/avatar/layers/${layer.file}`;
        image.alt = "";
        image.dataset.layerRole = layer.role;
        image.style.zIndex = String(layer.zIndex ?? index);
        realLayerStack.append(image);
        this.layerElements.set(layer.role, image);
      });

      this.assetMode = "real-layers";
      state.assetMode = "real-layers";
      puppet.dataset.assetMode = "real-layers";
      this.startBlinkLoop();
      log(`layers: loaded ${manifest.layers.length} PNG layers`);
      return true;
    } catch (error) {
      this.assetMode = "pseudo-layer fallback";
      state.assetMode = "pseudo-layer fallback";
      puppet.dataset.assetMode = "pseudo";
      log(`layers: fallback (${error.message})`);
      return false;
    }
  }
}

const renderer = new PngPuppetRenderer();

function resizeCanvas() {
  const rect = canvas.getBoundingClientRect();
  canvas.width = Math.max(1, Math.floor(rect.width * window.devicePixelRatio));
  canvas.height = Math.max(1, Math.floor(rect.height * window.devicePixelRatio));
}

function resetParticle(particle) {
  particle.x = Math.random() * canvas.width;
  particle.y = Math.random() * canvas.height;
  particle.size = (1.4 + Math.random() * 3.2) * window.devicePixelRatio;
  particle.speed = (0.3 + Math.random() * 0.8) * window.devicePixelRatio;
  particle.drift = (-0.35 + Math.random() * 0.7) * window.devicePixelRatio;
  particle.alpha = 0.2 + Math.random() * 0.45;
}

function initParticles() {
  particles.length = 0;
  for (let index = 0; index < 64; index += 1) {
    const particle = {};
    resetParticle(particle);
    particles.push(particle);
  }
}

function drawParticles() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const palette = colors[state.emotion] || colors.calm;
  const direction = state.emotion === "sad" ? 1 : -1;
  const density = state.emotion === "excited" ? 1 : state.emotion === "calm" ? 0.42 : 0.72;

  particles.forEach((particle, index) => {
    if (index / particles.length > density) return;
    particle.y += particle.speed * direction;
    particle.x += particle.drift;

    if (particle.y < -20 || particle.y > canvas.height + 20) {
      resetParticle(particle);
      particle.y = direction < 0 ? canvas.height + 10 : -10;
    }

    ctx.globalAlpha = particle.alpha;
    ctx.fillStyle = palette[index % palette.length];
    ctx.beginPath();
    ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
    ctx.fill();
  });

  ctx.globalAlpha = 1;
  requestAnimationFrame(drawParticles);
}

function log(message) {
  const item = document.createElement("li");
  const time = new Date().toLocaleTimeString("zh-CN", { hour12: false });
  item.textContent = `${time}  ${message}`;
  logList.prepend(item);
  while (logList.children.length > 8) logList.lastElementChild.remove();
}

function setSequenceStatus(text) {
  if (sequenceStatus) sequenceStatus.textContent = text;
}

function setBridgeStatus(text) {
  if (bridgeStatus) bridgeStatus.textContent = text;
}

function active(selector, key, value) {
  document.querySelectorAll(selector).forEach((button) => {
    button.classList.toggle("active", button.dataset[key] === value);
  });
}

function updateReadouts() {
  readouts.renderer.textContent = state.renderer;
  readouts.assetMode.textContent = state.assetMode;
  readouts.emotion.textContent = state.emotion;
  readouts.action.textContent = state.action;
  readouts.mouth.textContent = state.mouth;
  readouts.gaze.textContent = state.gaze;
}

function updateDialogueTurn(turn) {
  if (!turn || typeof turn !== "object") return false;
  state.currentTurn = turn;
  turnReadouts.id.textContent = turn.turn_id ? turn.turn_id.slice(0, 8) : "-";
  turnReadouts.intent.textContent = turn.intent || "-";
  turnReadouts.tts.textContent = turn.tts_state || "-";
  turnReadouts.user.textContent = turn.user_text || "-";
  turnReadouts.response.textContent = turn.response_text || "-";
  return true;
}

function updateCalibrationView() {
  renderer.setCalibration(state.calibration);

  document.querySelectorAll("[data-calibrate]").forEach((input) => {
    input.value = state.calibration[input.dataset.calibrate];
  });

  configOutput.textContent = JSON.stringify({
    version: 1,
    renderer: state.renderer,
    assetMode: state.assetMode,
    motionPlanner: state.plannerSource,
    baseImage: "assets/reference/character-reference.png",
    nextAssetTarget: "assets/avatar/layers/*.png",
    source: state.configSource,
    anchors: {
      eyes: {
        topPercent: state.calibration.eyeTop,
        leftEyeXPercent: state.calibration.eyeLeft,
        rightEyeXPercent: state.calibration.eyeRight,
      },
      mouth: {
        topPercent: state.calibration.mouthTop,
        xPercent: state.calibration.mouthLeft,
      },
    },
  }, null, 2);
}

function applyPuppetConfig(config, source = "assets/avatar/puppet-v1.json") {
  if (!config?.anchors?.eyes || !config?.anchors?.mouth) return false;

  state.calibration = {
    eyeTop: Number(config.anchors.eyes.topPercent ?? defaultCalibration.eyeTop),
    eyeLeft: Number(config.anchors.eyes.leftEyeXPercent ?? defaultCalibration.eyeLeft),
    eyeRight: Number(config.anchors.eyes.rightEyeXPercent ?? defaultCalibration.eyeRight),
    mouthTop: Number(config.anchors.mouth.topPercent ?? defaultCalibration.mouthTop),
    mouthLeft: Number(config.anchors.mouth.xPercent ?? defaultCalibration.mouthLeft),
  };
  state.configSource = source;
  updateCalibrationView();
  log(`config: loaded ${source}`);
  return true;
}

async function loadPuppetConfig() {
  try {
    const response = await fetch("./assets/avatar/puppet-v1.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const config = await response.json();
    applyPuppetConfig(config);
  } catch (error) {
    state.configSource = "defaults";
    updateCalibrationView();
    log(`config: using defaults (${error.message})`);
  }
}

async function loadMotionPlanner() {
  try {
    const response = await fetch("./assets/avatar/motion-planner-v1.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const config = await response.json();
    if (config.type !== "avatar.motion-planner" || !config.sequences) throw new Error("invalid motion planner");
    motionPlanner = config;
    state.plannerSource = "assets/avatar/motion-planner-v1.json";
    setSequenceStatus("Motion Planner 已加载，等待 AI 状态事件。");
    log("planner: loaded assets/avatar/motion-planner-v1.json");
  } catch (error) {
    motionPlanner = fallbackMotionPlanner;
    state.plannerSource = "fallback";
    setSequenceStatus(`Motion Planner 使用内置回退：${error.message}`);
    log(`planner: using fallback (${error.message})`);
  }
  updateCalibrationView();
}

function applyState(next, source = "manual") {
  Object.assign(state, next);
  renderer.applyState(state);

  active("[data-preset]", state.action, "preset");
  active("[data-mouth]", state.mouth, "mouth");
  active("[data-gaze]", state.gaze, "gaze");
  updateReadouts();

  bubble.textContent = lineByAction[state.action] || "Puppet 状态已更新。";
  log(`${source}: renderer=${state.renderer}, emotion=${state.emotion}, action=${state.action}, mouth=${state.mouth}, gaze=${state.gaze}`);
}

const presets = {
  idle: { emotion: "calm", action: "idle", mouth: "closed", speaking: false, intensity: 0.35 },
  happy: { emotion: "happy", action: "happy", mouth: "small", speaking: false, intensity: 0.7 },
  think: { emotion: "calm", action: "think", mouth: "closed", speaking: false, intensity: 0.45 },
  speak: { emotion: "happy", action: "speak", mouth: "medium", speaking: true, intensity: 0.65 },
  sing: { emotion: "excited", action: "sing", mouth: "large", speaking: true, intensity: 0.9 },
  sad: { emotion: "sad", action: "sad", mouth: "small", speaking: false, intensity: 0.5 },
};

function playSequence(name) {
  const sequence = motionPlanner.sequences?.[name];
  if (!sequence) {
    setSequenceStatus(`Motion Planner 中没有序列：${name}`);
    log(`sequence: missing ${name}`);
    return;
  }

  sequenceTimers.forEach((timer) => window.clearTimeout(timer));
  sequenceTimers = [];
  setSequenceStatus(`播放序列：${name}`);
  log(`sequence: start ${name}`);

  sequence.forEach((step) => {
    const timer = window.setTimeout(() => {
      setSequenceStatus(step.label);
      window.dispatchPuppetAction({
        type: "avatar.state",
        version: 1,
        source: `sequence:${name}`,
        ...step.event,
      });
    }, Number(step.delay || 0));
    sequenceTimers.push(timer);
  });
}

function handleBridgeMessage(message) {
  if (!message || typeof message !== "object") return false;

  if (message.type === "avatar.state") {
    window.dispatchPuppetAction({
      source: message.source || "bridge",
      ...message,
    });
    return true;
  }

  if (message.type === "avatar.sequence") {
    playSequence(message.name || message.sequence || motionPlanner.defaultSequence || "reply");
    return true;
  }

  if (message.type === "dialogue.turn") {
    const updated = updateDialogueTurn(message.turn);
    if (updated) log(`turn: ${message.turn.intent || "unknown"} ${message.turn.tts_state || ""}`);
    return updated;
  }

  log(`bridge: ignored message type ${message.type || "unknown"}`);
  return false;
}

function connectAvatarBridge(url = bridgeUrl) {
  bridgeUrl = url;

  if (!("WebSocket" in window)) {
    setBridgeStatus("当前环境不支持 WebSocket。");
    return false;
  }

  if (bridgeSocket) {
    bridgeSocket.close();
    bridgeSocket = null;
  }

  setBridgeStatus(`正在连接：${bridgeUrl}`);
  bridgeSocket = new WebSocket(bridgeUrl);

  bridgeSocket.addEventListener("open", () => {
    setBridgeStatus(`已连接：${bridgeUrl}`);
    log(`bridge: connected ${bridgeUrl}`);
  });

  bridgeSocket.addEventListener("message", (event) => {
    try {
      const message = JSON.parse(event.data);
      const accepted = handleBridgeMessage(message);
      if (accepted) log(`bridge: received ${message.type}`);
    } catch (error) {
      log(`bridge: invalid json (${error.message})`);
    }
  });

  bridgeSocket.addEventListener("close", () => {
    setBridgeStatus(`已断开：${bridgeUrl}`);
    log("bridge: disconnected");
    bridgeSocket = null;
  });

  bridgeSocket.addEventListener("error", () => {
    setBridgeStatus(`连接失败：${bridgeUrl}`);
    log("bridge: connection error");
  });

  return true;
}

function disconnectAvatarBridge() {
  if (!bridgeSocket) {
    setBridgeStatus(`WebSocket 未连接：${bridgeUrl}`);
    return;
  }
  bridgeSocket.close();
  bridgeSocket = null;
}

document.querySelectorAll("[data-preset]").forEach((button) => {
  button.addEventListener("click", () => applyState(presets[button.dataset.preset], `preset:${button.dataset.preset}`));
});

document.querySelectorAll("[data-mouth]").forEach((button) => {
  button.addEventListener("click", () => applyState({ mouth: button.dataset.mouth, speaking: false }, "mouth"));
});

document.querySelectorAll("[data-gaze]").forEach((button) => {
  button.addEventListener("click", () => {
    const gaze = button.dataset.gaze;
    applyState({ gaze }, "gaze");
    if (gaze === "center") renderer.setGaze(0, 0);
    if (gaze === "left") renderer.setGaze(-1, 0);
    if (gaze === "right") renderer.setGaze(1, 0);
  });
});

document.querySelectorAll("[data-sequence]").forEach((button) => {
  button.addEventListener("click", () => playSequence(button.dataset.sequence));
});

connectBridgeButton?.addEventListener("click", () => connectAvatarBridge());
disconnectBridgeButton?.addEventListener("click", () => disconnectAvatarBridge());

document.querySelectorAll("[data-calibrate]").forEach((input) => {
  input.addEventListener("input", () => {
    state.calibration[input.dataset.calibrate] = Number(input.value);
    updateCalibrationView();
  });
});

document.querySelector("#reset-calibration").addEventListener("click", () => {
  state.calibration = { ...defaultCalibration };
  state.configSource = "defaults";
  updateCalibrationView();
  log("calibration: reset");
});

stage.addEventListener("pointermove", (event) => {
  if (state.gaze !== "cursor") return;
  const rect = stage.getBoundingClientRect();
  const x = (event.clientX - rect.left) / rect.width;
  const y = (event.clientY - rect.top) / rect.height;
  const dx = Math.max(-1, Math.min(1, (x - 0.5) * 2));
  const dy = Math.max(-1, Math.min(1, (y - 0.32) * 2));
  renderer.setGaze(dx, dy);
});

window.dispatchPuppetAction = (event) => {
  if (!event || event.type !== "avatar.state") return false;
  applyState({
    emotion: event.emotion || state.emotion,
    action: event.action || state.action,
    mouth: event.mouth || state.mouth,
    gaze: event.gaze || state.gaze,
    speaking: Boolean(event.speaking),
    intensity: Number(event.intensity ?? state.intensity),
  }, event.source || "event");
  return true;
};

window.playAvatarSequence = (name) => {
  playSequence(name || motionPlanner.defaultSequence || "reply");
};

window.connectAvatarBridge = connectAvatarBridge;
window.disconnectAvatarBridge = disconnectAvatarBridge;
window.handleAvatarBridgeMessage = handleBridgeMessage;

resizeCanvas();
initParticles();
updateCalibrationView();
applyState(state, "boot");
loadPuppetConfig();
loadMotionPlanner();
renderer.tryLoadRealLayers("./assets/avatar/layers/manifest.json").then(() => {
  updateCalibrationView();
  applyState(state, "asset-probe");
});
drawParticles();

window.addEventListener("resize", () => {
  resizeCanvas();
  initParticles();
});
