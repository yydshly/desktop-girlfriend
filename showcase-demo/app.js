const clamp = (value, min, max) => Math.min(Math.max(value, min), max);

document.documentElement.dataset.showcaseScript = "loading";
const useMotionVideo = new URLSearchParams(window.location.search).get("renderer") === "video";

const motionLibrary = {
  walking: "./assets/motions/walking.webm",
  wave: "./assets/motions/wave.webm",
  heart: "./assets/motions/heart.webm",
  point: "./assets/motions/point.webm",
  think: "./assets/motions/think.webm",
  sing: "./assets/motions/sing.webm",
  idleWave: "./assets/motions/idle-wave.webm",
  idleStretch: "./assets/motions/idle-stretch.webm",
  idleRead: "./assets/motions/idle-read.webm",
  idleDrink: "./assets/motions/idle-drink.webm",
};

function loadMotion(video, motionKey, loadedClassTarget = video.parentElement) {
  if (!useMotionVideo) return;
  const src = motionLibrary[motionKey];
  if (!src || !video) return;

  video.hidden = true;
  video.classList.remove("is-loaded");
  loadedClassTarget?.classList.remove("has-video");
  video.src = src;

  video.oncanplay = () => {
    video.hidden = false;
    video.classList.add("is-loaded");
    loadedClassTarget?.classList.add("has-video");
    video.play().catch(() => {});
  };
  video.onerror = () => {
    video.hidden = true;
    video.removeAttribute("src");
    video.classList.remove("is-loaded");
    loadedClassTarget?.classList.remove("has-video");
  };
  video.load();
}

function initMotionSlots() {
  document.querySelectorAll("[data-motion-video]").forEach((video) => {
    loadMotion(video, video.dataset.motionVideo);
  });

  const idleMotionKeys = {
    wave: "idleWave",
    stretch: "idleStretch",
    read: "idleRead",
    drink: "idleDrink",
  };

  document.querySelectorAll(".idle-tile").forEach((tile) => {
    loadMotion(tile.querySelector(".tile-video"), idleMotionKeys[tile.dataset.idle], tile);
  });
}

function initGestureDemo() {
  const card = document.querySelector(".gesture-card");
  const avatar = card.querySelector(".gesture-avatar");
  const video = card.querySelector(".gesture-video");
  const buttons = card.querySelectorAll("[data-gesture]");

  window.setGestureAction = (gesture) => {
    const button = card.querySelector(`[data-gesture="${gesture}"]`);
    if (!button) return false;
    buttons.forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    avatar.dataset.gesture = gesture;
    loadMotion(video, gesture);
    return true;
  };

  buttons.forEach((button) => {
    button.addEventListener("click", () => {
      window.setGestureAction(button.dataset.gesture);
    });
  });
}

function initGazeDemo() {
  const scene = document.querySelector(".gaze-scene");
  const avatar = scene.querySelector(".gaze-avatar");
  const head = avatar.querySelector(".head");
  const eyes = avatar.querySelectorAll(".eye");
  const cursor = scene.querySelector(".cursor-proxy");
  const line = scene.querySelector(".gaze-line");

  scene.addEventListener("pointermove", (event) => {
    const rect = scene.getBoundingClientRect();
    const x = (event.clientX - rect.left) / rect.width;
    const y = (event.clientY - rect.top) / rect.height;
    const dx = clamp((x - 0.66) * 2, -1, 1);
    const dy = clamp((y - 0.44) * 2, -1, 1);

    cursor.style.left = `${x * 100}%`;
    cursor.style.top = `${y * 100}%`;
    avatar.style.transform = `translateX(-50%) scale(1.24) rotate(${dx * 4}deg)`;
    head.style.transform = `translate(${dx * 4}px, ${dy * 3}px)`;
    eyes.forEach((eye) => {
      eye.style.transform = `translate(${dx * 5}px, ${dy * 4}px)`;
    });

    const lineStartX = x * 100;
    const lineStartY = y * 100;
    const targetX = 66;
    const targetY = 37;
    const angle = Math.atan2(targetY - lineStartY, targetX - lineStartX) * (180 / Math.PI);
    const distance = Math.hypot(targetX - lineStartX, targetY - lineStartY);
    line.style.left = `${lineStartX}%`;
    line.style.top = `${lineStartY}%`;
    line.style.width = `${distance}%`;
    line.style.transform = `rotate(${angle}deg)`;
  });
}

