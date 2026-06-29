# desktop-girlfriend

桌面 AI 伙伴原型项目 — 探索桌面人格表现、语音交互、手势交互、多模态感知、情绪陪伴和 MiniMax AI 能力集成。

> **它不是**：单纯聊天机器人、单纯桌宠、或第一阶段就要实现完整 3D AI 女友。
>
> **更准确的长期方向**：桌面人格壳 + Jarvis 式助手 + 情绪陪伴 + 多模态交互实验平台。

## Vision

> **北极星愿景图**是项目整体目标指导图，用于指导项目目标、产品定位、能力边界和路线图。

![Vision Board](./docs/assets/vision-board.png)

详见：[Vision Reference](./docs/VISION_REFERENCE.md)

## 当前状态

当前为 **V2 冻结 / V3 准备前** 阶段。

- V1 已完成 PySide6 最小桌面壳。
- V2 已完成 EventBus、StateMachine、StateController、ViewModel 和基础状态展示。
- V3 才会引入 MiniMax 文本对话、TTS 和 Prompt Registry。
- 在进入 V3 前，优先修复运行环境、事件契约、文档一致性和质量检查入口。

### 项目结构

```
app/
├── contracts/      # 事件、状态、payload 定义
├── core/           # EventBus、StateMachine、Config、Logging
├── ui/             # PySide6 窗口和 ViewModel
├── brain/          # LLM、Prompt、Provider（后续阶段）
├── expression/     # TTS、Avatar（后续阶段）
├── perception/     # ASR、手势（后续阶段）
├── memory/         # 记忆（后续阶段）
├── tools/          # Tool Router（后续阶段）
└── tests/         # 单元测试
```

### 环境要求

- **Python 3.11+**（项目 `pyproject.toml` 固定 `requires-python = ">=3.11"`）

### 安装

Windows 推荐使用 Python 3.11+ 创建虚拟环境。若本机有 `py` launcher：

```bash
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install -e ".[dev]"
```

若没有 `py` launcher，请使用已安装的 Python 3.11+ 解释器创建虚拟环境，并确认 `python --version` 满足 `>=3.11`。

### 运行

```bash
python -m app.main
```

### 测试

```bash
python -m ruff check .
python -m mypy app
python -m pytest -q
```

## 技术架构

详见：[架构规范](./docs/ARCHITECTURE.md)

| 模块 | 描述 |
|------|------|
| UI 层 | 桌面窗口、角色展示、用户界面 |
| Core 层 | EventBus、StateMachine、Config、应用生命周期 |
| Brain 层 | LLM、Prompt、MiniMax Provider、Agent 决策 |
| Expression 层 | TTS、语音播放、Avatar 表现、动作状态 |
| Perception 层 | ASR、麦克风、摄像头、手势识别 |
| Memory 层 | 短期上下文、长期记忆、会话历史 |
| Tool 层 | Tool Router、工具调用、权限控制、审计日志 |

## 核心原则

- **EventBus 驱动** — 跨层业务事件通过 EventBus
- **StateMachine 驱动** — 状态变更通过 StateMachine
- **Provider 化** — 外部服务封装为 Provider
- **Prompt Registry** — Prompt 集中管理

## 开发辅助体系

项目使用 **Superpowers** 作为主要开发辅助流程，用于需求澄清、计划拆解、TDD、调试和代码审查。它不能替代测试、CI 和人工架构判断；项目自定义 Skill 暂缓，等真实流程稳定后再沉淀。

### 开发流程

- **Solo Developer Flow** — 单人开发流程，MiniMax 执行，ChatGPT 审查
- **Module Development Gate** — 新模块开发前必须通过的准入审查
- **Checkpoint Review** — 阶段完成后的轻量审查

详见：

- [MiniMax 执行规范](./docs/MINIMAX_EXECUTION.md) — Solo Developer Flow 和 Module Development Gate
- [代码审查指南](./docs/REVIEW_GUIDE.md) — Checkpoint Review 和 Gate Checklist
- [Skill 体系](./docs/SKILLS.md) — 开发辅助体系

## 文档导航

### 愿景与定位
- [愿景图参考](./docs/VISION_REFERENCE.md) — 北极星愿景图
- [项目简介](./docs/PROJECT_BRIEF.md) — 项目概述和定位

### 开发规范
- [架构规范](./docs/ARCHITECTURE.md) — 分层架构和核心原则
- [代码审查指南](./docs/REVIEW_GUIDE.md) — Checkpoint Review 原则
- [MiniMax 执行规范](./docs/MINIMAX_EXECUTION.md) — Agent 执行边界
- [Skill 体系](./docs/SKILLS.md) — 开发辅助体系

### 项目管理
- [路线图](./docs/ROADMAP.md) — V0-V8 版本规划和里程碑

## 版本路线图

| 版本 | 阶段 |
|------|------|
| V0 | 文档治理与项目规则 |
| V1 | 工程初始化与 PySide6 最小桌面壳 |
| V2 | 状态机、事件总线与桌面角色状态 |
| V3 | MiniMax 文本对话与 TTS |
| V4 | 语音输入 ASR |
| V5 | MediaPipe 手势事件 |
| V6 | Avatar / 数字人表现增强 |
| V7 | Agent 工具能力 |
| V8 | 记忆与人格系统 |

