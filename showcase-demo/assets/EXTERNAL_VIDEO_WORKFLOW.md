# 外部视频生成工作流

这份说明用于把 MiniMax/Hailuo/其他视频生成工具产出的动作视频接入 showcase。

## 最推荐的顺序

不要一口气生成 10 个动作。先验证角色一致性。

第一批只做 3 个：

```text
wave.webm
sing.webm
walking.webm
```

这三个能覆盖手势、口型/表演、全身运动三种最关键风险。

## 步骤

### 1. 使用角色参考图

上传：

```text
assets/reference/character-reference.png
```

把它作为 image-to-video 的输入，不要让模型重新设计角色。

### 2. 使用动作提示词

提示词在：

```text
assets/prompts/motion-prompts.md
```

每次只生成一个动作。

### 3. 导出视频

建议导出：

```text
duration: 4-6s
resolution: 720p or 1080p
audio: off
camera: static
watermark: off if available
```

### 4. 放入项目

如果导出的是 `webm` 且尺寸合适，可以直接覆盖：

```text
assets/motions/wave.webm
```

如果导出的是 `mp4` 或 `mov`，运行：

```powershell
python .\tools\normalize_motion.py wave C:\Downloads\wave.mp4 --replace
```

### 5. 检查素材

```powershell
python .\tools\check_assets.py
```

### 6. 打开页面验证

```text
index.html
```

重点看：

- 是否循环顺畅
- 是否有水印
- 角色脸是否变了
- 手部有没有明显畸形
- 卡片里的文字是否遮挡主体

## 什么时候停止视频路线

如果出现下面任意两项，建议暂停继续生成视频，转 Live2D/Spine：

- 每个动作角色长得不一样
- 手部经常畸形
- 眼神追踪无法真实互动
- 唱歌口型不可控
- 想做透明桌面常驻角色

## 什么时候继续视频路线

如果你当前目标只是 showcase 展示页：

- 视频路线最快
- 成本最低
- 最容易看出效果
- 可以快速验证视觉风格

## 推荐决策

第一版产品展示：视频路线。

长期桌面陪伴：Live2D/Spine。

真实 3D 空间互动：VRM/Three.js。
