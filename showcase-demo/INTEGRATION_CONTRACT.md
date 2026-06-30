# Avatar Runtime Integration Contract

这份契约定义 AI 后端、Motion Planner 和前端渲染层之间的边界。

## Runtime Pipeline

```text
Python AI / EventBus / StateMachine
  -> WebSocket Bridge
  -> Motion Planner
  -> Avatar Renderer
  -> PNG Puppet / Live2D / VRM
```

当前 demo 已经实现：

```text
avatar.state
avatar.sequence
window.dispatchPuppetAction(event)
window.playAvatarSequence(name)
window.connectAvatarBridge(url)
```

## WebSocket Bridge

默认地址：

```text
ws://127.0.0.1:8765/avatar
```

前端点击 `连接本地桥接` 后，会监听 WebSocket 消息。

## Message: avatar.state

用于直接驱动角色状态。

```json
{
  "type": "avatar.state",
  "version": 1,
  "source": "python-state-machine",
  "emotion": "happy",
  "action": "speak",
  "mouth": "medium",
  "gaze": "cursor",
  "speaking": true,
  "intensity": 0.72
}
```

字段枚举见：

```text
assets/avatar/avatar-state-schema.json
```

## Message: avatar.sequence

用于让前端 Motion Planner 播放一段状态时间线。

```json
{
  "type": "avatar.sequence",
  "name": "reply",
  "source": "python-state-machine"
}
```

当前序列配置在：

```text
assets/avatar/motion-planner-v1.json
```

已有序列：

```text
greet
listen
reply
comfort
```

## Message: dialogue.turn

这是后端调试/观测消息，用于描述一轮对话的数据模型。当前前端会忽略它，后续可以用于 UI 调试面板或日志。

```json
{
  "type": "dialogue.turn",
  "turn": {
    "turn_id": "unique-id",
    "created_at": "2026-06-30T00:00:00+00:00",
    "user_text": "hello",
    "intent": "greet",
    "response_text": "Hi, I am here.",
    "tts_state": "pending"
  }
}
```

当前 `puppet.html` 已经会显示最近一条 `dialogue.turn`：

```text
turn_id
intent
tts_state
user_text
response_text
```

## Browser Console Debug

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

```js
window.playAvatarSequence("reply");
```

```js
window.connectAvatarBridge("ws://127.0.0.1:8765/avatar");
```

## Mock Backend

运行无依赖 Python mock 服务。它只播放固定脚本，用于测试 WebSocket 通路：

```powershell
python .\tools\mock_avatar_ws.py
```

如果 `8765` 被占用，可以换端口：

```powershell
python .\tools\mock_avatar_ws.py --port 8766
```

然后在 `puppet.html` 点击：

```text
连接本地桥接
```

如果使用非默认端口，可以在浏览器控制台调用：

```js
window.connectAvatarBridge("ws://127.0.0.1:8766/avatar");
```

mock 服务会依次发送：

```text
avatar.sequence: greet
avatar.sequence: reply
avatar.state: idle
```

## State Machine Backend

运行无依赖 Python 状态机示例。它模拟真实对话生命周期：

```powershell
python .\tools\avatar_state_machine.py --port 8766
```

也可以启用交互模式：

```powershell
python .\tools\avatar_state_machine.py --port 8766 --interactive
```

此时你在终端输入一句话，它会触发一轮 `listen -> think -> speak -> idle`。

如果端口被占用，换一个空闲端口，并在前端使用同一个端口连接即可。

当前 `DialogueController` 是规则版意图识别：

```text
hello / 你好 / 早安  -> avatar.sequence greet
sad / 难过 / 累       -> avatar.sequence comfort
其他输入             -> reply cycle
```

它位于：

```text
tools/dialogue_controller.py
```

测试：

```powershell
python .\tools\test_dialogue_controller.py
```

然后在浏览器控制台连接：

```js
window.connectAvatarBridge("ws://127.0.0.1:8766/avatar");
```

它会依次模拟：

```text
user_input_started -> avatar.sequence listen
model_thinking     -> avatar.state think
tts_started        -> avatar.sequence reply
tts_viseme         -> avatar.state speak + mouth
tts_finished       -> avatar.state idle
```

## Next Integration Step

真实项目里，Python 后端可以把对话状态映射成两类消息：

```text
用户开始说话       -> avatar.sequence listen
模型正在思考       -> avatar.sequence reply 的 think 阶段
TTS 开始播放       -> avatar.state speaking=true
TTS 音量/音素变化  -> avatar.state mouth/tts
回复结束           -> avatar.state idle
```
