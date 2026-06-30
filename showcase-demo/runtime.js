const stage = document.querySelector(".stage");
const companion = document.querySelector(".companion");
const speechLine = document.querySelector(".speech-line");
const logList = document.querySelector("#event-log");
const readoutEmotion = document.querySelector("#readout-emotion");
const readoutAction = document.querySelector("#readout-action");
const readoutSpeaking = document.querySelector("#readout-speaking");
const canvas = document.querySelector(".emotion-canvas");
const ctx = canvas.getContext("2d");

const state = { emotion: "calm", action: "idle", speaking: false };
const particles = [];
const emotionColors = {
  happy: ["#ffd36b", "#fff0a8", "#ff9f7a"],
  calm: ["#8de8cf", "#9fcfff", "#d7fff5"],
  excited: ["#ff8df2", "#c891ff", "#ffd36b"],
  sad: ["#74b7ff", "#b9d4e8", "#e3f1ff"],
};

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
  const colors = emotionColors[state.emotion] || emotionColors.calm;
  const direction = state.emotion === "sad" ? 1 : -1;
  const density = state.emotion === "excited" ? 1 : state.emotion === "calm" ? 0.46 : 0.72;

  particles.forEach((particle, index) => {
    if (index / particles.length > density) return;
    particle.y += particle.speed * direction;
    particle.x += particle.drift;
    if (particle.y < -20 || particle.y > canvas.height + 20) {
      resetParticle(particle);
      particle.y = direction < 0 ? canvas.height + 10 : -10;
    }
    ctx.globalAlpha = particle.alpha;
    ctx.fillStyle = colors[index % colors.length];
    ctx.beginPath();
    ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
    ctx.fill();
  });
  ctx.globalAlpha = 1;
  requestAnimationFrame(drawParticles);
}

function updateReadout() {
  readoutEmotion.textContent = state.emotion;
  readoutAction.textContent = state.action;
  readoutSpeaking.textContent = String(state.speaking);
}

function logEvent(message) {
  const item = document.createElement("li");
  const time = new Date().toLocaleTimeString("zh-CN", { hour12: false });
  item.textContent = `${time}  ${message}`;
  logList.prepend(item);
  while (logList.children.length > 8) logList.lastElementChild.remove();
}

function setActiveButton(groupSelector, value, attribute) {
  document.querySelectorAll(groupSelector).forEach((button) => {
    button.classList.toggle("active", button.dataset[attribute] === value);
  });
}

function applyState(nextState, source = "manual") {
  Object.assign(state, nextState);
  stage.dataset.emotion = state.emotion;
  stage.dataset.action = state.action;
  stage.dataset.speaking = String(state.speaking);
  setActiveButton("[data-emotion]", state.emotion, "emotion");
  setActiveButton("[data-action]", state.action, "action");
  updateReadout();

  const lineByAction = {
    idle: "我在这里，等你的状态事件。",
    think: "让我想一下，这件事有几个可能方向。",
    wave: "嗨，我收到你的消息啦。",
    sing: "我先用占位口型表现唱歌状态。",
    lookAtCursor: "我会看向你的鼠标位置。",
  };
  speechLine.textContent = lineByAction[state.action] || "状态已更新。";
  logEvent(`${source}: emotion=${state.emotion}, action=${state.action}, speaking=${state.speaking}`);
}

function dispatchCompanionAction(event) {
  if (!event || event.type !== "companion.action") return false;
  applyState({
    emotion: event.emotion || state.emotion,
    action: event.action || state.action,
    speaking: Boolean(event.speaking),
  }, event.source || "event");
  return true;
}

function initControls() {
  document.querySelectorAll("[data-emotion]").forEach((button) => {
    button.addEventListener("click", () => applyState({ emotion: button.dataset.emotion }, "emotion-button"));
  });
  document.querySelectorAll("[data-action]").forEach((button) => {
    button.addEventListener("click", () => {
      const action = button.dataset.action;
      applyState({ action, speaking: action === "sing" }, "action-button");
    });
  });

  const presets = {
    greeting: { emotion: "happy", action: "wave", speaking: true },
    thinking: { emotion: "calm", action: "think", speaking: false },
    speaking: { emotion: "happy", action: "idle", speaking: true },
    idle: { emotion: "calm", action: "idle", speaking: false },
  };
  document.querySelectorAll("[data-preset]").forEach((button) => {
    button.addEventListener("click", () => applyState(presets[button.dataset.preset], `preset:${button.dataset.preset}`));
  });
}

function initGaze() {
  stage.addEventListener("pointermove", (event) => {
    if (state.action !== "lookAtCursor") return;
    const rect = stage.getBoundingClientRect();
    const x = (event.clientX - rect.left) / rect.width;
    const y = (event.clientY - rect.top) / rect.height;
    const dx = Math.max(-1, Math.min(1, (x - 0.5) * 2));
    const dy = Math.max(-1, Math.min(1, (y - 0.32) * 2));
    companion.style.transform = `translateX(-50%) rotate(${dx * 3.2}deg)`;
    document.querySelectorAll(".eye-glint").forEach((eye) => {
      eye.style.transform = `translate(${dx * 8}px, ${dy * 5}px)`;
    });
  });
}

window.dispatchCompanionAction = dispatchCompanionAction;
document.addEventListener("companion-action", (event) => dispatchCompanionAction(event.detail));

resizeCanvas();
initParticles();
initControls();
initGaze();
applyState(state, "boot");
drawParticles();
window.addEventListener("resize", () => {
  resizeCanvas();
  initParticles();
});
