# Live2D Model Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Live2D-first prototype path and a model-production path so the desktop girlfriend project can move from PNG demo to a real model-driven character.

**Architecture:** Keep the existing PNG puppet as a legacy protocol prototype. Add `showcase-demo/live2d-prototype` for model rendering and state mapping, and `showcase-demo/model-production` for the custom character/model asset pipeline. The first renderer must work without a real model by using an explicit placeholder adapter, then switch to a real Live2D adapter when a model is available.

**Tech Stack:** Static HTML/CSS/JavaScript, existing WebSocket avatar protocol, future Live2D Cubism Web SDK or `pixi-live2d-display`, MiniMax or other image models for character concept references, Live2D Cubism Editor for final model binding.

---

## File Structure

- Create `showcase-demo/live2d-prototype/index.html`: standalone Live2D mainline prototype page.
- Create `showcase-demo/live2d-prototype/live2d.css`: page layout, stage, controls, status panels.
- Create `showcase-demo/live2d-prototype/state-mapper.js`: maps existing `avatar.state`, `avatar.sequence`, and `dialogue.turn` messages into renderer commands.
- Create `showcase-demo/live2d-prototype/avatar-controller.js`: owns runtime state, calls renderer adapter, exposes global test helpers.
- Create `showcase-demo/live2d-prototype/live2d.js`: bootstraps the page, wires controls and WebSocket bridge.
- Create `showcase-demo/live2d-prototype/README.md`: explains how to run and what is real vs placeholder.
- Create `showcase-demo/live2d-prototype/adapters/placeholder-renderer.js`: visible non-Live2D renderer that proves state mapping before a model exists.
- Create `showcase-demo/live2d-prototype/adapters/live2d-renderer.js`: adapter boundary for future Live2D SDK integration.
- Create `showcase-demo/model-production/CHARACTER_BRIEF.md`: first custom character direction.
- Create `showcase-demo/model-production/LIVE2D_ASSET_SPEC.md`: handoff spec for illustrator/Live2D rigger.
- Create `showcase-demo/model-production/MINIMAX_PROMPTS.md`: image-generation prompts for concept art and expression sheets.
- Create `showcase-demo/model-production/MODEL_PIPELINE.md`: production steps from concept image to `.model3.json`.
- Create `showcase-demo/model-production/README.md`: overview for model asset work.

## Task 1: Create Live2D Prototype Shell

**Files:**
- Create: `showcase-demo/live2d-prototype/index.html`
- Create: `showcase-demo/live2d-prototype/live2d.css`
- Create: `showcase-demo/live2d-prototype/README.md`

- [ ] **Step 1: Create the prototype HTML**

Create `showcase-demo/live2d-prototype/index.html` with this content:

```html
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Live2D 主线原型</title>
    <link rel="stylesheet" href="./live2d.css" />
  </head>
  <body>
    <main class="app-shell">
      <section class="stage-panel">
        <div class="stage-header">
          <div>
            <p class="eyebrow">B 方案 / Live2D 主线</p>
            <h1>模型驱动原型</h1>
          </div>
          <span id="rendererMode" class="status-pill">placeholder renderer</span>
        </div>
        <div id="avatarStage" class="avatar-stage" aria-label="Live2D avatar stage">
          <canvas id="avatarCanvas" width="900" height="1200"></canvas>
        </div>
      </section>

      <aside class="control-panel">
        <section class="panel-section">
          <h2>状态控制</h2>
          <div class="button-grid">
            <button data-state="idle">待机</button>
            <button data-state="happy">开心</button>
            <button data-state="think">思考</button>
            <button data-state="sad">低落</button>
            <button data-state="comfort">安慰</button>
            <button data-state="speak">说话</button>
          </div>
        </section>

        <section class="panel-section">
          <h2>动作序列</h2>
          <div class="button-grid">
            <button data-sequence="greet">打招呼</button>
            <button data-sequence="listen">倾听</button>
            <button data-sequence="reply">回复</button>
            <button data-sequence="comfort">安慰</button>
          </div>
        </section>

        <section class="panel-section">
          <h2>桥接状态</h2>
          <div class="bridge-row">
            <input id="bridgeUrl" value="ws://127.0.0.1:8879" />
            <button id="connectBridge">连接</button>
            <button id="disconnectBridge">断开</button>
          </div>
          <pre id="stateReadout">{}</pre>
        </section>
      </aside>
    </main>

    <script type="module" src="./live2d.js"></script>
  </body>
</html>
```

