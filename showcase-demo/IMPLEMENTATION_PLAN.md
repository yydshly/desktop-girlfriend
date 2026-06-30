# 实现路线：从 Showcase 到桌面女友呈现层

这份文档把当前展示页拆成可执行的技术路线。核心原则是：先做可见效果，再替换真实角色资产，最后接入 AI 状态机。

## 1. 当前目录的定位

`showcase-demo` 不是最终产品，而是视觉与交互验证层。

它要回答的问题是：

- 桌面女友在桌面场景中应该如何出现？
- 走路、手势、眼神、情绪、唱歌、待机这些能力的 UI 如何组织？
- 哪些效果值得后续投入真实素材和引擎？

## 2. 推荐技术方案

### 方案 A：静态 Showcase

当前已经采用。

- 适合：快速验证设计、给自己看效果、拆模块
- 技术：HTML + CSS + Canvas + JavaScript
- 优点：零依赖、打开就能看、迭代快
- 缺点：不适合长期维护复杂状态

### 方案 B：React Showcase

下一步建议迁移。

- 适合：组件化管理 6 个 demo 卡片
- 技术：React + Vite + Framer Motion 或 GSAP
- 优点：状态、动画、素材切换更清晰
- 缺点：需要构建环境

建议组件结构：

```text
src/
  App.tsx
  components/
    DemoCard.tsx
    AvatarStage.tsx
  demos/
    WalkDemo.tsx
    GestureDemo.tsx
    GazeDemo.tsx
    EmotionVfxDemo.tsx
    SingDemo.tsx
    IdleDemo.tsx
  assets/
    character/
    background/
    motions/
```

### 方案 C：Tauri 桌面壳

适合做真正桌面呈现。

- 适合：轻量桌面应用、透明窗口、置顶、托盘
- 技术：Tauri + React
- 关键能力：
  - transparent window
  - always on top
  - frameless window
  - click-through 可选
  - 与 Python 后端通过本地 HTTP/WebSocket/命令桥通信

### 方案 D：Electron 桌面壳

适合追求生态成熟和调试方便。

- 优点：Web 能力完整、资料多、插件多
- 缺点：体积和内存占用更高

## 3. 六个模块的最小可行实现

### 走路效果

第一版：

- 用 `walking.webm` 或序列帧循环
- 外层做左右平移
- 加轻微上下 bob

进阶版：

- Live2D/Spine locomotion 动作
- 根据鼠标目标点或屏幕边界规划移动

### 手势动作

第一版：

- 每个按钮切换一个短视频或序列帧
- 动作包括 wave、heart、point、think

进阶版：

- 动作状态机
- 动作可被 AI 回复、情绪、用户输入触发

### 眼神追踪

第一版：

- 头部轻微旋转
- 眼睛独立小幅偏移

进阶版：

- 角色分层素材：head、eyeL、eyeR、pupil、blink
- 鼠标位置、当前活跃窗口、语音来源共同决定视线目标

### 情绪粒子

第一版：

- Canvas 粒子 overlay
- emotion preset 控制颜色、速度、密度

进阶版：

- 情绪状态来自 persona/state machine
- 粒子强度和 TTS 音色、表情同步

### 唱歌效果

第一版：

- 唱歌 loop + 音符 + 波形
- 简单口型开合

进阶版：

- Web Audio API 分析音量
- 3 到 5 个嘴型状态
- TTS 或音乐播放驱动 lip-sync

### 待机互动

第一版：

- 多个 idle 动作小片段
- 定时轮播

进阶版：

- 根据时间、用户活跃度、对话状态选择 idle
- 接入主项目 EventBus 和 StateMachine

## 4. 素材清单

优先准备这些文件，能最快把占位动画替换成真实效果：

```text
assets/
  background/room-night.png
  motions/walking.webm
  motions/wave.webm
  motions/heart.webm
  motions/point.webm
  motions/think.webm
  motions/sing.webm
  motions/idle-wave.webm
  motions/idle-stretch.webm
  motions/idle-read.webm
  motions/idle-drink.webm
```

如果要走可控角色路线，则需要：

```text
character/
  body.png
  head.png
  hair-front.png
  hair-back.png
  eye-left.png
  eye-right.png
  pupil-left.png
  pupil-right.png
  mouth-closed.png
  mouth-open-small.png
  mouth-open-medium.png
  mouth-open-large.png
```

## 5. 与当前 Python 项目的连接方式

当前主项目是 PySide6/Python。后续有两条连接路线：

### 路线 1：PySide6 内嵌 WebView

- 用 Qt WebEngine 显示 React/Tauri-like 页面
- Python 直接驱动 UI 状态
- 适合保持单一 Python 应用

### 路线 2：独立 Tauri/Electron 前端 + Python 后端

- 前端负责桌面呈现和动画
- Python 负责 AI、TTS、记忆、状态机
- 通信用本地 WebSocket 或 HTTP

建议先选路线 2，因为前后端边界更清楚，动画能力也更强。

## 6. 下一步任务

推荐顺序：

1. 把静态 showcase 迁移成 React/Vite。
2. 把每个 demo 抽成独立组件。
3. 增加 `assets` 目录和素材加载约定。
4. 先替换走路、手势、唱歌三个模块为 WebM。
5. 再做眼神追踪的分层角色素材。
6. 最后接主项目状态机，让 AI 能触发动作和情绪。
