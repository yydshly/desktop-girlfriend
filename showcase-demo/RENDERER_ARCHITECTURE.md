# 桌面女友渲染架构

## 结论

最终可以做 3D，但当前主线应该先做“角色运行时”，而不是直接做视频或 3D。

可靠架构是：

```text
AI State
  -> Motion Planner
  -> Renderer Adapter
  -> Desktop Shell
  -> User Interaction Feedback
```

其中 `Renderer Adapter` 可以逐步替换：

```text
PngPuppetRenderer
  -> Live2DRenderer
  -> Vrm3DRenderer
```

## 为什么不继续走视频

视频适合展示，不适合真实桌面女友。

原因：

- 视频不能实时看鼠标。
- 视频不能跟随 TTS 音量自然改口型。
- 视频不能根据对话状态随时切换表情。
- 视频不能稳定处理点击、拖拽、靠边、缩放和待机。
- 视频素材越多，一致性越难维护。

所以视频只能作为早期展示或特殊动作素材，不能作为长期运行时核心。

## 为什么先做 PNG Puppet

PNG Puppet 的目标不是最终质感，而是验证控制闭环：

```text
AI 说她开心
  -> emotion=happy
  -> 角色眼神更亮、嘴角打开、暖色粒子出现

AI 正在说话
  -> speaking=true
  -> mouth 在 small/medium/large 间变化

用户移动鼠标
  -> gaze=cursor
  -> 眼睛和头部跟随
```

这一步能证明“人物素材被状态控制”是否成立。

## Live2D 的位置

Live2D 是最适合桌面女友的中期方案。它仍然是 2D，但能提供：

- 头部转动
- 眼神追踪
- 眨眼
- 呼吸
- 发丝摆动
- 表情参数
- 口型同步
- 待机 motion

如果用户目标是“好看、轻量、长期陪伴”，Live2D 通常比 3D 更划算。

## 3D 的位置

3D 是最终增强方案，不是当前阻塞项。

适合引入 3D 的情况：

- 需要转身、走动、坐下、探头等空间动作。
- 需要真实光照和摄像机角度。
- 需要和桌面边缘、窗口、图标产生空间互动。
- 已经有稳定角色设定和状态协议。

推荐技术栈：

```text
VRM model
Three.js
@pixiv/three-vrm
Electron or Tauri transparent desktop window
```

## 渲染器接口

所有渲染器都应该实现同一组能力：

```ts
interface AvatarRenderer {
  id: string;
  load(assetConfig: unknown): Promise<void>;
  applyState(state: AvatarState): void;
  setGaze(x: number, y: number): void;
  setMouth(shape: "closed" | "small" | "medium" | "large" | "auto"): void;
  destroy(): void;
}
```

当前 `puppet.js` 已经先把 DOM 控制收拢成 `PngPuppetRenderer`，后续替换 Live2D / VRM 时，不应该改 AI 状态层，只替换渲染器。

## 下一步工作

1. 产出透明 PNG 分层素材。
2. 让 `puppet.html` 从 `assets/avatar/layers/` 加载真实图层。
3. 把口型切换接到 TTS 音量或音素。
4. 用 Electron / Tauri 包成透明桌面窗口。
5. 状态协议稳定后，再升级 Live2D。
6. 需要空间互动时，再接 VRM 3D。
