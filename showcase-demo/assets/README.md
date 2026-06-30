# Showcase Assets

把真实动作素材放在这里，页面会自动优先使用素材；如果文件不存在，会回退到 CSS/Canvas 占位动画。

## 推荐目录

```text
assets/
  reference/
    character-reference.png
  background/
    background-room-night.png
  motions/
    walking.webm
    wave.webm
    heart.webm
    point.webm
    think.webm
    sing.webm
    idle-wave.webm
    idle-stretch.webm
    idle-read.webm
    idle-drink.webm
```

第一版素材生产方案见 [ASSET_PRODUCTION_PLAN.md](./ASSET_PRODUCTION_PLAN.md)。
外部视频生成流程见 [EXTERNAL_VIDEO_WORKFLOW.md](./EXTERNAL_VIDEO_WORKFLOW.md)。
生成提示词见 [prompts/](./prompts/)。
当前素材来源见 [ASSET_ORIGIN.md](./ASSET_ORIGIN.md)。

## 素材建议

- 格式优先用 `webm`，体积小，适合循环动作。
- 如果要做透明角色层，优先导出带 alpha 的 WebM。
- 每个动作建议做成 2 到 6 秒的 loop。
- 分辨率建议先用 720p 或 1080p，不要一开始追求 4K。
- 背景和角色最好分离，方便以后做透明桌面层。

## 命名约定

页面当前使用的动作 key：

```text
walking
wave
heart
point
think
sing
idleWave
idleStretch
idleRead
idleDrink
```

如果要改文件名，对应修改 [app.js](../app.js) 里的 `motionLibrary`。