- [ ] **Step 2: Create the prototype CSS**

Create `showcase-demo/live2d-prototype/live2d.css` with this content:

```css
:root {
  color-scheme: dark;
  --bg: #101418;
  --panel: #171d22;
  --panel-2: #20272d;
  --text: #f4f7f8;
  --muted: #aab5bb;
  --accent: #f2a6b3;
  --line: rgba(255, 255, 255, 0.12);
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  min-height: 100vh;
  font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
  background: radial-gradient(circle at 30% 15%, #27313a 0, #101418 38%, #080b0e 100%);
  color: var(--text);
}

button,
input {
  font: inherit;
}

.app-shell {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 360px;
  gap: 18px;
  min-height: 100vh;
  padding: 18px;
}

.stage-panel,
.control-panel {
  border: 1px solid var(--line);
  background: rgba(23, 29, 34, 0.82);
  backdrop-filter: blur(16px);
}

.stage-panel {
  display: flex;
  min-height: calc(100vh - 36px);
  flex-direction: column;
}

.stage-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 18px 20px;
  border-bottom: 1px solid var(--line);
}

.eyebrow {
  margin: 0 0 6px;
  color: var(--accent);
  font-size: 13px;
}

h1,
h2 {
  margin: 0;
  letter-spacing: 0;
}

h1 {
  font-size: 24px;
}

h2 {
  font-size: 16px;
}

.status-pill {
  border: 1px solid rgba(242, 166, 179, 0.45);
  border-radius: 999px;
  padding: 7px 10px;
  color: #ffd6dd;
  background: rgba(242, 166, 179, 0.12);
  white-space: nowrap;
}

.avatar-stage {
  position: relative;
  display: grid;
  flex: 1;
  place-items: center;
  overflow: hidden;
  background:
    linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0)),
    radial-gradient(circle at 50% 68%, rgba(242,166,179,0.18), transparent 34%);
}

#avatarCanvas {
  width: min(62vh, 72vw);
  max-width: 760px;
  height: auto;
  aspect-ratio: 3 / 4;
}

.control-panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-height: calc(100vh - 36px);
  padding: 16px;
}

.panel-section {
  display: grid;
  gap: 10px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--line);
}

.button-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

button {
  min-height: 38px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--panel-2);
  color: var(--text);
  cursor: pointer;
}

button:hover {
  border-color: rgba(242, 166, 179, 0.55);
  background: #2a333a;
}

.bridge-row {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
}

input {
  min-width: 0;
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 9px 10px;
  background: #10161a;
  color: var(--text);
}

pre {
  min-height: 220px;
  max-height: 42vh;
  overflow: auto;
  margin: 0;
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 12px;
  background: #0b0f12;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
}

@media (max-width: 900px) {
  .app-shell {
    grid-template-columns: 1fr;
  }

  .stage-panel,
  .control-panel {
    min-height: auto;
  }
}
```

- [ ] **Step 3: Create the prototype README**

Create `showcase-demo/live2d-prototype/README.md` with this content:

```markdown
# Live2D Prototype

This directory is the new B-plan mainline for the desktop girlfriend project.

The first version deliberately uses a placeholder renderer. That renderer is not the final visual target. It proves that the existing `avatar.state`, `avatar.sequence`, and `dialogue.turn` protocol can drive a model-shaped runtime before a real `.model3.json` file is available.

The intended upgrade path is:

1. Run placeholder renderer and validate state mapping.
2. Add a legally usable sample Live2D model.
3. Replace `placeholder-renderer.js` with `live2d-renderer.js` at runtime.
4. Replace sample model with custom character model.
5. Wrap the prototype in Electron for transparent desktop rendering.
```

## Task 2: Add State Mapper And Placeholder Renderer

**Files:**
- Create: `showcase-demo/live2d-prototype/state-mapper.js`
- Create: `showcase-demo/live2d-prototype/adapters/placeholder-renderer.js`
- Create: `showcase-demo/live2d-prototype/adapters/live2d-renderer.js`

- [ ] **Step 1: Create the state mapper**

Create `showcase-demo/live2d-prototype/state-mapper.js` with this content:

