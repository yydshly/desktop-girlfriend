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

## 质量支撑体系

项目使用 **Skill / Superpowers** 作为开发辅助层，用于降低单人开发的审查成本。它们不能替代测试、CI 和人工架构判断；项目自定义 Skill 只有在真实创建并验证后，才视为正式质量机制。

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
