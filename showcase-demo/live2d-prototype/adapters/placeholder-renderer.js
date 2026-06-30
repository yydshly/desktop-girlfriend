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

    ctx.fillStyle = "#f2c7be";
    ctx.beginPath();
    ctx.ellipse(0, -8, 38, 96, 0, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = "#765047";
    ctx.beginPath();
    ctx.ellipse(-110, -36, 58, 250, -0.18, 0, Math.PI * 2);
    ctx.ellipse(112, -34, 58, 250, 0.18, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = "#6b3f34";
    ctx.beginPath();
    ctx.ellipse(0, -162, 152, 138, 0, Math.PI * 1.02, Math.PI * 2.02);
    ctx.fill();

    this.drawEye(ctx, -48, -124);
    this.drawEye(ctx, 48, -124);
    this.drawBrows(ctx);
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
    ctx.fillStyle = "rgba(255, 255, 255, 0.78)";
    ctx.beginPath();
    ctx.ellipse(x + lookX + 4, y + lookY - 4, 3, 4, 0, 0, Math.PI * 2);
    ctx.fill();
  }

  drawBrows(ctx) {
    ctx.strokeStyle = "#59332f";
    ctx.lineWidth = 5;
    ctx.lineCap = "round";
    const sad = this.state.emotion === "sad";
    const thinking = this.state.emotion === "thinking";
    ctx.beginPath();
    ctx.moveTo(-76, sad ? -160 : -154);
    ctx.lineTo(-24, thinking ? -164 : -152);
    ctx.moveTo(24, thinking ? -164 : -152);
    ctx.lineTo(76, sad ? -160 : -154);
    ctx.stroke();
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