```javascript
const STATE_PRESETS = {
  idle: { emotion: "neutral", mouth: 0, gaze: "cursor", motion: "idle", intensity: 0.25 },
  happy: { emotion: "happy", mouth: 0.28, gaze: "cursor", motion: "happy", intensity: 0.72 },
  think: { emotion: "thinking", mouth: 0.05, gaze: "down-left", motion: "think", intensity: 0.48 },
  sad: { emotion: "sad", mouth: 0.08, gaze: "down", motion: "sad", intensity: 0.56 },
  comfort: { emotion: "soft", mouth: 0.18, gaze: "cursor", motion: "comfort", intensity: 0.68 },
  speak: { emotion: "engaged", mouth: 0.65, gaze: "cursor", motion: "reply", intensity: 0.76 }
};

const SEQUENCE_TO_STATE = {
  greet: "happy",
  listen: "think",
  reply: "speak",
  comfort: "comfort"
};

export function mapAvatarState(payload = {}) {
  const preset = STATE_PRESETS[payload.state] || STATE_PRESETS.idle;
  return {
    ...preset,
    ...payload,
    source: "avatar.state"
  };
}

export function mapAvatarSequence(payload = {}) {
  const stateName = SEQUENCE_TO_STATE[payload.name] || "idle";
  return {
    ...STATE_PRESETS[stateName],
    sequence: payload.name || "idle",
    source: "avatar.sequence"
  };
}

export function mapDialogueTurn(payload = {}) {
  const intent = payload.intent || "reply";
  const stateName = SEQUENCE_TO_STATE[intent] || (intent === "idle" ? "idle" : "speak");
  return {
    ...STATE_PRESETS[stateName],
    turn: {
      turnId: payload.turn_id || "",
      userText: payload.user_text || "",
      responseText: payload.response_text || "",
      ttsState: payload.tts_state || "none"
    },
    source: "dialogue.turn"
  };
}

export function mapBridgeMessage(message = {}) {
  if (message.type === "avatar.state") {
    return mapAvatarState(message.payload);
  }
  if (message.type === "avatar.sequence") {
    return mapAvatarSequence(message.payload);
  }
  if (message.type === "dialogue.turn") {
    return mapDialogueTurn(message.payload);
  }
  return {
    ...STATE_PRESETS.idle,
    source: message.type || "unknown"
  };
}
```

- [ ] **Step 2: Create the placeholder renderer**

Create `showcase-demo/live2d-prototype/adapters/placeholder-renderer.js` with this content:

