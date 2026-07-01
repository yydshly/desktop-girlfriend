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

当前网页端已经完成第一阶段拆分：

- `live2d.js`：只负责识别模式、创建 runtime、按需挂载 debug panel。
- `runtime-app.js`：负责人物运行时、模型加载、profile、bridge 和 AvatarController。
- `debug-panel.js`：只负责浏览器 showcase 的按钮、状态读数和 Motion Probe。
- `bridge-client.js`：只负责 WebSocket 连接、断开、重连和消息转发。

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

当前项目已经从“状态直接驱动 motion”收敛到“Emotion 驱动的可替换 Live2D 角色运行系统”。

最终链路是：

```text
主窗口输入
  -> EventBus
  -> dialogue / state / tts events
  -> Live2DBridgeEventMapper
  -> Live2DBridgeServer ws://127.0.0.1:8879
  -> Live2D 页面 bridge client
  -> AvatarController
  -> Emotion State
  -> Behavior Planner
  -> Character Contract
  -> Model Adapter
  -> Live2DRenderer
  -> motion / expression / parameters
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

关键原则：

- AI 或主窗口只表达“情绪/语义行为”，不要直接指定某个模型的 motion_03。
- Character Contract 定义统一动作语义，例如 idle / greet / happy / sad / think / speak。
- profile.json 只负责把统一语义映射到具体模型的 motion / expression。
- Model Adapter 负责输出模型命令。
- Live2DRenderer 只负责执行模型命令，并写入 Cubism 参数。

当前已接通的 adapter 输出：

- motion：优先使用 `modelCommands.motion.group/index`。
- expression：优先使用 `modelCommands.expression.name`。
- parameters：优先使用 `modelCommands.parameters.mouth/intensity` 控制口型和活跃度。

浏览器 showcase 的状态栏会显示 `adapter:` 诊断信息，用来确认当前语义行为被翻译成了什么模型命令。

## 7. 如何判断效果是否正常

浏览器 showcase 正常时：

- 页面能看到完整 Live2D 人物模型。
- Renderer 显示 Live2D 相关状态。
- 点击“待机 / 思考 / 说话”等按钮，人物会有动作和微动。
- Motion Probe 点击 Idle 0、Idle 1、TapBody 0 等按钮时，模型动作会变化。
- 状态栏里能看到 `adapter:`，例如 `happy -> TapBody[0]`、`engaged -> smile`、`mouth 0.64`。
- 如果人物动作看起来不明显，先看 `adapter:` 是否变化；如果 adapter 变了但人物没变，问题在模型能力或 profile 映射。
- 点击“模型实验 / 运行固定情绪序列”，可以一次触发 `idle -> listening -> thinking -> speaking -> happy -> comfort -> idle`。
- 实验输出会列出每一步的 motion / expression / mouth / intensity，用来判断模型动态效果是否符合“小云”规格。
- 模型资产区会显示 candidate score。这个分数不是审美评分，而是模型包动态能力评分：actions、expressions、lip sync、eye blink、physics、idle motion 等是否满足小云规格。
- 如果 candidate score 低，优先看 `missing`；它会说明缺少 expression 映射、动作映射、physics 或口型参数。

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

### 点击状态按钮但人物变化很弱

先看 showcase 状态栏：

- 如果 `adapter:` 没变化，问题在 bridge / AvatarController / Emotion Layer。
- 如果 `adapter:` 变化了，但 active motion 没变，问题在 model profile 的 actions 映射。
- 如果 active motion 变化了，但视觉很弱，说明当前模型本身动作幅度小，或者不适合桌面伴侣验证。
- 如果 expression 是 `none`，说明模型没有表情文件，或 profile 的 expressions 映射为空。

Hiyori 目前是 baseline 技术验证模型，不是最终“小云”角色。它能验证运行链路，但人物表现不代表最终产品效果。

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

1. 建立 Model Gallery / 模型实验页
   - 固定 emotion timeline：idle -> happy -> think -> speak -> idle。
   - 同一套状态序列对比多个模型。
   - 显示 adapter 命令、active motion、expression、FPS、模型能力。

2. 完善 profile.json 作为角色契约
   - 每个模型都必须声明 actions / expressions / placement。
   - 后续增加参数别名和参数范围。
   - profile 只做映射，不写业务逻辑。

3. 筛选更适合桌面伴侣的 Live2D 模型
   - Hiyori 作为 baseline。
   - 增加一个表现更丰富的商业/示例模型做对照。
   - 重点看 idle 舒适度、微表情、长期观看疲劳、说话口型。
   - 模型目标规格见 `docs/XIAOYUN_CHARACTER_MODEL_SPEC.md`。

4. 优化桌面人物窗口体验
   - 拖动稳定。
   - 位置持久化。
   - 透明背景和点击穿透策略。
   - 主窗口只负责控制，人物窗口负责呈现。

5. 接入更真实的驱动
   - TTS 音量驱动 mouth。
   - 对话语义驱动 emotion intensity。
   - 主动陪伴事件驱动 idle / greet / comfort。

6. 准备自定义“小云”模型
   - 当前 Hiyori 只是技术验证样例。
   - 最终效果取决于一个符合“小云”设定、适合桌面长期陪伴的 Live2D 模型。
   - 自定义模型需要从 Character Contract 反推动作和表情需求。