function makeParticles(canvas, preset) {
  const ctx = canvas.getContext("2d");
  const particles = [];
  const colors = {
    happy: ["#ffd36b", "#fff3a5", "#ff9d73"],
    calm: ["#72e6c1", "#b8fff0", "#8ec9ff"],
    excited: ["#ff8df4", "#b783ff", "#ffd36b"],
    sad: ["#6eb7ff", "#8cc7d8", "#d5e7ff"],
  }[preset];
  const count = preset === "excited" ? 42 : 28;

  function resetParticle(particle) {
    particle.x = Math.random() * canvas.width;
    particle.y = Math.random() * canvas.height;
    particle.size = 1.4 + Math.random() * 3.6;
    particle.speed = 0.35 + Math.random() * 0.9;
    particle.alpha = 0.35 + Math.random() * 0.65;
    particle.color = colors[Math.floor(Math.random() * colors.length)];
    particle.drift = -0.45 + Math.random() * 0.9;
  }

  function resize() {
    const rect = canvas.getBoundingClientRect();
    canvas.width = Math.max(1, Math.floor(rect.width * window.devicePixelRatio));
    canvas.height = Math.max(1, Math.floor(rect.height * window.devicePixelRatio));
    particles.forEach(resetParticle);
  }

  for (let index = 0; index < count; index += 1) {
    const particle = {};
    particles.push(particle);
  }

  resize();
  window.addEventListener("resize", resize);

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    particles.forEach((particle) => {
      const direction = preset === "sad" ? 1 : -1;
      particle.y += particle.speed * direction * window.devicePixelRatio;
      particle.x += particle.drift * window.devicePixelRatio;

      if (particle.y < -20 || particle.y > canvas.height + 20) {
        resetParticle(particle);
        particle.y = preset === "sad" ? -10 : canvas.height + 10;
      }

      ctx.globalAlpha = particle.alpha;
      ctx.fillStyle = particle.color;
      ctx.beginPath();
      ctx.arc(particle.x, particle.y, particle.size * window.devicePixelRatio, 0, Math.PI * 2);
      ctx.fill();
    });
    ctx.globalAlpha = 1;
    requestAnimationFrame(draw);
  }

  draw();
}

function initEmotionParticles() {
  document.querySelectorAll(".emotion-panel").forEach((panel) => {
    makeParticles(panel.querySelector("canvas"), panel.dataset.emotion);
    panel.addEventListener("click", () => {
      window.setEmotionState(panel.dataset.emotion);
    });
  });

  window.setEmotionState = (emotion) => {
    const panel = document.querySelector(`.emotion-panel[data-emotion="${emotion}"]`);
    if (!panel) return false;
    document.querySelectorAll(".emotion-panel").forEach((item) => item.classList.remove("active"));
    panel.classList.add("active");
    return true;
  };
}

function initWaveform() {
  const card = document.querySelector(".sing-card");
  const canvas = card.querySelector(".wave-canvas");
  const ctx = canvas.getContext("2d");
  let paused = false;
  let tick = 0;

  function resize() {
    const rect = canvas.getBoundingClientRect();
    canvas.width = Math.max(1, Math.floor(rect.width * window.devicePixelRatio));
    canvas.height = Math.max(1, Math.floor(rect.height * window.devicePixelRatio));
  }

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const mid = canvas.height * 0.72;
    ctx.lineWidth = 2 * window.devicePixelRatio;
    ctx.strokeStyle = "rgba(244, 111, 238, 0.92)";
    ctx.shadowColor = "#f46fee";
    ctx.shadowBlur = 16 * window.devicePixelRatio;
    ctx.beginPath();

    for (let x = 0; x < canvas.width; x += 8 * window.devicePixelRatio) {
      const amplitude = paused ? 8 : 20 + Math.sin(tick * 0.05 + x * 0.015) * 12;
      const y = mid + Math.sin(x * 0.04 + tick * 0.09) * amplitude * window.devicePixelRatio;
      if (x === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }

    ctx.stroke();
    if (!paused) tick += 1;
    requestAnimationFrame(draw);
  }

  resize();
  window.addEventListener("resize", resize);
  card.querySelector(".play-toggle").addEventListener("click", (event) => {
    paused = !paused;
    window.setSingingActive(!paused);
  });
  window.setSingingActive = (active) => {
    paused = !active;
    card.classList.toggle("paused", paused);
    card.querySelector(".play-toggle").textContent = paused ? "播放" : "暂停";
    return true;
  };
  draw();
}

function initIdleDemo() {
  document.querySelectorAll(".idle-tile").forEach((tile) => {
    tile.addEventListener("click", () => {
      window.setIdleAction(tile.dataset.idle);
    });
  });

  window.setIdleAction = (idle) => {
    const tile = document.querySelector(`.idle-tile[data-idle="${idle}"]`);
    if (!tile) return false;
    document.querySelectorAll(".idle-tile").forEach((item) => item.classList.remove("active"));
    tile.classList.add("active");
    return true;
  };
}

function initActionDispatcher() {
  const dispatch = (event) => {
    if (!event || event.type !== "companion.action") return false;
    let handled = false;

    if (event.emotion) {
      handled = window.setEmotionState?.(event.emotion) || handled;
    }

    if (["wave", "heart", "point", "think"].includes(event.action)) {
      handled = window.setGestureAction?.(event.action) || handled;
    }

    if (event.action === "sing") {
      handled = window.setSingingActive?.(true) || handled;
    }

    const idleMap = {
      idleWave: "wave",
      idleStretch: "stretch",
      idleRead: "read",
      idleDrink: "drink",
    };
    if (idleMap[event.action]) {
      handled = window.setIdleAction?.(idleMap[event.action]) || handled;
    }

    document.documentElement.dataset.lastCompanionAction = event.action || "";
    document.documentElement.dataset.lastCompanionEmotion = event.emotion || "";
    return handled;
  };

  window.dispatchCompanionAction = dispatch;
  document.addEventListener("companion-action", (event) => {
    dispatch(event.detail);
  });
}

try {
  initGestureDemo();
  initMotionSlots();
  initGazeDemo();
  initEmotionParticles();
  initWaveform();
  initIdleDemo();
  initActionDispatcher();
  document.documentElement.dataset.showcaseScript = "ready";
} catch (error) {
  document.documentElement.dataset.showcaseScript = "error";
  document.documentElement.dataset.showcaseError = error instanceof Error ? error.message : String(error);
  throw error;
}