```javascript
export class PlaceholderRenderer {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.state = {
      emotion: "neutral",
      mouth: 0,
      gaze: "cursor",
      motion: "idle",
      intensity: 0.25
    };
    this.pointer = { x: 0, y: 0 };
    this.startedAt = performance.now();
  }

  start() {
    const frame = () => {
      this.draw(performance.now());
      this.raf = requestAnimationFrame(frame);
    };
    frame();
  }

  stop() {
    cancelAnimationFrame(this.raf);
  }

  setPointer(x, y) {
    this.pointer = { x, y };
  }

  applyState(nextState) {
    this.state = { ...this.state, ...nextState };
  }

  draw(now) {
    const ctx = this.ctx;
    const w = this.canvas.width;
    const h = this.canvas.height;
    const t = (now - this.startedAt) / 1000;
    const breath = Math.sin(t * 2) * 8;
    const mood = this.getMoodColors();

    ctx.clearRect(0, 0, w, h);
    ctx.save();
    ctx.translate(w / 2, h * 0.53 + breath);

    ctx.fillStyle = "rgba(0, 0, 0, 0.25)";
    ctx.beginPath();
    ctx.ellipse(0, h * 0.34, 180, 34, 0, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = mood.sweater;
    this.roundRect(ctx, -150, 80, 300, 360, 70);
    ctx.fill();

    ctx.fillStyle = "#f8d7ca";
    ctx.beginPath();
    ctx.ellipse(0, -120, 128, 152, 0, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = "#6b3f34";
    ctx.beginPath();
    ctx.ellipse(0, -162, 152, 138, 0, Math.PI * 1.02, Math.PI * 2.02);
    ctx.fill();

    ctx.fillStyle = "#765047";
    ctx.beginPath();
    ctx.ellipse(-110, -38, 58, 250, -0.18, 0, Math.PI * 2);
    ctx.ellipse(112, -36, 58, 250, 0.18, 0, Math.PI * 2);
    ctx.fill();

    this.drawEye(ctx, -48, -124);
    this.drawEye(ctx, 48, -124);
    this.drawMouth(ctx, 0, -54);

    if (this.state.emotion === "happy" || this.state.emotion === "soft") {
      ctx.fillStyle = "rgba(242, 118, 142, 0.24)";
      ctx.beginPath();
      ctx.ellipse(-72, -82, 26, 14, 0, 0, Math.PI * 2);
      ctx.ellipse(72, -82, 26, 14, 0, 0, Math.PI * 2);
      ctx.fill();
    }

    ctx.restore();
  }

  drawEye(ctx, x, y) {
    const lookX = Math.max(-8, Math.min(8, this.pointer.x * 12));
    const lookY = Math.max(-5, Math.min(5, this.pointer.y * 8));
    ctx.fillStyle = "#fff8f5";
    ctx.beginPath();
    ctx.ellipse(x, y, 28, 17, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "#4a2c27";
    ctx.beginPath();
    ctx.ellipse(x + lookX, y + lookY, 10, 13, 0, 0, Math.PI * 2);
    ctx.fill();
  }

  drawMouth(ctx, x, y) {
    const open = Math.max(2, this.state.mouth * 34);
    ctx.strokeStyle = "#8f4a54";
    ctx.fillStyle = "rgba(105, 39, 49, 0.72)";
    ctx.lineWidth = 4;
    ctx.beginPath();
    ctx.ellipse(x, y, 20, open, 0, 0, Math.PI * 2);
    if (open > 7) {
      ctx.fill();
    } else {
      ctx.stroke();
    }
  }

  getMoodColors() {
    if (this.state.emotion === "sad") {
      return { sweater: "#9eb0c6" };
    }
    if (this.state.emotion === "thinking") {
      return { sweater: "#d7c5e7" };
    }
    return { sweater: "#f0aebb" };
  }

  roundRect(ctx, x, y, width, height, radius) {
    ctx.beginPath();
    ctx.moveTo(x + radius, y);
    ctx.lineTo(x + width - radius, y);
    ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
    ctx.lineTo(x + width, y + height - radius);
    ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
    ctx.lineTo(x + radius, y + height);
    ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
    ctx.lineTo(x, y + radius);
    ctx.quadraticCurveTo(x, y, x + radius, y);
    ctx.closePath();
  }
}
```

- [ ] **Step 3: Create the Live2D adapter boundary**

Create `showcase-demo/live2d-prototype/adapters/live2d-renderer.js` with this content:

```javascript
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
```

## Task 3: Add Controller And Bridge Wiring

**Files:**
- Create: `showcase-demo/live2d-prototype/avatar-controller.js`
- Create: `showcase-demo/live2d-prototype/live2d.js`

- [ ] **Step 1: Create the avatar controller**

Create `showcase-demo/live2d-prototype/avatar-controller.js` with this content:

```javascript
import { mapAvatarSequence, mapAvatarState, mapBridgeMessage } from "./state-mapper.js";

export class AvatarController {
  constructor(renderer, readoutElement) {
    this.renderer = renderer;
    this.readoutElement = readoutElement;
    this.currentState = {
      emotion: "neutral",
      mouth: 0,
      gaze: "cursor",
      motion: "idle",
      intensity: 0.25,
      source: "boot"
    };
  }

  start() {
    this.renderer.start();
    this.renderReadout();
  }

  applyStateName(state) {
    this.applyMappedState(mapAvatarState({ state }));
  }

  playSequence(name) {
    this.applyMappedState(mapAvatarSequence({ name }));
  }

  handleBridgeMessage(message) {
    this.applyMappedState(mapBridgeMessage(message));
  }

  setPointerFromEvent(event, element) {
    const rect = element.getBoundingClientRect();
    const x = ((event.clientX - rect.left) / rect.width - 0.5) * 2;
    const y = ((event.clientY - rect.top) / rect.height - 0.5) * 2;
    this.renderer.setPointer(x, y);
  }

  applyMappedState(nextState) {
    this.currentState = {
      ...this.currentState,
      ...nextState,
      updatedAt: new Date().toISOString()
    };
    this.renderer.applyState(this.currentState);
    this.renderReadout();
  }

  renderReadout() {
    this.readoutElement.textContent = JSON.stringify(this.currentState, null, 2);
  }
}
```

- [ ] **Step 2: Create page bootstrap and WebSocket bridge**

Create `showcase-demo/live2d-prototype/live2d.js` with this content:

