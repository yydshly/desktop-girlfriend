# Desktop Girlfriend Runtime Demo

这是桌面女友项目的独立呈现层原型。当前目标不是生成视频，也不是直接做 3D，而是先验证：

```text
AI 状态如何驱动角色表现
```

核心架构：

```text
Python AI / EventBus / StateMachine
  -> WebSocket Bridge
  -> Motion Planner
  -> Renderer Adapter
  -> PNG Puppet / Live2D / VRM
```

## 当前入口

```text
home.html          Demo 导航首页
puppet.html        当前主线：PNG Puppet Runtime
architecture.html  渲染架构路线：PNG -> Live2D -> VRM 3D
runtime.html       早期 Avatar Runtime 状态演示
index.html         早期 6 卡片 Showcase
```

推荐使用 HTTP 服务打开，避免浏览器限制 JSON 加载：

```powershell
cd D:\claude_code\20260628_桌面女友\desktop-girlfriend\showcase-demo
python -m http.server 8784 --bind 127.0.0.1
```

然后访问：

```text
http://127.0.0.1:8784/puppet.html
```

## 已完成

- `real-layers` PNG 分层加载
- 技术占位透明 PNG 图层
- 瞳孔移动
- 口型切换
- 眨眼
- 情绪粒子
- `avatar.state` 协议
- `motion-planner-v1.json`
- AI 事件序列：`greet / listen / reply / comfort`
- WebSocket Bridge
- Python mock 后端
- Python StateMachine 后端雏形
- `DialogueTurn` 数据结构：`user_text / intent / response_text / tts_state`
- 前端“当前对话轮次”面板：显示 `turn_id / intent / tts_state / user_text / response_text`

## 前端调试入口

直接发状态：

```js
window.dispatchPuppetAction({
  type: "avatar.state",
  version: 1,
  source: "console",
  emotion: "happy",
  action: "speak",
  mouth: "medium",
  gaze: "cursor",
  speaking: true,
  intensity: 0.7
});
```

播放 Motion Planner 序列：

```js
window.playAvatarSequence("reply");
```

连接本地后端桥接：

```js
window.connectAvatarBridge("ws://127.0.0.1:8766/avatar");
```

## 后端调试

固定脚本 mock：

```powershell
python .\tools\mock_avatar_ws.py --port 8766
```

状态机自动脚本：

```powershell
python .\tools\avatar_state_machine.py --port 8766
```

状态机交互模式：

```powershell
python .\tools\avatar_state_machine.py --port 8766 --interactive
```

如果端口被占用，可以换成任意空闲端口，例如：

```powershell
python .\tools\avatar_state_machine.py --port 8879 --interactive
```

交互模式下，在终端输入一句话，会触发：

```text
user_input_started -> avatar.sequence listen
model_thinking     -> avatar.state think
tts_started        -> avatar.sequence reply
tts_viseme         -> avatar.state speak + mouth
tts_finished       -> avatar.state idle
```

当前 `DialogueController` 是最小规则版：

```text
问候词       -> greet
低落/疲惫词  -> comfort
其他输入     -> reply
```

意图识别测试：

```powershell
python .\tools\test_dialogue_controller.py
```

## 关键文件

```text
assets/avatar/avatar-state-schema.json
assets/avatar/motion-planner-v1.json
assets/avatar/layers/manifest.json
tools/avatar_ws.py
tools/dialogue_controller.py
tools/dialogue_turn.py
tools/mock_avatar_ws.py
tools/avatar_state_machine.py
puppet.html
puppet.js
puppet.css
```

## 素材边界

当前 `assets/avatar/layers/*.png` 是技术占位素材，用来证明分层运行时可行。它们不是最终角色素材。

下一步真正进入角色制作时，需要替换成同一角色的透明分层 PNG：

```text
base-body.png
eye-left-white.png
eye-right-white.png
pupil-left.png
pupil-right.png
mouth-closed.png
mouth-small.png
mouth-medium.png
mouth-large.png
eyelid-left.png
eyelid-right.png
```

## 验证

```powershell
node --check .\puppet.js
python .\tools\check_assets.py
python .\tools\check_layers.py
python .\tools\test_dialogue_controller.py
python .\tools\test_dialogue_turn.py
python -m py_compile .\tools\avatar_ws.py .\tools\mock_avatar_ws.py .\tools\avatar_state_machine.py
```

## 后续路线

```text
V1  PNG Puppet
    验证 AI 状态、Motion Planner、WebSocket Bridge、口型和眼神。

V2  Real Character Layers
    替换成真实角色透明分层素材。

V3  Live2D
    用 Live2D 参数和 motion 替换 PNG Renderer。

V4  Desktop Shell
    用 Electron / Tauri 做透明窗口、置顶、拖拽、托盘。

V5  VRM / Three.js 3D
    需要空间动作、转身、坐下、桌面互动时，再接 3D 模型。
```