## 功能概览

当前已集成的功能模块：

| 能力 | 描述 | 状态 |
|------|------|------|
| 文本对话 | MiniMax LLM 对话 | 可用 |
| TTS 语音合成 | MiniMax TTS，播报回复 | 可配置启用 |
| ASR 语音输入 | 语音识别转文字 | 可配置启用 |
| 人格 | 小云人格，可自定义姓名 | 可用 |
| 记忆上下文 | 把确认记忆注入 LLM 会话 | 可配置启用 |
| 记忆建议 | 检测输入中值得记忆的内容 | 可配置启用 |
| 记忆管理 | 查看/删除已确认记忆 | 可配置启用 |
| 主动陪伴 | 空闲时主动发消息 | 可配置启用 |
| 主动陪伴 TTS | 主动消息走 TTS 播报 | 可配置启用 |
| Avatar 状态反馈 | 头像显示当前状态 | 可用 |
| 状态面板 | 查看能力开关状态 | 可用 |

> **默认关闭**：记忆（上下文/建议/管理）和主动陪伴（及 TTS）默认均为 `false`，需手动在 `.env` 中启用。

## Windows 本地启动

```powershell
# 1. 克隆仓库
git clone <repo-url>
cd desktop-girlfriend

# 2. 创建虚拟环境
python -m venv .venv
.venv\Scripts\python.exe -m pip install -U pip
.venv\Scripts\python.exe -m pip install -r requirements.txt

# 3. 配置环境变量
Copy-Item .env.example .env
# 用编辑器填写 .env 中的 API Key（可选，fake 模式无需填写）

# 4. 启动应用
.venv\Scripts\python.exe -m app.main
```

> **注意**：Windows 下推荐使用 PowerShell 或 Windows Terminal，CMD 可能存在编码问题。

## 配置说明

### 功能开关（`.env`）

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `MEMORY_CONTEXT_ENABLED` | `false` | 是否把已确认记忆注入 LLM 会话上下文 |
| `MEMORY_SUGGESTIONS_ENABLED` | `false` | 是否在用户输入后检测候选记忆 |
| `MEMORY_MANAGEMENT_ENABLED` | `false` | 是否显示记忆管理面板（查看/删除） |
| `PROACTIVE_ENABLED` | `false` | 是否启用主动陪伴（空闲时主动发消息） |
| `PROACTIVE_TTS_ENABLED` | `false` | 主动陪伴是否走 TTS 语音播报 |
| `PROACTIVE_QUIET_HOURS_ENABLED` | `false` | 是否启用勿扰时间（夜间不打扰） |

### 记忆安全说明

- 记忆必须由**用户主动确认**才会保存
- 不会保存原始完整对话
- 不会保存 evidence 文件
- 记忆内容为简短摘要，不会保存长文本

### 勿打扰与暂停

- `PROACTIVE_QUIET_HOURS_ENABLED=true` 时，23:00–08:00 不发送主动消息
- 用户说"别打扰"后，主动陪伴会暂停 `PROACTIVE_FEEDBACK_PAUSE_SECONDS` 秒

## UI 使用说明

### 状态面板（V11-A）

点击标题栏右侧 **「状态」** 按钮，可查看当前能力开关状态（只读）。

面板显示：
- 对话是否启用
- 记忆上下文/建议/管理是否开启
- 主动陪伴及 TTS 是否开启
- 勿扰时间是否开启
- 当前 Avatar 状态（☁️ 👂 💭 🗣️ ✨ ⚠️）

### 记忆面板（V8-J）

点击底部 **「记忆」** 按钮，可查看已保存的记忆（需 `MEMORY_MANAGEMENT_ENABLED=true`）。

### Avatar 状态

| Emoji | 状态 | 说明 |
|-------|------|------|
| ☁️ | idle | 待机 |
| 👂 | listening | 正在听 |
| 💭 | thinking | 正在想 |
| 🗣️ | speaking | 正在说话 |
| ✨ | proactive | 主动陪伴中 |
| ⚠️ | error | 出错 |

## 开发验证

```powershell
# 代码检查
.venv\Scripts\python.exe -m ruff check .

# 类型检查
.venv\Scripts\python.exe -m mypy app

# 单元测试
.venv\Scripts\python.exe -m pytest -q

# 启动就绪检查
.venv\Scripts\python.exe scripts\probe_launch_readiness.py
```

## Release Candidate

Current RC version: `0.1.0-rc.1`

Windows 快速启动：

```powershell
.\scripts\run_desktop.ps1
```

更多说明见：

```text
RELEASE_CANDIDATE.md
```

## 不要提交的内容

以下文件/目录**永远不要**提交到版本控制：

```
.env              # 包含真实 API Key
.tmp/             # 运行时生成的临时文件
__pycache__/      # Python 缓存
*.pyc
.venv/            # 虚拟环境
```