```javascript
import { AvatarController } from "./avatar-controller.js";
import { PlaceholderRenderer } from "./adapters/placeholder-renderer.js";

const canvas = document.querySelector("#avatarCanvas");
const stage = document.querySelector("#avatarStage");
const readout = document.querySelector("#stateReadout");
const bridgeUrl = document.querySelector("#bridgeUrl");
const connectBridge = document.querySelector("#connectBridge");
const disconnectBridge = document.querySelector("#disconnectBridge");

const renderer = new PlaceholderRenderer(canvas);
const controller = new AvatarController(renderer, readout);
let socket = null;

controller.start();

document.querySelectorAll("[data-state]").forEach((button) => {
  button.addEventListener("click", () => controller.applyStateName(button.dataset.state));
});

document.querySelectorAll("[data-sequence]").forEach((button) => {
  button.addEventListener("click", () => controller.playSequence(button.dataset.sequence));
});

stage.addEventListener("pointermove", (event) => {
  controller.setPointerFromEvent(event, stage);
});

connectBridge.addEventListener("click", () => {
  if (socket) {
    socket.close();
  }
  socket = new WebSocket(bridgeUrl.value);
  socket.addEventListener("message", (event) => {
    controller.handleBridgeMessage(JSON.parse(event.data));
  });
  socket.addEventListener("close", () => {
    socket = null;
  });
});

disconnectBridge.addEventListener("click", () => {
  if (socket) {
    socket.close();
  }
});

window.live2dPrototype = {
  applyState: (state) => controller.applyStateName(state),
  playSequence: (name) => controller.playSequence(name),
  handleBridgeMessage: (message) => controller.handleBridgeMessage(message)
};
```

## Task 4: Add Model Production Documents

**Files:**
- Create: `showcase-demo/model-production/README.md`
- Create: `showcase-demo/model-production/CHARACTER_BRIEF.md`
- Create: `showcase-demo/model-production/LIVE2D_ASSET_SPEC.md`
- Create: `showcase-demo/model-production/MINIMAX_PROMPTS.md`
- Create: `showcase-demo/model-production/MODEL_PIPELINE.md`

- [ ] **Step 1: Create model production overview**

Create `showcase-demo/model-production/README.md` with this content:

```markdown
# Model Production

This directory defines how the project gets from "no model" to a custom driveable desktop girlfriend model.

MiniMax or another image model can help create concept art, expression sheets, outfits, and pose references. It does not replace Live2D rigging. The driveable artifact for the B-plan is a Live2D Cubism export: `.model3.json`, textures, expressions, motions, and physics.
```

- [ ] **Step 2: Create character brief**

Create `showcase-demo/model-production/CHARACTER_BRIEF.md` with this content:

```markdown
# Character Brief

## Product Role

A desktop AI companion who feels present, attentive, and emotionally responsive while staying lightweight enough for a desktop overlay.

## Visual Direction

- Young adult anime-inspired character.
- Warm, soft, modern desktop-room style.
- Pink sweater and light skirt are the initial outfit direction from the existing visual exploration.
- Friendly expression, large readable eyes, natural hair silhouette.
- Designed for close-up desktop presence, not only full-body poster viewing.

## Interaction Needs

- Idle breathing.
- Mouse gaze tracking.
- Natural blink.
- Speaking mouth movement.
- Happy, thinking, sad, comfort, shy expressions.
- Greet, listen, reply, comfort motions.
```

- [ ] **Step 3: Create Live2D asset spec**

Create `showcase-demo/model-production/LIVE2D_ASSET_SPEC.md` with this content:

```markdown
# Live2D Asset Specification

## Required Delivery

- Layered PSD suitable for Live2D Cubism.
- Exported Live2D model folder with `.model3.json`.
- Texture files referenced by the model.
- At least four expressions: neutral, happy, thinking, sad.
- At least four motions: idle, greet, reply, comfort.
- Physics file for hair and clothing movement when available.

## PSD Layer Requirements

- Back hair separated from face and body.
- Front hair separated into left, center, and right clumps when possible.
- Face base separated from eyes, brows, mouth, blush, and shadow.
- Eye whites, pupils, highlights, and eyelids separated.
- Mouth shapes separated for closed, small, medium, and wide open.
- Brows separated for neutral, happy, sad, and thinking poses.
- Neck, body, arms, sleeves, skirt, and accessories separated.

## Runtime Parameter Targets

- `ParamAngleX`
- `ParamAngleY`
- `ParamAngleZ`
- `ParamBodyAngleX`
- `ParamEyeLOpen`
- `ParamEyeROpen`
- `ParamEyeBallX`
- `ParamEyeBallY`
- `ParamMouthOpenY`
- `ParamMouthForm`
- `ParamBreath`
```

