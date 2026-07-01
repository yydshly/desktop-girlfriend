# 桌面女友项目启动与架构说明

## 1. 当前最佳架构

推荐保留三层结构：

1. 主窗口
   - 负责聊天输入、对话记录、设置、模型选择、人物显示/隐藏、缩放、透明度等控制。
   - 这是用户日常使用的控制台。

2. Live2D 人物模拟窗口
   - 负责最终桌面人物呈现。
   - 由主窗口启动和控制。
   - 通过本地 WebSocket 接收主窗口发出的状态与对话事件。
   - 后续口型、动作、情绪、待机互动都应该主要落在这里。

3. 浏览器 Live2D showcase
   - 保留为开发和调试页面。
   - 用来检查模型是否加载成功、动作是否绑定正确、Motion Probe 是否合理、bridge 消息是否正常。
   - 它不是最终产品界面，但非常适合调模型和排查问题。

这套结构的好处是：

- 主窗口不直接承载复杂动画逻辑。
- 人物窗口可以逐步演化成真正的桌面伴侣。
- 浏览器页面可以继续作为调试台，不影响最终体验。
- 后续更换模型、增加 TTS 口型、接入记忆和主动互动时，不会把逻辑塞成一团。

## 2. 推荐使用方式

日常开发时建议同时看两类效果：

1. 浏览器 showcase：看模型、动作、调试信息。
2. 桌面主应用 + 人物窗口：看最终桌面伴侣体验。

如果只是调 Live2D 模型，优先打开浏览器 showcase。

如果要验证“用户输入 -> AI 回复 -> 人物动作/说话/情绪变化”，启动完整桌面应用。

## 3. 启动浏览器 showcase

在项目根目录执行：

```powershell
cd D:\claude_code\20260628_桌面女友\desktop-girlfriend\showcase-demo
python -m http.server 8786
```

然后打开：

```text
http://127.0.0.1:8786/live2d-prototype/
```

这个页面可以查看：

- Live2D 模型是否加载成功。
- 当前 renderer 状态。
- SDK 是否检测成功。
- 模型 motions / expressions 能力。
- 状态按钮：待机、开心、思考、低落、安慰、说话。
- Motion Probe：逐个试模型动作。
- Motion Binding：把动作绑定到状态。
- Bridge 状态：是否连接到主程序的 WebSocket。

如果页面里显示真实人物模型，而不是贴图 atlas，说明 Live2D runtime 加载成功。

## 4. 启动完整桌面应用

在项目根目录执行：

```powershell
cd D:\claude_code\20260628_桌面女友\desktop-girlfriend
.\scripts\run_desktop.ps1
```

它会启动主聊天窗口。

主窗口里的人物相关按钮包括：

- 人物+：放大人物窗口。
- 人物-：缩小人物窗口。
- 淡一点：降低人物窗口透明度。
- 实一点：提高人物窗口透明度。
- 人物：显示或隐藏人物窗口。
- 重置人物：重置人物窗口位置。
- 模型选择：切换可用 Live2D 模型。
- 刷新模型：重新扫描模型目录。
- 打开模型目录：打开 Live2D 模型放置位置。

默认情况下，`.env.example` 里 `LIVE2D_DESKTOP_AUTO_LAUNCH=true`，所以复制出的 `.env` 也会默认自动启动人物窗口。

## 5. 单独启动 Live2D 人物窗口

如果只想看桌面人物窗口，不启动主聊天窗口，可以执行：

```powershell
cd D:\claude_code\20260628_桌面女友\desktop-girlfriend
.venv\Scripts\python.exe -m app.live2d_desktop
```

可带参数：

```powershell
.venv\Scripts\python.exe -m app.live2d_desktop --scale 1.1 --opacity 0.9
```

注意：单独启动人物窗口时，如果主应用没有运行，本地 bridge 服务可能没有消息来源，所以人物可以显示，但不会跟随聊天状态变化。

## 6. 当前驱动链路

完整链路是：

```text
主窗口输入
  -> EventBus
  -> dialogue / state / tts events
  -> Live2DBridgeEventMapper
  -> Live2DBridgeServer ws://127.0.0.1:8879
  -> Live2D 页面 bridge client
  -> AvatarController
  -> Live2DRenderer
  -> 模型参数 / 表情 / motion
```

稳定状态协议是：

```text
idle
listening
thinking
speaking
happy
sad
comfort
error
```

网页端会把这些产品状态翻译成模型参数、表情和 motion。

## 7. 如何判断效果是否正常

浏览器 showcase 正常时：

- 页面能看到完整 Live2D 人物模型。
- Renderer 显示 Live2D 相关状态。
- 点击“待机 / 思考 / 说话”等按钮，人物会有动作和微动。
- Motion Probe 点击 Idle 0、Idle 1、TapBody 0 等按钮时，模型动作会变化。

桌面应用正常时：

- 主窗口可以打开。
- 人物窗口会自动出现，或者点击“人物”后出现。
- 点击“人物+ / 人物- / 淡一点 / 实一点”会重启人物窗口并改变大小或透明度。
- 输入消息后，人物状态会通过 bridge 被驱动。

## 8. 常见问题

### 浏览器页面只显示贴图 atlas

说明 Live2D SDK 或模型 runtime 没有真正接起来，页面走了 fallback preview。

优先检查：

- URL 是否是 `http://127.0.0.1:8786/live2d-prototype/`。
- 是否通过 http server 打开，而不是直接双击 html。
- 页面右侧 SDK 状态是否 ready。
- model path 是否指向 `.model3.json`。

### 桌面人物不跟随主窗口变化

优先检查：

- 主应用是否已启动。
- `ws://127.0.0.1:8879` bridge 是否可用。
- 浏览器 showcase 的 Bridge 状态是否连接成功。
- 主窗口发送消息时，showcase 的 bridge readout 是否有事件变化。

### 主窗口启动但没有人物窗口

检查 `.env`：

```text
LIVE2D_DESKTOP_AUTO_LAUNCH=true
```

也可以在主窗口点击“人物”按钮手动打开。

## 9. 后续推进方向

推荐后续按这个顺序继续：

1. 优化桌面人物窗口体验
   - 拖动稳定。
   - 位置持久化。
   - 更自然的透明背景。
   - 更像桌面伴侣，而不是调试窗口。

2. 强化人物动作表现
   - idle 微动。
   - thinking / listening 微动。
   - speaking 口型与 TTS 音量同步。
   - 情绪动作和表情 profile 化。

3. 建立模型 profile
   - 每个模型自己的 motionBindings。
   - 每个模型自己的 expression aliases。
   - 每个模型自己的参数范围。

4. 准备自定义模型
   - 现在的 Hiyori 是技术验证样例。
   - 最终需要一个符合“小云”设定的自定义 Live2D 模型。

5. 再考虑 Runtime / Debug 分离
   - 当前可以先保留一个网页调试入口。
   - 等人物体验更稳定后，再把最终 runtime 和 debug panel 拆干净。