- [ ] **Step 4: Create MiniMax prompt sheet**

Create `showcase-demo/model-production/MINIMAX_PROMPTS.md` with this content:

```markdown
# MiniMax Prompt Sheet

## Character Concept

Create a high-quality anime-style young adult female desktop AI companion character, warm and expressive, long brown hair with soft bangs, pink oversized sweater, light pleated skirt, gentle eyes, modern cozy desktop-room mood, clean front-facing full-body design, consistent proportions, suitable for Live2D character design reference.

## Expression Sheet

Create a character expression sheet for the same anime-style desktop AI companion: neutral, happy, shy, thinking, sad, comforting, surprised, speaking. Keep face shape, hair, outfit, eye color, and proportions consistent across all expressions.

## Live2D Layer Planning Reference

Create a clean character design reference for Live2D modeling, front-facing, arms visible, hair silhouette clear, face unobstructed, simple lighting, no complex background, no cropped body, no extra characters.

## Negative Guidance

Avoid heavy background detail, extreme camera angle, inconsistent outfit, inconsistent face, hidden hands, cropped head, cropped feet, extra limbs, extra characters, text, watermark, logo, cinematic motion blur.
```

- [ ] **Step 5: Create model pipeline**

Create `showcase-demo/model-production/MODEL_PIPELINE.md` with this content:

```markdown
# Model Pipeline

## Phase 1: Concept

Generate multiple character concepts with MiniMax or another image model. Pick one visual direction and freeze the core identity: hair, face, outfit, palette, and emotional tone.

## Phase 2: Production Art

Create or commission a clean front-facing character illustration designed for Live2D. Convert the final illustration into a layered PSD that follows `LIVE2D_ASSET_SPEC.md`.

## Phase 3: Rigging

Import the PSD into Live2D Cubism Editor. Bind face angle, eye movement, blink, mouth open, mouth form, breathing, hair physics, and basic body movement.

## Phase 4: Export

Export the Live2D runtime package. The expected main entry is a `.model3.json` file with textures, expressions, motions, and physics in the same model directory.

## Phase 5: Runtime Integration

Place the exported model under `showcase-demo/live2d-prototype/assets/models/custom/`. Configure the Live2D renderer to load that `.model3.json`. Keep the existing `avatar.state`, `avatar.sequence`, and `dialogue.turn` protocol unchanged.
```

## Task 5: Verify Static Prototype

**Files:**
- Verify: `showcase-demo/live2d-prototype/live2d.js`
- Verify: `showcase-demo/live2d-prototype/state-mapper.js`

- [ ] **Step 1: Run JavaScript syntax checks**

Run:

```powershell
node --check .\showcase-demo\live2d-prototype\live2d.js
node --check .\showcase-demo\live2d-prototype\state-mapper.js
node --check .\showcase-demo\live2d-prototype\avatar-controller.js
node --check .\showcase-demo\live2d-prototype\adapters\placeholder-renderer.js
node --check .\showcase-demo\live2d-prototype\adapters\live2d-renderer.js
```

Expected: each command exits with code `0` and prints no syntax error.

- [ ] **Step 2: Serve the prototype**

Run:

```powershell
python -m http.server 8786 -d .\showcase-demo
```

Open:

```text
http://127.0.0.1:8786/live2d-prototype/
```

Expected: a dark prototype page appears with a model stage, placeholder character, state controls, sequence controls, and bridge controls.

- [ ] **Step 3: Verify bridge compatibility**

Run the existing backend:

```powershell
python .\showcase-demo\tools\avatar_state_machine.py --port 8879 --interactive
```

Click `连接` in the prototype page, then type:

```text
你好
```

Expected: the state readout changes to a `dialogue.turn` mapped state and the placeholder renderer changes expression/mouth behavior.

## Self-Review

- Spec coverage: The plan covers the Live2D prototype, model-production documents, protocol mapping, placeholder renderer, future Live2D adapter, and verification.
- Placeholder scan: The word placeholder is used only for the intentional non-final renderer name, not as an unspecified implementation gap.
- Type consistency: `AvatarController`, `PlaceholderRenderer`, `Live2DRenderer`, and state mapper function names match across tasks.
